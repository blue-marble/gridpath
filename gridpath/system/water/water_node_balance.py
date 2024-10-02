# Copyright 2016-2024 Blue Marble Analytics LLC.
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

"""
Water nodes and connections for modeling cascading hydro systems.
"""

import csv
import os.path
from pyomo.environ import (
    Set,
    Param,
    Boolean,
    NonNegativeReals,
    Var,
    Constraint,
    Expression,
    Any,
    value,
)

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import create_results_df
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)


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
    """

    :param m:
    :param d:
    :return:
    """

    # TODO: units
    m.exogenous_water_inflow_vol_per_sec = Param(
        m.WATER_NODES, m.TMPS, default=0, within=NonNegativeReals
    )

    def water_links_to_by_water_node_rule(mod, wn):
        wl_list = []
        for wl in mod.WATER_LINKS:
            if mod.water_node_to[wl] == wn:
                wl_list.append(wl)

        return wl_list

    def water_links_from_by_water_node_rule(mod, wn):
        wl_list = []
        for wl in mod.WATER_LINKS:
            if mod.water_node_from[wl] == wn:
                wl_list.append(wl)

        return wl_list

    m.WATER_LINKS_TO_BY_WATER_NODE = Set(
        m.WATER_NODES, initialize=water_links_to_by_water_node_rule
    )

    m.WATER_LINKS_FROM_BY_WATER_NODE = Set(
        m.WATER_NODES, initialize=water_links_from_by_water_node_rule
    )

    # exog inflow + var inflow - res_store_water - evap losses + res discharge
    # = water outflow

    # TODO: units with different timepoint durations
    # TODO: add time delays
    def water_node_mass_balance_rule(mod, wn, tmp):
        # Skip constraint for the last node with no links out
        if not mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]:
            return Constraint.Skip
        # For other nodes, apply the mass balance constraint
        else:
            # TODO: sum over all reservoirs at a node
            res = "temp"
            return (
                mod.exogenous_water_inflow_vol_per_sec[wn, tmp]
                + sum(
                    mod.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp]
                    for wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn]
                )
                + sum(
                    mod.Net_Reservoir_Outflow[res, tmp]
                    for res in mod.RESERVOIRS_BY_NODE[wn]
                )
            ) == sum(
                mod.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp]
                for wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]
            )

    m.Water_Node_Mass_Balance_Constraint = Constraint(
        m.WATER_NODES, m.TMPS, rule=water_node_mass_balance_rule
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
    fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "water_inflows.tab",
    )

    data_portal.load(
        filename=fname,
        param=m.exogenous_water_inflow_vol_per_sec,
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
    water_inflows = c.execute(
        f"""SELECT water_node, timepoint, exogenous_water_inflow_vol_per_sec
            FROM inputs_system_water_inflows
            WHERE water_inflow_scenario_id = 
            {subscenarios.WATER_INFLOW_SCENARIO_ID}
            AND timepoint
            IN (SELECT timepoint
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage})
            ;
            """
    )

    return water_inflows


def validate_inputs(
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
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # carbon_cap_zone = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


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
    Get inputs from database and write out the model input
    water_inflows.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
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

    water_inflows = get_inputs_from_database(
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
            "water_inflows.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "water_node",
                "timepoint",
                "exogenous_water_inflow_vol_per_sec",
            ]
        )

        for row in water_inflows:
            writer.writerow(row)


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    # TODO: add results for node balance
    pass
    # results_columns = [
    #     "water_flow",
    # ]
    # data = [
    #     [
    #         wl,
    #         tmp,
    #         value(m.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp]),
    #     ]
    #     for wl in m.WATER_LINKS
    #     for tmp in m.TMPS
    # ]
    # results_df = create_results_df(
    #     index_columns=["water_node", "timepoint"],
    #     results_columns=results_columns,
    #     data=data,
    # )
    #
    # results_df.to_csv(
    #     os.path.join(
    #         scenario_directory,
    #         weather_iteration,
    #         hydro_iteration,
    #         availability_iteration,
    #         subproblem,
    #         stage,
    #         "results",
    #         "water_node_timepoint.csv",
    #     ),
    #     sep=",",
    #     index=True,
    # )


# TODO: results import
