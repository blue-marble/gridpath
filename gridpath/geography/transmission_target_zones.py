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
Zones where transmission target will be enforced; these can be different from the load zones
and reserve balancing areas.
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

    m.TRANSMISSION_TARGET_ZONES = Set()

    m.transmission_target_allow_violation = Param(
        m.TRANSMISSION_TARGET_ZONES, within=Boolean, default=0
    )
    m.transmission_target_violation_penalty_per_mwh = Param(
        m.TRANSMISSION_TARGET_ZONES, within=NonNegativeReals, default=0
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_target_zones.tab",
        ),
        index=m.TRANSMISSION_TARGET_ZONES,
        param=(
            m.transmission_target_allow_violation,
            m.transmission_target_violation_penalty_per_mwh,
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
    transmission_target_zones = c.execute(
        """SELECT transmission_target_zone, allow_violation, 
        violation_penalty_per_mwh
           FROM inputs_geography_transmission_target_zones
           WHERE transmission_target_zone_scenario_id = {};""".format(
            subscenarios.TRANSMISSION_TARGET_ZONE_SCENARIO_ID
        )
    )

    return transmission_target_zones


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
    # Validation to be added


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    transmission_target_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    transmission_target_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_target_zones.tab",
        ),
        "w",
        newline="",
    ) as transmission_target_zones_tab_file:
        writer = csv.writer(
            transmission_target_zones_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            ["transmission_target_zone", "allow_violation", "violation_penalty_per_mwh"]
        )

        for row in transmission_target_zones:
            writer.writerow(row)
