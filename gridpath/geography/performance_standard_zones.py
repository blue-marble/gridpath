# Copyright 2022 (c) Crown Copyright, GC.
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
Zones where performance standard enforced; these can be different from the load
zones and other balancing areas.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.PERFORMANCE_STANDARD_ZONES = Set()

    m.performance_standard_allow_violation = Param(m.PERFORMANCE_STANDARD_ZONES, within=Boolean, default=0)
    m.performance_standard_violation_penalty_per_emission = Param(
        m.PERFORMANCE_STANDARD_ZONES, within=NonNegativeReals, default=0
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "performance_standard_zones.tab",
        ),
        index=m.PERFORMANCE_STANDARD_ZONES,
        param=(
            m.performance_standard_allow_violation,
            m.performance_standard_violation_penalty_per_emission,
        ),
    )


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
    performance_standard_zone = c.execute(
        """SELECT performance_standard_zone, allow_violation, 
        violation_penalty_per_emission
        FROM inputs_geography_performance_standard_zones
        WHERE performance_standard_zone_scenario_id = {};
        """.format(
            subscenarios.PERFORMANCE_STANDARD_ZONE_SCENARIO_ID
        )
    )

    return performance_standard_zone


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    performance_standard_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    performance_standard_zone = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "performance_standard_zones.tab",
        ),
        "w",
        newline="",
    ) as performance_standard_zones_file:
        writer = csv.writer(performance_standard_zones_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["performance_standard_zone", "allow_violation", "violation_penalty_per_emission"]
        )

        for row in performance_standard_zone:
            writer.writerow(row)
