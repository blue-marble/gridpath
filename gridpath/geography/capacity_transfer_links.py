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
Zones where PRM is enforced; these can be different from the load
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

    m.PRM_ZONES_CAPACITY_TRANSFER_ZONES = Set(dimen=2, within=m.PRM_ZONES * m.PRM_ZONES)


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
            "prm_capacity_transfer_zone_links.tab",
        ),
        set=m.PRM_ZONES_CAPACITY_TRANSFER_ZONES,
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
    prm_zone_transfers = c.execute(
        f"""SELECT prm_zone, prm_capacity_transfer_zones
        FROM inputs_geography_prm_capacity_transfers
        WHERE prm_capacity_transfer_scenario_id={subscenarios.PRM_CAPACITY_TRANSFER_SCENARIO_ID};
        """
    )

    return prm_zone_transfers


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
    # prm_zone_transfers = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    prm_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    prm_zone_transfers = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "prm_capacity_transfer_zone_links.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["prm_zone", "prm_capacity_transfer_zones"])

        for row in prm_zone_transfers:
            writer.writerow(row)
