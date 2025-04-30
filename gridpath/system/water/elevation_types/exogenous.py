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

""" """

import csv
import os.path
from pyomo.environ import (
    Set,
    Param,
    Boolean,
    NonNegativeReals,
    NonNegativeIntegers,
    Any,
)

from gridpath.auxiliary.auxiliary import subset_init_by_param_value
from gridpath.auxiliary.db_interface import directories_to_db_values


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
    # Volume-elevation relationship
    m.EXOG_ELEV_WATER_NODES_W_RESERVOIRS = Set(
        within=m.WATER_NODES_W_RESERVOIRS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "WATER_NODES_W_RESERVOIRS", "elevation_type", "exogenous"
        ),
    )

    m.reservoir_exogenous_elevation = Param(
        m.EXOG_ELEV_WATER_NODES_W_RESERVOIRS, m.TMPS, within=NonNegativeReals
    )


def elevation_rule(mod, r, tmp):
    return mod.reservoir_exogenous_elevation[r, tmp]


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
            "reservoir_exogenous_elevations.tab",
        ),
        param=m.reservoir_exogenous_elevation,
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
    exogenous_elevations = c.execute(
        f"""SELECT water_node, timepoint, reservoir_exogenous_elevation
        FROM inputs_system_water_node_reservoir_exogenous_elevations
        WHERE (water_node, exogenous_elevation_id)
        IN (SELECT water_node, exogenous_elevation_id
            FROM inputs_system_water_node_reservoirs
            WHERE water_node_reservoir_scenario_id = 
            {subscenarios.WATER_NODE_RESERVOIR_SCENARIO_ID}
            AND elevation_type = 'exogenous'
        )
        AND water_node IN (
                    SELECT water_node_from as water_node
                    FROM inputs_geography_water_network
                    WHERE water_network_scenario_id = 
                    {subscenarios.WATER_NETWORK_SCENARIO_ID}
                    UNION
                    SELECT water_node_to as water_node
                    FROM inputs_geography_water_network
                    WHERE water_network_scenario_id = 
                    {subscenarios.WATER_NETWORK_SCENARIO_ID}
                )
        AND timepoint
                IN (SELECT timepoint
                    FROM inputs_temporal
                    WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                    AND subproblem_id = {subproblem}
                    AND stage_id = {stage})
        AND hydro_iteration = {hydro_iteration}
        ;
        """
    )

    return exogenous_elevations


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
    water_network.tab file.
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

    exogenous_elevations = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    # Volume to elevation curves
    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "reservoir_exogenous_elevations.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "reservoir",
                "timepoint",
                "exogenous_elevation",
            ]
        )

        for row in exogenous_elevations:
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
    # TODO: export elevation here
    pass


# TODO: results import
