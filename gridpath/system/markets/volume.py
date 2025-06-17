# Copyright 2016-2025 Blue Marble Analytics LLC.
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
from pyomo.environ import Expression, Param, Constraint, NonNegativeReals, Boolean

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.project.operations.operational_types.common_functions import (
    write_tab_file_model_inputs,
)

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

    # Params limiting total transactions across all markets in a timepoint
    m.max_total_net_market_purchases_in_tmp = Param(
        m.TMPS, within=NonNegativeReals, default=Infinity
    )
    m.max_total_net_market_sales_in_tmp = Param(
        m.TMPS, within=NonNegativeReals, default=Infinity
    )

    # Params limiting total transactions across all markets in a period
    m.max_total_net_market_purchases_in_prd = Param(
        m.PERIODS, within=NonNegativeReals, default=Infinity
    )
    m.max_total_net_market_sales_in_prd = Param(
        m.PERIODS, within=NonNegativeReals, default=Infinity
    )
    # Based on 'stor' operational type
    m.max_total_net_market_sales_in_prd_include_storage_losses = Param(
        m.PERIODS, within=Boolean, default=0
    )

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

    def max_market_sales_rule(mod, market, tmp):
        return (
            mod.Total_Net_Market_Purchased_Power[market, tmp]
            >= -mod.max_market_sales[market, tmp]
        )

    m.Max_Market_Sales_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_market_sales_rule
    )

    def max_market_purchases_rule(mod, market, tmp):
        return (
            mod.Total_Net_Market_Purchased_Power[market, tmp]
            <= mod.max_market_purchases[market, tmp]
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

    def max_final_market_sales_rule(mod, market, tmp):
        return (
            mod.Total_Final_Net_Market_Purchased_Power[market, tmp]
            >= -mod.max_final_market_sales[market, tmp]
        )

    m.Max_Final_Market_Sales_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_final_market_sales_rule
    )

    def max_final_market_purchases_rule(mod, market, tmp):
        return (
            mod.Total_Final_Net_Market_Purchased_Power[market, tmp]
            <= mod.max_final_market_purchases[market, tmp]
        )

    m.Max_Final_Market_Purchases_Constraint = Constraint(
        m.MARKETS, m.TMPS, rule=max_final_market_purchases_rule
    )

    # Constraints on total transactions across all markets (e.g., a total
    # import limit or total sales limit in a timepoint)
    def total_purchases_in_tmp_constraint_rule(mod, tmp):
        return (
            sum(
                mod.Total_Net_Market_Purchased_Power[market, tmp]
                for market in mod.MARKETS
            )
            <= mod.max_total_net_market_purchases_in_tmp[tmp]
        )

    m.Total_Purchases_in_Tmp_Constraint = Constraint(
        m.TMPS, rule=total_purchases_in_tmp_constraint_rule
    )

    def total_sales_in_tmp_constraint_rule(mod, tmp):
        return (
            sum(
                mod.Total_Net_Market_Purchased_Power[market, tmp]
                for market in mod.MARKETS
            )
            >= -mod.max_total_net_market_sales_in_tmp[tmp]
        )

    m.Aggregate_Sales_in_Tmp_Constraint = Constraint(
        m.TMPS, rule=total_sales_in_tmp_constraint_rule
    )

    # Period-level totals
    # Constraints on total transactions across all markets (e.g., a total
    # import limit or total sales limit in a timepoint)
    def total_purchases_in_prd_constraint_rule(mod, prd):
        return (
            sum(
                mod.Total_Net_Market_Purchased_Power[market, tmp]
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for market in mod.MARKETS
                for tmp in mod.TMPS_IN_PRD[prd]
            )
            <= mod.max_total_net_market_purchases_in_prd[prd]
        )

    m.Total_Purchases_in_Prd_Constraint = Constraint(
        m.PERIODS, rule=total_purchases_in_prd_constraint_rule
    )

    def total_sales_in_prd_constraint_rule(mod, prd):
        return sum(
            mod.Total_Net_Market_Purchased_Power[market, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for market in mod.MARKETS
            for tmp in mod.TMPS_IN_PRD[prd]
        ) >= -mod.max_total_net_market_sales_in_prd[
            prd
        ] + mod.max_total_net_market_sales_in_prd_include_storage_losses[
            prd
        ] * sum(
            (mod.Stor_Charge_MW[prj, tmp] - mod.Stor_Discharge_MW[prj, tmp])
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (prj, tmp) in mod.PRJ_OPR_TMPS
            if mod.operational_type[prj] == "stor" and tmp in mod.TMPS_IN_PRD[prd]
        )

    m.Aggregate_Sales_in_Prd_Constraint = Constraint(
        m.PERIODS, rule=total_sales_in_prd_constraint_rule
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

    total_volume_in_tmp_filename = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "market_volume_totals_in_tmp.tab",
    )
    if os.path.exists(total_volume_in_tmp_filename):
        data_portal.load(
            filename=total_volume_in_tmp_filename,
            param=(
                m.max_total_net_market_purchases_in_tmp,
                m.max_total_net_market_sales_in_tmp,
            ),
        )

    total_volume_in_prd_filename = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "market_volume_totals_in_prd.tab",
    )
    if os.path.exists(total_volume_in_prd_filename):
        data_portal.load(
            filename=total_volume_in_prd_filename,
            param=(
                m.max_total_net_market_purchases_in_prd,
                m.max_total_net_market_sales_in_prd,
                m.max_total_net_market_sales_in_prd_include_storage_losses,
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
    market_list = c.execute(
        f"""
        SELECT market, 
        market_volume_profile_scenario_id,
        varies_by_weather_iteration, 
        varies_by_hydro_iteration
        FROM inputs_market_volume
        WHERE market_volume_scenario_id = {subscenarios.MARKET_VOLUME_SCENARIO_ID}
        -- Get volume for included markets only
        AND market in (
            SELECT market
            FROM inputs_geography_markets
            WHERE market_scenario_id = {subscenarios.MARKET_SCENARIO_ID}
        )
        """
    ).fetchall()

    # Loop over the markets for the final query since volume don't all vary
    # by the same iteration types
    n_markets = len(market_list)
    query_all = str()
    n = 1
    for (
        market,
        market_volume_profile_scenario_id,
        varies_by_weather_iteration,
        varies_by_hydro_iteration,
    ) in market_list:
        union_str = "UNION" if n < n_markets else ""

        weather_iteration_to_use = (
            weather_iteration if varies_by_weather_iteration else 0
        )
        hydro_iteration_to_use = hydro_iteration if varies_by_hydro_iteration else 0

        query_market = f"""
            -- Select market name explicitly here to print even if volume 
            -- are not found for the relevant timepoints
            SELECT '{market}' AS market, timepoint, 
                max_market_sales, max_market_purchases,
                max_final_market_sales, max_final_market_purchases
            -- Get volumes for scenario's timepoints only
            FROM (
                SELECT stage_id, timepoint 
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage}
            ) as tmp_tbl
            LEFT OUTER JOIN (
                SELECT market, stage_id, timepoint, 
                max_market_sales, max_market_purchases,
                max_final_market_sales, max_final_market_purchases
                FROM inputs_market_volume_profiles
                WHERE market = '{market}'
                AND market_volume_profile_scenario_id = {market_volume_profile_scenario_id}
                AND hydro_iteration = {hydro_iteration_to_use}
                AND weather_iteration = {weather_iteration_to_use}
            ) as volume_tbl
            USING (stage_id, timepoint)
            {union_str}
            """

        query_all += query_market
        n += 1

    c1 = conn.cursor()
    volume = c1.execute(query_all)

    # Timepoint totals
    totals_in_tmp_query = f"""
        SELECT timepoint, max_total_net_market_purchases_in_tmp, 
        max_total_net_market_sales_in_tmp
        FROM inputs_market_volume_totals_in_tmp
        WHERE market_volume_total_in_tmp_scenario_id = 
        {subscenarios.MARKET_VOLUME_TOTAL_IN_TMP_SCENARIO_ID}
        AND timepoint in (
            SELECT timepoint
            FROM inputs_temporal
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
        )
        ;
    """
    tot_in_tmp_c = conn.cursor()
    totals_in_tmp_agg = tot_in_tmp_c.execute(totals_in_tmp_query)

    # Period totals
    totals_in_prd_query = f"""
        SELECT period, max_total_net_market_purchases_in_prd, 
        max_total_net_market_sales_in_prd, max_total_net_market_sales_in_prd_include_storage_losses
        FROM inputs_market_volume_totals_in_prd
        WHERE market_volume_total_in_prd_scenario_id = 
        {subscenarios.MARKET_VOLUME_TOTAL_IN_PRD_SCENARIO_ID}
        AND period in (
            SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID} 
        )
        ;
    """
    tot_in_prd_c = conn.cursor()
    totals_in_prd_agg = tot_in_prd_c.execute(totals_in_prd_query)

    return volume, totals_in_tmp_agg, totals_in_prd_agg


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

    market_limits, totals_in_tmp, totals_in_prd = get_inputs_from_database(
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

    write_tab_file_model_inputs(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        fname="market_volume_totals_in_tmp.tab",
        data=totals_in_tmp,
        replace_nulls=True,
    )

    write_tab_file_model_inputs(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        fname="market_volume_totals_in_prd.tab",
        data=totals_in_prd,
        replace_nulls=True,
    )
