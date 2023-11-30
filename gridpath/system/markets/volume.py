# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import os.path
from pyomo.environ import Expression, Param, Constraint

from gridpath.auxiliary.db_interface import directories_to_db_values

Infinity = float("inf")


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """ """
    m.max_market_sales = Param(m.MARKETS, m.TMPS, default=Infinity)
    m.max_market_purchases = Param(m.MARKETS, m.TMPS, default=Infinity)
    m.max_final_market_sales = Param(m.MARKETS, m.TMPS, default=Infinity)
    m.max_final_market_purchases = Param(m.MARKETS, m.TMPS, default=Infinity)

    # Constrain total net purchases in the current stage
    def total_net_market_purchases_init(mod, market, tmp):
        return sum(
            mod.Net_Market_Purchased_Power[lz, mrkt, tmp]
            for (lz, mrkt) in mod.LZ_MARKETS
            if mrkt == market
        )

    m.Total_Net_Market_Purchased_Power = Expression(
        m.MARKETS, m.TMPS, initialize=total_net_market_purchases_init
    )

    def max_market_sales_rule(mod, hub, tmp):
        return (
            mod.Total_Net_Market_Purchased_Power[hub, tmp]
            >= -mod.max_market_sales[hub, tmp]
        )

    m.Max_Market_Sales_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_market_sales_rule
    )

    def max_market_purchases_rule(mod, hub, tmp):
        return (
            mod.Total_Net_Market_Purchased_Power[hub, tmp]
            <= mod.max_market_purchases[hub, tmp]
        )

    m.Max_Market_Purchases_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_market_purchases_rule
    )

    # Constrain total final net purchases in the current stage (given previous stage
    # positions)
    def total_final_net_market_purchases_init(mod, market, tmp):
        return sum(
            mod.Final_Net_Market_Purchased_Power[lz, mrkt, tmp]
            for (lz, mrkt) in mod.LZ_MARKETS
            if mrkt == market
        )

    m.Total_Final_Net_Market_Purchased_Power = Expression(
        m.MARKETS, m.TMPS, rule=total_final_net_market_purchases_init
    )

    def max_final_market_sales_rule(mod, hub, tmp):
        return (
            mod.Total_Final_Net_Market_Purchased_Power[hub, tmp]
            >= -mod.max_final_market_sales[hub, tmp]
        )

    m.Max_Final_Market_Sales_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_final_market_sales_rule
    )

    def max_final_market_purchases_rule(mod, hub, tmp):
        return (
            mod.Total_Final_Net_Market_Purchased_Power[hub, tmp]
            <= mod.max_final_market_purchases[hub, tmp]
        )

    m.Max_Final_Market_Purchases_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_final_market_purchases_rule
    )


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "market_volume.tab",
        ),
        param=(
            m.max_market_sales,
            m.max_market_purchases,
            m.max_final_market_sales,
            m.max_final_market_purchases,
        ),
    )


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()

    # Get load zones and their markets; only include load zones that are
    # in the load_zone_scenario_id and markets that are in the
    # market_scenario_id
    market_limits = c.execute(
        """
        SELECT market, timepoint, max_market_sales, max_market_purchases,
        max_final_market_sales, max_final_market_purchases
        -- Get prices for included markets only
        FROM (
            SELECT market
            FROM inputs_geography_markets
            WHERE market_scenario_id = ?
        ) as market_tbl
        -- Get prices for included timepoints only
        CROSS JOIN (
            SELECT stage_id, timepoint from inputs_temporal
            WHERE temporal_scenario_id = ?
            AND subproblem_id = ?
            AND stage_id = ?
        ) as tmp_tbl
        LEFT OUTER JOIN (
            SELECT market, stage_id, timepoint, max_market_sales, max_market_purchases,
            max_final_market_sales, max_final_market_purchases
            FROM inputs_market_volume
            WHERE market_volume_scenario_id = ?
        ) as price_tbl
        USING (market, stage_id, timepoint)
        ;
        """,
        (
            subscenarios.MARKET_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.MARKET_VOLUME_SCENARIO_ID,
        ),
    )

    return market_limits


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    market_prices.tab file.
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    market_limits = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "market_volume.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerow(
            [
                "market",
                "timepoint",
                "max_market_sales",
                "max_market_purchases",
                "max_final_market_sales",
                "max_final_market_purchases",
            ]
        )
        for row in market_limits:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
