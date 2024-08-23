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
The **gridpath.transmission.operations.operational_types** package contains
modules to describe the various ways in which transmission-line operations are
constrained in optimization problem, e.g. as a simple transport model, or DC
OPF.
"""
import os.path
import pandas as pd

from gridpath.transmission.operations.common_functions import (
    load_tx_operational_type_modules,
)


# TODO: missing test for this module


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
    Go through each relevant operational type and add the module components
    for that operational type.
    """
    # Import needed transmission operational type modules
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "transmission_lines.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "tx_capacity_type", "tx_operational_type"],
    )

    required_tx_operational_modules = df.tx_operational_type.unique()

    # Import needed transmission operational type modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_operational_modules
    )
    # Add any components specific to the transmission operational modules
    for op_m in required_tx_operational_modules:
        imp_op_m = imported_tx_operational_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(
                m,
                d,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )


# Input-Output
###############################################################################


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
    Go through each relevant operational type and add load the model data
    for that operational type.

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Import needed operational modules
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "transmission_lines.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "tx_capacity_type", "tx_operational_type"],
    )

    required_tx_operational_modules = df.tx_operational_type.unique()

    # Import needed transmission operational type modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_operational_modules
    )
    for op_m in required_tx_operational_modules:
        if hasattr(imported_tx_operational_modules[op_m], "load_model_data"):
            imported_tx_operational_modules[op_m].load_model_data(
                m,
                d,
                data_portal,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )


# TODO: move this into SubScenarios class?
def get_required_tx_opchar_modules(scenario_id, c):
    """
    Get the required tx operational type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    tx operational types in the scenario's portfolio. Get the list based
    on the transmission_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which operational type submodules we
    should validate inputs, get inputs from database, or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required tx operational type submodules
    """

    transmission_portfolio_scenario_id = c.execute(
        """SELECT transmission_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(
            scenario_id
        )
    ).fetchone()[0]

    transmission_opchars_scenario_id = c.execute(
        """SELECT transmission_operational_chars_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(
            scenario_id
        )
    ).fetchone()[0]

    required_tx_opchar_modules = [
        p[0]
        for p in c.execute(
            """SELECT DISTINCT operational_type 
            FROM 
            (SELECT transmission_line FROM inputs_transmission_portfolios
            WHERE transmission_portfolio_scenario_id = {}) AS prj_tbl
            INNER JOIN 
            (SELECT transmission_line, operational_type
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {}) 
            AS op_type_tbl
            USING (transmission_line);""".format(
                transmission_portfolio_scenario_id, transmission_opchars_scenario_id
            )
        ).fetchall()
    ]

    return required_tx_opchar_modules


# Database
###############################################################################


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
    Go through each relevant operational type and write the model inputs
    for that operational type based on the database.

    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required operational modules
    c = conn.cursor()

    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules
    )

    # Write module-specific inputs
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m], "write_model_inputs"):
            imported_tx_operational_modules[op_m].write_model_inputs(
                scenario_directory,
                scenario_id,
                subscenarios,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                conn,
            )


# TODO: move this into operations.py?
def import_results_into_database(
    scenario_id,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    c,
    db,
    results_directory,
    quiet,
):
    """
    Go through each relevant operational type and import the results into the
    database for that operational type.

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """

    # Load in the required operational modules
    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules
    )

    # Import module-specific results
    for op_m in required_tx_opchar_modules:
        if hasattr(
            imported_tx_operational_modules[op_m], "import_model_results_to_database"
        ):
            imported_tx_operational_modules[op_m].import_model_results_to_database(
                scenario_id, subproblem, stage, c, db, results_directory, quiet
            )


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Go through each relevant operational type and process the results
    for that operational type.

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """

    # Load in the required operational modules

    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules
    )

    # Process module-specific results
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m], "process_model_results"):
            imported_tx_operational_modules[op_m].process_model_results(
                db, c, scenario_id, subscenarios, quiet
            )


# Validation
###############################################################################


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
    Go through each relevant operational type and validate the database inputs
    for that operational type.

    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required operational modules
    c = conn.cursor()

    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules
    )

    # Validate module-specific inputs
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m], "validate_inputs"):
            imported_tx_operational_modules[op_m].validate_inputs(
                scenario_id, subscenarios, subproblem, stage, conn
            )
