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

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    m.LF_RESERVES_UP_ZONES = Set()

    m.lf_reserves_up_allow_violation = Param(m.LF_RESERVES_UP_ZONES, within=Boolean)
    m.lf_reserves_up_violation_penalty_per_mw = Param(
        m.LF_RESERVES_UP_ZONES, within=NonNegativeReals
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "load_following_up_balancing_areas.tab",
        ),
        select=("balancing_area", "allow_violation", "violation_penalty_per_mw"),
        index=m.LF_RESERVES_UP_ZONES,
        param=(
            m.lf_reserves_up_allow_violation,
            m.lf_reserves_up_violation_penalty_per_mw,
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
    lf_up_bas = c.execute(
        """SELECT lf_reserves_up_ba, allow_violation,
        violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_lf_reserves_up_bas
           WHERE lf_reserves_up_ba_scenario_id = {};""".format(
            subscenarios.LF_RESERVES_UP_BA_SCENARIO_ID
        )
    )

    return lf_up_bas


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
    # lf_up_bas = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    load_following_up_balancing_areas.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    lf_up_bas = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "load_following_up_balancing_areas.tab",
        ),
        "w",
        newline="",
    ) as lf_up_bas_tab_file:
        writer = csv.writer(lf_up_bas_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "balancing_area",
                "allow_violation",
                "violation_penalty_per_mw",
                "reserve_to_energy_adjustment",
            ]
        )

        for row in lf_up_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
