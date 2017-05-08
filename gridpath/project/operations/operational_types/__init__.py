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

    # First, add any components specific to the operational modules
    for op_m in getattr(d, required_operational_modules):
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
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
                m, d, scenario_directory, horizon, stage,
            )
        else:
            pass


def get_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    
    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    # TODO: get these directly from database
    project_op_types = \
        pd.read_csv(
            os.path.join(inputs_directory, "projects.tab"),
            sep="\t", usecols=["project",
                               "operational_type"]
        )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    required_operational_modules = \
            project_op_types.operational_type.unique()

    # Get module-specific inputs
    # Load in the required operational modules
    imported_operational_modules = \
        load_operational_type_modules(required_operational_modules)

    for op_m in required_operational_modules:
        if hasattr(imported_operational_modules[op_m],
                   "get_module_specific_inputs_from_database"):
            imported_operational_modules[op_m]. \
                get_module_specific_inputs_from_database(
                subscenarios, c, inputs_directory
            )
        else:
            pass


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Required modules are the unique set of generator operational types in
    # the scenario's portfolio
    # This list will be used to know which operational type modules to load
    # Get the list based on the project_operational_chars_scenario_id of this
    # scenario_id
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
            FROM inputs_project_portfolios
            LEFT OUTER JOIN inputs_project_operational_chars
            USING (project)
            WHERE project_portfolio_scenario_id = {}
            AND project_operational_chars_scenario_id = {}""".format(
                project_portfolio_scenario_id,
                project_opchars_scenario_id
            )
        ).fetchall()
    ]

    # Import module-specific results
    # Load in the required operational modules
    imported_operational_modules = \
        load_operational_type_modules(required_opchar_modules)

    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m],
                   "import_module_specific_results_to_database"):
            imported_operational_modules[op_m]. \
                import_module_specific_results_to_database(
                scenario_id, c, db, results_directory
            )
        else:
            pass
