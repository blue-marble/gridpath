#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe ELCC-eligibility constraints on infrastructure.
"""

import os.path
import pandas as pd
from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import required_prm_modules
from gridpath.auxiliary.auxiliary import load_prm_type_modules


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    project_dynamic_data = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project",
                               "prm_type"]
        )

    # Required modules are the unique set of generator PRM types
    # This list will be used to know which PRM type modules to load
    setattr(d, required_prm_modules,
            [prm_type for prm_type in project_dynamic_data.prm_type.unique()
             if prm_type != "."]
            )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed PRM modules
    imported_prm_modules = \
        load_prm_type_modules(getattr(d, required_prm_modules))

    # Add any components specific to the PRM modules
    for prm_m in getattr(d, required_prm_modules):
        imp_prm_m = imported_prm_modules[prm_m]
        if hasattr(imp_prm_m, "add_module_specific_components"):
            imp_prm_m.add_module_specific_components(m, d)

    # For each PRM project, get the ELCC-eligible capacity
    def elcc_eligible_capacity_rule(mod, g, p):
        prm_type = mod.prm_type[g]
        return imported_prm_modules[prm_type]. \
            elcc_eligible_capacity_rule(mod, g, p)

    m.ELCC_Eligible_Capacity_MW = Expression(
        m.PRM_PROJECT_OPERATIONAL_PERIODS,
        rule=elcc_eligible_capacity_rule
    )


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
    imported_prm_modules = \
        load_prm_type_modules(getattr(d, required_prm_modules))
    for prm_m in getattr(d, required_prm_modules):
        if hasattr(imported_prm_modules[prm_m],
                   "load_module_specific_data"):
            imported_prm_modules[prm_m].load_module_specific_data(
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
    imported_prm_modules = \
        load_prm_type_modules(getattr(d, required_prm_modules))
    for prm_m in getattr(d, required_prm_modules):
        if hasattr(imported_prm_modules[prm_m],
                   "export_module_specific_results"):
            imported_prm_modules[prm_m]. \
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

    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT(prm_type)
            FROM inputs_project_prm_zones
            LEFT OUTER JOIN inputs_project_elcc_chars
            USING (project)
            WHERE prm_zone_scenario_id = {}
            AND project_prm_zone_scenario_id = {}
            AND project_elcc_chars_scenario_id = {}
            AND prm_type IS NOT NULL;""".format(
                subscenarios.PRM_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
            )
        ).fetchall()
    ]

    # Get module-specific inputs
    # Load in the required operational modules
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "get_module_specific_inputs_from_database"):
            imported_prm_modules[prm_m]. \
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

    (prm_zone_scenario_id, project_prm_scenario_id,
     project_elcc_chars_scenario_id) = c.execute(
        """SELECT prm_zone_scenario_id, project_prm_zone_scenario_id, 
        project_elcc_chars_scenario_id
        FROM scenarios
        WHERE scenario_id = {};""".format(scenario_id)
    ).fetchone()

    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT(prm_type)
        FROM inputs_project_prm_zones
        LEFT OUTER JOIN inputs_project_elcc_chars
        USING (project)
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}
        AND project_elcc_chars_scenario_id = {}
        AND prm_type IS NOT NULL;""".format(
            prm_zone_scenario_id,
            project_prm_scenario_id,
            project_elcc_chars_scenario_id
        )
    ).fetchall()
    ]

    # Import module-specific results
    # Load in the required operational modules
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "import_module_specific_results_into_database"):
            imported_prm_modules[prm_m]. \
                import_module_specific_results_into_database(
                scenario_id, c, db, results_directory
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
    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT(prm_type)
        FROM inputs_project_prm_zones
        LEFT OUTER JOIN inputs_project_elcc_chars
        USING (project)
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}
        AND project_elcc_chars_scenario_id = {}
        AND prm_type IS NOT NULL;""".format(
                subscenarios.PRM_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
            )
        ).fetchall()
    ]

    # Import module-specific results
    # Load in the required operational modules
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "process_module_specific_results"):
            imported_prm_modules[prm_m]. \
                process_module_specific_results(
                db=db, c=c, subscenarios=subscenarios
            )
        else:
            pass
