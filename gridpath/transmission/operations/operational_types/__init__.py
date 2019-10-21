#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.transmission.operations.operational_types** package contains
modules to describe the various ways in which transmission-line operations are
constrained in optimization problem, e.g. as a simple transport model, or DC
OPF.
"""

from gridpath.auxiliary.auxiliary import load_tx_operational_type_modules
from gridpath.auxiliary.dynamic_components import \
    required_tx_operational_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed transmission operational type modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
            getattr(d, required_tx_operational_modules))
    # Add any components specific to the transmission operational modules
    for op_m in getattr(d, required_tx_operational_modules):
        imp_op_m = imported_tx_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)


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
    # Import needed operational modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
            getattr(d, required_tx_operational_modules))
    for op_m in getattr(d, required_tx_operational_modules):
        if hasattr(imported_tx_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_tx_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, subproblem, stage)
        else:
            pass


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
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    transmission_opchars_scenario_id = c.execute(
        """SELECT transmission_operational_chars_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_tx_opchar_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT operational_type 
            FROM 
            (SELECT transmission_line FROM inputs_transmission_portfolios
            WHERE transmission_portfolio_scenario_id = {}) AS prj_tbl
            LEFT OUTER JOIN 
            (SELECT transmission_line, operational_type
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {}) 
            AS op_type_tbl
            USING (transmission_line);""".format(
                transmission_portfolio_scenario_id,
                transmission_opchars_scenario_id
            )
        ).fetchall()
    ]

    return required_tx_opchar_modules


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required operational modules
    c = conn.cursor()
    scenario_id = subscenarios.SCENARIO_ID
    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules)

    # Validate module-specific inputs
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_tx_operational_modules[op_m]. \
                validate_module_specific_inputs(
                    subscenarios, subproblem, stage, conn)
        else:
            pass


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input .tab files
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required operational modules
    c = conn.cursor()
    scenario_id = subscenarios.SCENARIO_ID
    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules)

    # Write module-specific inputs
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m],
                   "write_module_specific_model_inputs"):
            imported_tx_operational_modules[op_m].\
                write_module_specific_model_inputs(
                    inputs_directory, subscenarios, subproblem, stage, conn)
        else:
            pass


# TODO: move this into operations.py?
def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    # Load in the required operational modules
    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = \
        load_tx_operational_type_modules(required_tx_opchar_modules)

    # Import module-specific results
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m],
                   "import_module_specific_results_to_database"):
            imported_tx_operational_modules[op_m]. \
                import_module_specific_results_to_database(
                scenario_id, subproblem, stage, c, db, results_directory
            )
        else:
            pass


def process_results(db, c, subscenarios):
    """

    :param db:
    :param c:
    :param subscenarios:
    :return:
    """

    # Load in the required operational modules
    scenario_id = subscenarios.SCENARIO_ID
    required_tx_opchar_modules = get_required_tx_opchar_modules(scenario_id, c)
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_opchar_modules)

    # Process module-specific results
    for op_m in required_tx_opchar_modules:
        if hasattr(imported_tx_operational_modules[op_m],
                   "process_module_specific_results"):
            imported_tx_operational_modules[op_m]. \
                process_module_specific_results(
                    db, c, subscenarios)
        else:
            pass