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
Balancing areas where fuel constraints are enforced; these can be different from the
load zones and other balancing areas.
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

    m.FUEL_BURN_LIMIT_BAS = Set(dimen=2)  # fuel and BA

    m.fuel_burn_limit_allow_violation = Param(
        m.FUEL_BURN_LIMIT_BAS, within=Boolean, default=0
    )
    m.fuel_burn_limit_violation_penalty_per_unit = Param(
        m.FUEL_BURN_LIMIT_BAS, within=NonNegativeReals, default=0
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "fuel_burn_limit_balancing_areas.tab",
        ),
        index=m.FUEL_BURN_LIMIT_BAS,
        param=(
            m.fuel_burn_limit_allow_violation,
            m.fuel_burn_limit_violation_penalty_per_unit,
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
    fuel_burn_limit_bas = c.execute(
        """SELECT fuel, fuel_burn_limit_ba, allow_violation, 
        violation_penalty_per_unit
        FROM inputs_geography_fuel_burn_limit_balancing_areas
        WHERE fuel_burn_limit_ba_scenario_id = {fuel_burn_limit_ba_scenario_id};
        """.format(
            fuel_burn_limit_ba_scenario_id=subscenarios.FUEL_BURN_LIMIT_BA_SCENARIO_ID
        )
    )

    return fuel_burn_limit_bas


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
    carbon_cap_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    fuel_burn_limit_bas = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "fuel_burn_limit_balancing_areas.tab",
        ),
        "w",
        newline="",
    ) as tab_file:
        writer = csv.writer(tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "fuel",
                "fuel_burn_limit_ba",
                "allow_violation",
                "violation_penalty_per_unit",
            ]
        )

        for row in fuel_burn_limit_bas:
            writer.writerow(row)
