# Copyright 2016-2020 Blue Marble Analytics LLC.
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
Zones where local capacity constraint is enforced; these can be different from
the load zones and other balancing areas.
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

    m.LOCAL_CAPACITY_ZONES = Set()

    m.local_capacity_allow_violation = Param(
        m.LOCAL_CAPACITY_ZONES, within=Boolean, default=0
    )
    m.local_capacity_violation_penalty_per_mw = Param(
        m.LOCAL_CAPACITY_ZONES, within=NonNegativeReals, default=0
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
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
            str(subproblem),
            str(stage),
            "inputs",
            "local_capacity_zones.tab",
        ),
        index=m.LOCAL_CAPACITY_ZONES,
        param=(
            m.local_capacity_allow_violation,
            m.local_capacity_violation_penalty_per_mw,
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
    local_capacity_zones = c.execute(
        """SELECT local_capacity_zone, allow_violation,
        violation_penalty_per_mw
        FROM inputs_geography_local_capacity_zones
        WHERE local_capacity_zone_scenario_id = {};
        """.format(
            subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID
        )
    )

    return local_capacity_zones


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
    # prm_zones = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    local_capacity_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    local_capacity_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "local_capacity_zones.tab",
        ),
        "w",
        newline="",
    ) as local_capacity_zones_file:
        writer = csv.writer(
            local_capacity_zones_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            ["local_capacity_zone", "allow_violation", "violation_penalty_per_mw"]
        )

        for row in local_capacity_zones:
            writer.writerow([row[0], row[1], row[2]])
