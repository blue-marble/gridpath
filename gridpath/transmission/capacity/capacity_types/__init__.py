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
The **gridpath.transmission.capacity.capacity_types** package contains
modules to describe the various ways in which transmission-line capacity can be
treated in the optimization problem, e.g. as specified, available to be
built, available to be retired, etc.
"""

import pandas as pd
import os.path

from gridpath.transmission.capacity.common_functions import \
    load_tx_capacity_type_modules


def get_required_capacity_type_modules(scenario_id, subscenarios, conn):
    """
    Get the required tx capacity type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    tx capacity types in the scenario's portfolio. Get the list based
    on the project_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which tx capacity type submodules we
    should validate inputs, get inputs from database, or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param subscenarios: SubScenarios object with all subscenario info
    :param conn: database connection
    :return: List of the required tx capacity type submodules
    """
    c = conn.cursor()
    required_tx_capacity_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT capacity_type
            FROM inputs_transmission_portfolios
            LEFT OUTER JOIN
            (SELECT transmission_line, load_zone_from, load_zone_to
            FROM inputs_transmission_load_zones
            WHERE transmission_load_zone_scenario_id = {}) as tx_load_zones
            USING (transmission_line)
            INNER JOIN
            (SELECT transmission_line
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {})
            USING (transmission_line)
            WHERE transmission_portfolio_scenario_id = {};""".format(
                subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
            )
        ).fetchall()
    ]

    return required_tx_capacity_modules


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required tx capacity type modules

    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, subscenarios, conn)
    imported_capacity_type_modules = load_tx_capacity_type_modules(
            required_capacity_type_modules)

    # Validate module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "validate_inputs"):
            imported_capacity_type_modules[op_m]. \
                validate_inputs(
                    scenario_id, subscenarios, subproblem, stage, conn)
        else:
            pass


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input .tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    # Load in the required capacity type modules
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, subscenarios, conn)
    imported_capacity_type_modules = load_tx_capacity_type_modules(
            required_capacity_type_modules)

    # Write module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "write_model_inputs"):
            imported_capacity_type_modules[op_m]. \
                write_model_inputs(
                    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
            )
        else:
            pass
