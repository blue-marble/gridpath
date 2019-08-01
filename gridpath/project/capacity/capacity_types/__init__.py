#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.capacity.capacity_types** package contains modules to
describe the various ways in which project capacity can be treated in the
optimization problem, e.g. as specified, available to be built, available to
be retired, etc.
"""

from gridpath.auxiliary.auxiliary import load_gen_storage_capacity_type_modules

# TODO: we should shorten the names of the capacity-type modules, e.g. to
#   gen_specified, gen_specified_lin_ret, gen_new, stor_specified, stor_new,
#   shift_load_supply_curve
# TODO: We should decide on naming conventions for sets, variables, etc. in
#  the capacity type modules


def get_required_capacity_type_modules(scenario_id, c):
    """
    Get the required capacity type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    generator capacity types in the scenario's portfolio. Get the list based
    on the project_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which capacity type submodules we
    should validate inputs, get inputs from database , or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required capacity type submodules
    """

    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_capacity_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT capacity_type 
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}""".format(
                project_portfolio_scenario_id
            )
        ).fetchall()
    ]

    return required_capacity_type_modules


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required capacity type modules
    c = conn.cursor()
    scenario_id = subscenarios.SCENARIO_ID
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Validate module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_capacity_type_modules[op_m]. \
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
    c = conn.cursor()
    # Load in the required capacity type modules
    scenario_id = subscenarios.SCENARIO_ID
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Get module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "write_module_specific_model_inputs"):
            imported_capacity_type_modules[op_m].\
                write_module_specific_model_inputs(
                    inputs_directory, subscenarios, subproblem, stage, conn)
        else:
            pass


def import_results_into_database(scenario_id, subproblem, stage,
                                 c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    # Load in the required capacity type modules
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Import module-specific results
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "import_module_specific_results_into_database"):
            imported_capacity_type_modules[op_m]. \
                import_module_specific_results_into_database(
                scenario_id, subproblem, stage, c, db, results_directory
            )
        else:
            pass
