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


def get_inputs_from_database(subscenarios, subproblem, stage, c, inputs_directory):
    """

    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """
    # Required modules are the unique set of generator capacity types
    # This list will be used to know which capacity type modules to load
    # Get the list based on the project_portfoio_scenario_id of this
    # scenario_id
    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(subscenarios.SCENARIO_ID)
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

    # Load in the required capacity type modules
    imported_capacity_type_modules = \
        load_gen_storage_capacity_type_modules(required_capacity_type_modules)

    # Get module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "get_module_specific_inputs_from_database"):
            imported_capacity_type_modules[op_m]. \
                get_module_specific_inputs_from_database(
                subscenarios, c, inputs_directory
            )
        else:
            pass


def import_results_into_database(scenario_id, subproblem, stage, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    # Required modules are the unique set of generator capacity types
    # This list will be used to know which capacity type modules to load
    # Get the list based on the project_portfolio_scenario_id of this
    # scenario_id
    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {};
        """.format(scenario_id)
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

    # Import module-specific results
    # Load in the required capacity type modules
    imported_capacity_type_modules = \
        load_gen_storage_capacity_type_modules(required_capacity_type_modules)

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
