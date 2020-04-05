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


# TODO: rename to deliverability types; the PRM types are really 'simple'
#  and 'elcc surface'
def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """

    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    project_dynamic_data = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "prm_type"]
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
        m.PRM_PRJ_OPR_PRDS,
        rule=elcc_eligible_capacity_rule
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
    imported_prm_modules = \
        load_prm_type_modules(getattr(d, required_prm_modules))
    for prm_m in getattr(d, required_prm_modules):
        if hasattr(imported_prm_modules[prm_m],
                   "load_module_specific_data"):
            imported_prm_modules[prm_m].load_module_specific_data(
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
    imported_prm_modules = \
        load_prm_type_modules(getattr(d, required_prm_modules))
    for prm_m in getattr(d, required_prm_modules):
        if hasattr(imported_prm_modules[prm_m],
                   "export_module_specific_results"):
            imported_prm_modules[prm_m]. \
                export_module_specific_results(
                m, d, scenario_directory, subproblem, stage,
            )
        else:
            pass


def get_required_prm_type_modules(
    c, project_portfolio_scenario_id, project_prm_zone_scenario_id,
    project_elcc_chars_scenario_id
):
    """
    :param c:
    :param project_portfolio_scenario_id:
    :param project_prm_zone_scenario_id:
    :param project_elcc_chars_scenario_id:
    :return:

    Get the required prm  type submodules based on the user-specified database
    inputs.
    """
    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT(prm_type)
            FROM 
            (SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}) as portfolio_tbl
            LEFT OUTER JOIN 
            (SELECT project
            FROM inputs_project_prm_zones
            WHERE project_prm_zone_scenario_id = {}) as prm_proj_tbl
            LEFT OUTER JOIN 
            (SELECT project, prm_type
            FROM inputs_project_elcc_chars
            WHERE project_elcc_chars_scenario_id = {}) as prm_type_tbl
            USING (project)
            WHERE prm_type IS NOT NULL;""".format(
                project_portfolio_scenario_id,
                project_prm_zone_scenario_id,
                project_elcc_chars_scenario_id
            )
        ).fetchall()
    ]

    return required_prm_type_modules


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required prm type modules
    c = conn.cursor()
    required_prm_type_modules = get_required_prm_type_modules(
        c=c,
        project_portfolio_scenario_id
        =subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        project_prm_zone_scenario_id=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
        project_elcc_chars_scenario_id
        =subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
    )
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    # Validate module-specific inputs
    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "validate_module_specific_inputs"):
            imported_prm_modules[prm_m]. \
                validate_module_specific_inputs(
                    subscenarios, subproblem, stage, conn)
        else:
            pass


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input .tab files.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # Load in the required prm type modules
    required_prm_type_modules = get_required_prm_type_modules(
        c=c,
        project_portfolio_scenario_id
        =subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        project_prm_zone_scenario_id=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
        project_elcc_chars_scenario_id
        =subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
    )
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    # Write module-specific inputs
    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "write_module_specific_model_inputs"):
            imported_prm_modules[prm_m]. \
                write_module_specific_model_inputs(
                    inputs_directory, subscenarios, subproblem, stage, conn)
        else:
            pass


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """

    (project_portfolio_scenario_id, project_prm_zone_scenario_id,
     project_elcc_chars_scenario_id) = c.execute("""
        SELECT project_portfolio_scenario_id, project_prm_zone_scenario_id, 
        project_elcc_chars_scenario_id
        FROM scenarios
        WHERE scenario_id = {}
        """.format(scenario_id)
    ).fetchone()

    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = get_required_prm_type_modules(
        c=c,
        project_portfolio_scenario_id=project_portfolio_scenario_id,
        project_prm_zone_scenario_id=project_prm_zone_scenario_id,
        project_elcc_chars_scenario_id=project_elcc_chars_scenario_id
    )

    # Import module-specific results
    # Load in the required operational modules
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "import_module_specific_results_into_database"):
            imported_prm_modules[prm_m]. \
                import_module_specific_results_into_database(
                scenario_id, subproblem, stage, c, db, results_directory, quiet
            )
        else:
            pass


def process_results(db, c, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = get_required_prm_type_modules(
        c=c,
        project_portfolio_scenario_id
        =subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        project_prm_zone_scenario_id=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
        project_elcc_chars_scenario_id
        =subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
    )

    # Import module-specific results
    # Load in the required operational modules
    imported_prm_modules = \
        load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m],
                   "process_module_specific_results"):
            imported_prm_modules[prm_m]. \
                process_module_specific_results(
                db=db, c=c, subscenarios=subscenarios, quiet=quiet
            )
        else:
            pass
