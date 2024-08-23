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

"""
This module adds the main load-balance consumption component, the static
load requirement to the load-balance constraint.
"""

import csv
import os.path
from pyomo.environ import Param, NonNegativeReals

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import load_balance_consumption_components
from gridpath.common_functions import create_results_df
from gridpath.system.load_balance import LOAD_ZONE_TMP_DF


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds the static load to the load balance dynamic components.
    """
    getattr(dynamic_components, load_balance_consumption_components).append(
        "static_load_mw"
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
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we add the *static_load_mw* parameter -- the load requirement --
    defined for each load zone *z* and timepoint *tmp*, and add it to the
    dynamic load-balance consumption components that will go into the load
    balance constraint in the *load_balance* module (i.e. the constraint's
    rhs).
    """

    # Static load
    m.static_load_mw = Param(m.LOAD_ZONES, m.TMPS, within=NonNegativeReals)

    record_dynamic_components(dynamic_components=d)


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
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "load_mw.tab",
        ),
        param=m.static_load_mw,
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
    # Select only profiles for timepoints form the correct temporal
    # scenario and the correct subproblem
    # Select only profiles of load_zones that are part of the correct
    # load_zone_scenario
    # Select only profiles for the correct load_scenario
    loads = c.execute(
        f"""SELECT load_zone, timepoint, load_mw
        FROM inputs_system_load
        INNER JOIN
        (SELECT timepoint
        FROM inputs_temporal
        WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
        AND subproblem_id ={subproblem}
        AND stage_id = {stage}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT load_zone
        FROM inputs_geography_load_zones
        WHERE load_zone_scenario_id = {subscenarios.LOAD_ZONE_SCENARIO_ID}) as relevant_load_zones
        USING (load_zone)
        WHERE load_scenario_id = {subscenarios.LOAD_SCENARIO_ID}
        AND weather_iteration = {weather_iteration}
        AND stage_id = {stage}
        """
    )

    return loads


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
    # loads = get_inputs_from_database(
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
    load_mw.tab file.
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

    loads = get_inputs_from_database(
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
            "load_mw.tab",
        ),
        "w",
        newline="",
    ) as load_tab_file:
        writer = csv.writer(load_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["LOAD_ZONES", "timepoint", "load_mw"])

        for row in loads:
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
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "static_load_mw",
    ]
    data = [
        [
            lz,
            tmp,
            m.static_load_mw[lz, tmp],
        ]
        for lz in getattr(m, "LOAD_ZONES")
        for tmp in getattr(m, "TMPS")
    ]
    results_df = create_results_df(
        index_columns=["load_zone", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, LOAD_ZONE_TMP_DF)[c] = None
    getattr(d, LOAD_ZONE_TMP_DF).update(results_df)
