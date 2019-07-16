#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe operational constraints on the generation infrastructure.
"""

import csv
import os.path
import pandas as pd

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Add any components specific to the operational modules
    for op_m in getattr(d, required_operational_modules):
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)


# TODO: we should check that all operational types specified by user are
#  actually implemented
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
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, subproblem, stage)
        else:
            pass


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """

    # Export module-specific results
    # Operational type modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_operational_modules[op_m].\
                export_module_specific_results(
                m, d, scenario_directory, subproblem, stage,
            )
        else:
            pass


# TODO: move this into SubScenarios class?
def get_required_opchar_modules(scenario_id, c):
    """
    Get the required operational type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    generator operational types in the scenario's portfolio. Get the list based
    on the project_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which operational type submodules we
    should validate inputs, load inputs from database, or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required operational type submodules
    """

    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    project_opchars_scenario_id = c.execute(
        """SELECT project_operational_chars_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_opchar_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT operational_type 
            FROM 
            (SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}) as prj_tbl
            LEFT OUTER JOIN 
            (SELECT project, operational_type
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}) as op_type_tbl
            USING (project);""".format(
                project_portfolio_scenario_id,
                project_opchars_scenario_id
            )
        ).fetchall()
    ]

    return required_opchar_modules


def load_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    # Load in the required operational modules
    scenario_id = subscenarios.SCENARIO_ID
    required_opchar_modules = get_required_opchar_modules(scenario_id, c)
    imported_operational_modules = load_operational_type_modules(
        required_opchar_modules)

    # Get module-specific inputs
    operational_type_inputs = {}
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m],
                   "load_inputs_from_database"):
            operational_type_inputs[op_m] = imported_operational_modules[op_m].\
                load_inputs_from_database(subscenarios, subproblem, stage, c)
        else:
            pass
    # Note: loading submodule inputs for each submodule will create a nested
    # dictionary of inputs {module_name: {submodule_name: submodule_inputs}}

    return operational_type_inputs


def validate_inputs(inputs, subscenarios, c):
    """

    :param inputs: dictionary with inputs (loaded from database) by module name
        For modules with submodules (such as operational_types), the structure
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

    # Load in the required operational modules
    # Note: submodule_inputs only has keys for the submodules that have a
    # 'load_inputs_from_database' function. We assume that you don't validate
    # inputs if there were no loaded inputs. if not, we would need to pass the
    # cursor into validate inputs and derive the required operational modules
    required_opchar_modules = submodule_inputs.keys()
    imported_operational_modules = \
        load_operational_type_modules(required_opchar_modules)

    # Validate module-specific inputs
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_operational_modules[op_m]. \
                validate_module_specific_inputs(submodule_inputs,
                                                subscenarios, c)
        else:
            pass


def write_model_inputs(inputs, inputs_directory, subscenarios):
    """
    TODO: make sure this nested structure works everywhere (gets tricky if
       the parent module of a bunch of subtype module also wants to read in its
       own inputs
    :param inputs: dictionary with inputs (loaded from database) by module name
        For modules with submodules (such as operational_types), the structure
        will be a nested dict, with the inner dictionary being the submodule
        inputs by submodule name. This inner dictionary is the one we will pass
        to 'write_module_specific_inputs'.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :return:
    """

    # Load in the required operational modules
    # Assume that you only want to write inputs for operational type modules
    # that returned something in the 'load_inputs_from_database' step
    required_opchar_modules = inputs[__name__].keys()
    imported_operational_modules = load_operational_type_modules(
        required_opchar_modules)

    # Write module-specific inputs
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m],
                   "write_module_specific_inputs"):
            imported_operational_modules[op_m]. \
                write_module_specific_inputs(inputs[__name__], inputs_directory,
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

    # Load in the required operational modules
    required_opchar_modules = get_required_opchar_modules(scenario_id, c)
    imported_operational_modules = \
        load_operational_type_modules(required_opchar_modules)

    # Import module-specific results
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m],
                   "import_module_specific_results_to_database"):
            imported_operational_modules[op_m]. \
                import_module_specific_results_to_database(
                scenario_id, subproblem, stage, c, db, results_directory
            )
        else:
            pass
