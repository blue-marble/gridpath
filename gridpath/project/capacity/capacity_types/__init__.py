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
    should validate inputs, load inputs from database , or save results to
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


def load_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    # Load in the required capacity type modules
    required_capacity_type_modules = get_required_capacity_type_modules(
        subscenarios.SCENARIO_ID, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Get module-specific inputs
    capacity_type_inputs = {}
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "load_inputs_from_database"):
            capacity_type_inputs[op_m] = imported_capacity_type_modules[op_m].\
                load_inputs_from_database(subscenarios, subproblem, stage, c)
        else:
            pass
    # Note: loading submodule inputs for each submodule will create a nested
    # dictionary of inputs {module_name: {submodule_name: submodule_inputs}}

    return capacity_type_inputs


def validate_inputs(inputs, subscenarios, c):
    """

    :param inputs: dictionary with inputs (loaded from database) by module name
        For modules with submodules (such as capacity_types), the structure
        will be a nested dict, with the inner dictionary being the submodule
        inputs by submodule name. This inner dictionary is the one we will pass
        to 'validate_module_specific_inputs'.
    :param subscenarios: SubScenarios object with all subscenario info
    :param c: database cursor
    :return:
    """

    # Retrieve the inner inputs dictionary (submodule inputs by submodule name)
    # from the outer inputs dictionary (inputs by module name)
    submodule_inputs = inputs[__name__]

    # Load in the required capacity type modules
    # Note: submodule_inputs only has keys for the submodules that have a
    # 'load_inputs_from_database' function. We assume that you don't validate
    # inputs if there were no loaded inputs. if not, we would need to pass the
    # cursor into validate inputs and derive the required capacity type modules
    required_capacity_type_modules = submodule_inputs.keys()
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Validate module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_capacity_type_modules[op_m]. \
                validate_module_specific_inputs(submodule_inputs,
                                                subscenarios, c)
        else:
            pass


def write_model_inputs(inputs, inputs_directory, subscenarios):
    """

    :param inputs: dictionary with inputs (loaded from database) by module name
        For modules with submodules (such as capacity_types), the structure
        will be a nested dict, with the inner dictionary being the submodule
        inputs by submodule name. This inner dictionary is the one we will pass
        to 'write_module_specific_inputs'.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :return:
    """

    # Retrieve the inner inputs dictionary (submodule inputs by submodule name)
    # from the outer inputs dictionary (inputs by module name)
    submodule_inputs = inputs[__name__]

    # Load in the required capacity type modules
    # Note: submodule_inputs only has keys for the submodules that have a
    # 'load_inputs_from_database' function. We assume that you don't validate
    # inputs if there were no loaded inputs. if not, we would need to pass the
    # cursor into validate inputs and derive the required capacity type modules
    required_capacity_type_modules = submodule_inputs.keys()
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Get module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "write_module_specific_inputs"):
            imported_capacity_type_modules[op_m]. \
                write_module_specific_inputs(submodule_inputs, inputs_directory,
                                             subscenarios)
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
