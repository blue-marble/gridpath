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
Zones where instantaneous penetration target will be enforced; these can be different from the load zones
and reserve balancing areas.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals

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

    m.INSTANTANEOUS_PENETRATION_ZONES = Set()

    m.allow_violation_min_penetration = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES, within=Boolean
    )
    m.violation_penalty_min_penetration_per_mwh = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES, within=NonNegativeReals
    )
    m.allow_violation_max_penetration = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES, within=Boolean
    )
    m.violation_penalty_max_penetration_per_mwh = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES, within=NonNegativeReals
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
            str(subproblem),
            str(stage),
            "inputs",
            "instantaneous_penetration_zones.tab",
        ),
        index=m.INSTANTANEOUS_PENETRATION_ZONES,
        param=(
            m.allow_violation_min_penetration,
            m.violation_penalty_min_penetration_per_mwh,
            m.allow_violation_max_penetration,
            m.violation_penalty_max_penetration_per_mwh,
        ),
    )


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    subproblem,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    instantaneous_penetration_zones = c.execute(
        """SELECT instantaneous_penetration_zone, 
        allow_violation_min_penetration, 
        violation_penalty_min_penetration_per_mwh, 
        allow_violation_max_penetration,
        violation_penalty_max_penetration_per_mwh
           FROM inputs_geography_instantaneous_penetration_zones
           WHERE instantaneous_penetration_zone_scenario_id = {};""".format(
            subscenarios.INSTANTANEOUS_PENETRATION_ZONE_SCENARIO_ID
        )
    )

    return instantaneous_penetration_zones


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
    # instantaneous_penetration_zones = get_inputs_from_database(
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
    instantaneous_penetration_zones.tab file.
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

    instantaneous_penetration_zones = get_inputs_from_database(
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
            str(subproblem),
            str(stage),
            "inputs",
            "instantaneous_penetration_zones.tab",
        ),
        "w",
        newline="",
    ) as instantaneous_penetration_zones_tab_file:
        writer = csv.writer(
            instantaneous_penetration_zones_tab_file,
            delimiter="\t",
            lineterminator="\n",
        )

        # Write header
        writer.writerow(
            [
                "instantaneous_penetration_zone",
                "allow_violation_min_penetration",
                "violation_penalty_min_penetration_per_mwh",
                "allow_violation_max_penetration",
                "violation_penalty_max_penetration_per_mwh",
            ]
        )

        for (
            ipz,
            allow_min,
            vio_min,
            allow_max,
            vio_max,
        ) in instantaneous_penetration_zones:
            if allow_min is None:
                allow_min = "."
            if vio_min is None:
                vio_min = "."
            if allow_max is None:
                allow_max = "."
            if vio_max is None:
                vio_max = "."
            writer.writerow([ipz, allow_min, vio_min, allow_max, vio_max])
