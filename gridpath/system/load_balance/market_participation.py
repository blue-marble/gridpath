# Copyright 2016-2022 Blue Marble Analytics LLC.
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
import pandas as pd
from pyomo.environ import (
    Set,
    Param,
    Var,
    Expression,
    PositiveIntegers,
    NonNegativeReals,
    Boolean,
    value,
)

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import check_for_integer_subdirectories
from gridpath.auxiliary.dynamic_components import (
    load_balance_production_components,
    load_balance_consumption_components,
)
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """ """

    m.LZ_MARKETS = Set(dimen=2, within=m.LOAD_ZONES * m.MARKETS)

    m.MARKET_LZS = Set(
        within=m.LOAD_ZONES,
        initialize=lambda mod: list(set([lz for (lz, hub) in mod.LZ_MARKETS])),
    )

    m.MARKETS_BY_LZ = Set(
        m.MARKET_LZS,
        within=m.MARKETS,
        initialize=lambda mod, lz: [
            hub for (zone, hub) in mod.LZ_MARKETS if zone == lz
        ],
    )

    m.final_participation_stage = Param(
        m.LZ_MARKETS, within=PositiveIntegers, default=1
    )

    # Determine whether there is market participation in this stage
    # If no stages, we're using empty string as the stage, so convert that back to 1
    # If there are stages, convert the string to an integer for the comparison
    m.first_stage_flag = Param(within=Boolean)

    m.no_market_participation_in_stage = Param(
        m.LZ_MARKETS,
        rule=lambda mod, lz, hub: True
        if mod.final_participation_stage[lz, hub] < (1 if stage == "" else int(stage))
        else False,
    )

    m.LZ_MARKETS_PREV_STAGE_TMPS = Set(dimen=3)

    m.prev_stage_sell_power_position = Param(
        m.LZ_MARKETS_PREV_STAGE_TMPS, within=NonNegativeReals, default=0
    )
    m.prev_stage_buy_power_position = Param(
        m.LZ_MARKETS_PREV_STAGE_TMPS, within=NonNegativeReals, default=0
    )

    # Variables
    m.Sell_Power = Var(m.LZ_MARKETS, m.TMPS, within=NonNegativeReals)

    m.Buy_Power = Var(m.LZ_MARKETS, m.TMPS, within=NonNegativeReals)

    def final_sell_power_position_rule(mod, lz, hub, tmp):
        if mod.first_stage_flag:
            prev_position = 0
        else:
            prev_position = mod.prev_stage_sell_power_position[
                lz, hub, mod.prev_stage_tmp_map[tmp]
            ]

        return mod.Sell_Power[lz, hub, tmp] + prev_position

    m.Final_Sell_Power_Position = Expression(
        m.LZ_MARKETS, m.TMPS, rule=final_sell_power_position_rule
    )

    def final_buy_power_position_rule(mod, lz, hub, tmp):
        if mod.first_stage_flag:
            prev_position = 0
        else:
            prev_position = mod.prev_stage_buy_power_position[
                lz, hub, mod.prev_stage_tmp_map[tmp]
            ]

        return mod.Buy_Power[lz, hub, tmp] + prev_position

    m.Final_Buy_Power_Position = Expression(
        m.LZ_MARKETS, m.TMPS, rule=final_buy_power_position_rule
    )

    def total_power_sold_from_zone_rule(mod, z, tmp):
        if z in mod.MARKET_LZS:
            return sum(
                mod.Final_Sell_Power_Position[z, hub, tmp]
                for hub in mod.MARKETS_BY_LZ[z]
            )
        else:
            return 0

    m.Total_Power_Sold = Expression(
        m.LOAD_ZONES, m.TMPS, rule=total_power_sold_from_zone_rule
    )

    def total_power_sold_to_zone_rule(mod, z, tmp):
        if z in mod.MARKET_LZS:
            return sum(
                mod.Final_Buy_Power_Position[z, hub, tmp]
                for hub in mod.MARKETS_BY_LZ[z]
            )
        else:
            return 0

    m.Total_Power_Bought = Expression(
        m.LOAD_ZONES, m.TMPS, rule=total_power_sold_to_zone_rule
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:
    :return:

    """
    getattr(dynamic_components, load_balance_consumption_components).append(
        "Total_Power_Sold"
    )
    getattr(dynamic_components, load_balance_production_components).append(
        "Total_Power_Bought"
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "load_zone_markets.tab",
        ),
        set=m.LZ_MARKETS,
    )

    # Load starting market positions if applicable
    stages = check_for_integer_subdirectories(
        os.path.join(scenario_directory, subproblem)
    )

    if stages:
        # First check if we are in the first stage and set the first_stage_flag to
        # True if so; this is we'll know whether to look for previous stage positions
        # (an avoid errors when we are in the first stage)
        if int(stage) == int(stages[0]):
            first_stage_flag = {None: True}
        else:
            first_stage_flag = {None: False}

            starting_market_positions_df = pd.read_csv(
                os.path.join(
                    scenario_directory,
                    subproblem,
                    "pass_through_inputs",
                    "market_positions.tab",
                ),
                sep="\t",
                dtype={"stage": str},
            )

            starting_market_positions_df[
                "stage_index"
            ] = starting_market_positions_df.apply(
                lambda row: stages.index(row["stage"]), axis=1
            )
            prev_stage_market_positions_df = starting_market_positions_df[
                starting_market_positions_df["stage_index"] == stages.index(stage) - 1
            ]
            lz_market_timepoints = list(
                zip(
                    prev_stage_market_positions_df["load_zone"],
                    prev_stage_market_positions_df["market"],
                    prev_stage_market_positions_df["timepoint"],
                )
            )
            sell_positions_dict = dict(
                zip(
                    lz_market_timepoints,
                    prev_stage_market_positions_df["final_sell_power_position"],
                )
            )
            buy_positions_dict = dict(
                zip(
                    lz_market_timepoints,
                    prev_stage_market_positions_df["final_buy_power_position"],
                )
            )

            data_portal.data()["LZ_MARKETS_PREV_STAGE_TMPS"] = {
                None: lz_market_timepoints
            }
            data_portal.data()["prev_stage_sell_power_position"] = sell_positions_dict
            data_portal.data()["prev_stage_buy_power_position"] = buy_positions_dict
    else:
        first_stage_flag = {None: True}

    data_portal.data()["first_stage_flag"] = first_stage_flag


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    # Get load zones and their markets; only include load zones that are
    # in the load_zone_scenario_id and markets that are in the
    # market_scenario_id
    load_zone_markets = c.execute(
        """
        SELECT load_zone, market
        FROM
        -- Get included load_zones only
        (SELECT load_zone
            FROM inputs_geography_load_zones
            WHERE load_zone_scenario_id = ?
        ) as lz_tbl
        LEFT OUTER JOIN 
        -- Get markets for those load zones
        (SELECT load_zone, market
            FROM inputs_load_zone_markets
            WHERE load_zone_market_scenario_id = ?
        ) as lz_mh_tbl
        USING (load_zone)
        -- Filter out load zones whose market is not included in our 
        -- market_scenario_id
        WHERE market in (
            SELECT market
                FROM inputs_geography_markets
                WHERE market_scenario_id = ?
        );
        """,
        (
            subscenarios.LOAD_ZONE_SCENARIO_ID,
            subscenarios.LOAD_ZONE_MARKET_SCENARIO_ID,
            subscenarios.MARKET_SCENARIO_ID,
        ),
    )

    return load_zone_markets


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    load_zone_markets.tab file.
    """

    load_zone_markets = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "load_zone_markets.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerow(["load_zone", "market"])
        for row in load_zone_markets:
            writer.writerow(row)


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "market_participation.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "load_zone",
                "market",
                "timepoint",
                "period",
                "discount_factor",
                "number_years_represented",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "sell_power",
                "buy_power",
                "final_sell_power_position",
                "final_buy_power_position",
            ]
        )
        for (z, mrkt) in getattr(m, "LZ_MARKETS"):
            for tmp in getattr(m, "TMPS"):
                writer.writerow(
                    [
                        z,
                        mrkt,
                        tmp,
                        m.period[tmp],
                        m.discount_factor[m.period[tmp]],
                        m.number_years_represented[m.period[tmp]],
                        m.tmp_weight[tmp],
                        m.hrs_in_tmp[tmp],
                        value(m.Sell_Power[z, mrkt, tmp]),
                        value(m.Buy_Power[z, mrkt, tmp]),
                        value(m.Final_Sell_Power_Position[z, mrkt, tmp]),
                        value(m.Final_Buy_Power_Position[z, mrkt, tmp]),
                    ]
                )


def import_results_into_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    if not quiet:
        print("market participation")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_system_market_participation",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "market_participation.csv"), "r"
    ) as results_file:
        reader = csv.reader(results_file)

        next(reader)  # skip header
        for row in reader:
            lz = row[0]
            market = row[1]
            timepoint = row[2]
            period = row[3]
            discount_factor = row[4]
            number_years = row[5]
            timepoint_weight = row[6]
            number_of_hours_in_timepoint = row[7]
            sell_power = row[8]
            buy_power = row[9]
            final_sell_power = row[10]
            final_buy_power = row[11]

            results.append(
                (
                    scenario_id,
                    lz,
                    market,
                    subproblem,
                    stage,
                    timepoint,
                    period,
                    discount_factor,
                    number_years,
                    timepoint_weight,
                    number_of_hours_in_timepoint,
                    sell_power,
                    buy_power,
                    final_sell_power,
                    final_buy_power,
                )
            )
    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_market_participation{}
        (scenario_id, load_zone, market, subproblem_id, stage_id,
        timepoint, period, discount_factor, number_years_represented,
        timepoint_weight, number_of_hours_in_timepoint,
        sell_power, buy_power, final_sell_power, final_buy_power)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_market_participation
        (scenario_id, load_zone, market, subproblem_id, stage_id,
        timepoint, period, discount_factor, number_years_represented,
        timepoint_weight, number_of_hours_in_timepoint,
        sell_power, buy_power, final_sell_power, final_buy_power)
        SELECT
        scenario_id, load_zone, market, subproblem_id, stage_id,
        timepoint, period, discount_factor, number_years_represented,
        timepoint_weight, number_of_hours_in_timepoint,
        sell_power, buy_power, final_sell_power, final_buy_power
        FROM temp_results_system_market_participation{}
        ORDER BY scenario_id, load_zone, market, subproblem_id, stage_id, 
        timepoint;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
