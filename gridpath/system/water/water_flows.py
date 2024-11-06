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
Flows across water links.
"""

import csv
import os.path

from pyomo.environ import (
    Param,
    NonNegativeReals,
    Var,
    Constraint,
    Any,
    value,
)

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import create_results_df


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
    # TODO: units!!!
    # Start with these as params BUT:
    # These are probably not params but expressions with a non-linear
    # relationship to elevation; most of the curves look they can be
    # piecewise linear
    m.min_flow_vol_per_second = Param(
        m.WATER_LINKS, m.TMPS, within=NonNegativeReals, default=0
    )
    m.max_flow_vol_per_second = Param(m.WATER_LINKS, m.TMPS, default=float("inf"))

    # ### Variables ### #
    m.Water_Link_Flow_Rate_Vol_per_Sec = Var(
        m.WATER_LINKS, m.TMPS, within=NonNegativeReals
    )

    # ### Constraints ### #
    def min_flow_rule(mod, wl, tmp):
        return (
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp]
            >= mod.min_flow_vol_per_second[wl, tmp]
        )

    m.Water_Link_Minimum_Flow_Constraint = Constraint(
        m.WATER_LINKS, m.TMPS, rule=min_flow_rule
    )

    def max_flow_rule(mod, wl, tmp):
        return (
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp]
            <= mod.max_flow_vol_per_second[wl, tmp]
        )

    m.Water_Link_Maximum_Flow_Constraint = Constraint(
        m.WATER_LINKS, m.TMPS, rule=max_flow_rule
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
        "water_flow_bounds.tab",
    )
    if os.path.exists(fname):
        data_portal.load(
            filename=fname,
            param=(m.min_flow_vol_per_second, m.max_flow_vol_per_second),
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
    water_flows = c.execute(
        f"""SELECT water_link, timepoint, 
            min_flow_vol_per_second, max_flow_vol_per_second
            FROM inputs_system_water_flows
            WHERE water_flow_scenario_id = 
            {subscenarios.WATER_FLOW_SCENARIO_ID}
            AND timepoint
            IN (SELECT timepoint
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage})
            ;
            """
    )

    return water_flows


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
    water_flow_bounds.tab file.
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

    water_flows = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    water_flow_bounds_list = [row for row in water_flows]
    if water_flow_bounds_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "water_flow_bounds.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "water_link",
                    "timepoint",
                    "min_flow_vol_per_second",
                    "max_flow_vol_per_second",
                ]
            )

            for row in water_flow_bounds_list:
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
    results_columns = [
        "water_flow",
    ]
    data = [
        [
            wl,
            tmp,
            value(m.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp]),
        ]
        for wl in m.WATER_LINKS
        for tmp in m.TMPS
    ]
    results_df = create_results_df(
        index_columns=["water_link", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    results_df.to_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "water_link_timepoint.csv",
        ),
        sep=",",
        index=True,
    )


# TODO: results import
