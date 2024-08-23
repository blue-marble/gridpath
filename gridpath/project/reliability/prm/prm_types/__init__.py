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
Describe ELCC-eligibility constraints on infrastructure.
"""

import os.path
import pandas as pd
from pyomo.environ import Expression

from gridpath.project.reliability.prm.common_functions import load_prm_type_modules


# TODO: rename to deliverability types; the PRM types are really 'simple'
#  and 'elcc surface'
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

    :param m:
    :param d:
    :return:
    """
    # Import needed PRM modules
    project_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=["project", "prm_type"],
    )
    required_prm_modules = [
        prm_type for prm_type in project_df.prm_type.unique() if prm_type != "."
    ]

    imported_prm_modules = load_prm_type_modules(required_prm_modules)

    # Add any components specific to the PRM modules
    for prm_m in required_prm_modules:
        imp_prm_m = imported_prm_modules[prm_m]
        if hasattr(imp_prm_m, "add_model_components"):
            imp_prm_m.add_model_components(
                m,
                d,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )

    # For each PRM project, get the ELCC-eligible capacity
    def elcc_eligible_capacity_rule(mod, g, p):
        prm_type = mod.prm_type[g]
        return imported_prm_modules[prm_type].elcc_eligible_capacity_rule(mod, g, p)

    m.ELCC_Eligible_Capacity_MW = Expression(
        m.PRM_PRJ_OPR_PRDS, rule=elcc_eligible_capacity_rule
    )


# TODO: refactor importing prm modules as it's used several places in this
#  module
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

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    project_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=["project", "prm_type"],
    )
    required_prm_modules = [
        prm_type for prm_type in project_df.prm_type.unique() if prm_type != "."
    ]

    imported_prm_modules = load_prm_type_modules(required_prm_modules)

    for prm_m in required_prm_modules:
        if hasattr(imported_prm_modules[prm_m], "load_model_data"):
            imported_prm_modules[prm_m].load_model_data(
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


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
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
    project_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=["project", "prm_type"],
    )
    required_prm_modules = [
        prm_type for prm_type in project_df.prm_type.unique() if prm_type != "."
    ]

    imported_prm_modules = load_prm_type_modules(required_prm_modules)

    for prm_m in required_prm_modules:
        if hasattr(imported_prm_modules[prm_m], "export_results"):
            imported_prm_modules[prm_m].export_results(
                m,
                d,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )


def get_required_prm_type_modules(
    c,
    project_portfolio_scenario_id,
    project_prm_zone_scenario_id,
    project_elcc_chars_scenario_id,
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
        p[0]
        for p in c.execute(
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
                project_elcc_chars_scenario_id,
            )
        ).fetchall()
    ]

    return required_prm_type_modules


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
        project_portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        project_prm_zone_scenario_id=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
        project_elcc_chars_scenario_id=subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
    )
    imported_prm_modules = load_prm_type_modules(required_prm_type_modules)

    # Validate module-specific inputs
    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m], "validate_inputs"):
            imported_prm_modules[prm_m].validate_inputs(
                scenario_id, subscenarios, subproblem, stage, conn
            )


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
    Get inputs from database and write out the model input .tab files.
    :param scenario_directory: string, the scenario directory
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
        project_portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        project_prm_zone_scenario_id=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
        project_elcc_chars_scenario_id=subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
    )
    imported_prm_modules = load_prm_type_modules(required_prm_type_modules)

    # Write module-specific inputs
    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m], "write_model_inputs"):
            imported_prm_modules[prm_m].write_model_inputs(
                scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
            )


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

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """

    (
        project_portfolio_scenario_id,
        project_prm_zone_scenario_id,
        project_elcc_chars_scenario_id,
    ) = c.execute(
        """
        SELECT project_portfolio_scenario_id, project_prm_zone_scenario_id, 
        project_elcc_chars_scenario_id
        FROM scenarios
        WHERE scenario_id = {}
        """.format(
            scenario_id
        )
    ).fetchone()

    # Required modules are the unique set of generator PRM types in
    # the scenario's portfolio
    # This list will be used to know which PRM type modules to load
    required_prm_type_modules = get_required_prm_type_modules(
        c=c,
        project_portfolio_scenario_id=project_portfolio_scenario_id,
        project_prm_zone_scenario_id=project_prm_zone_scenario_id,
        project_elcc_chars_scenario_id=project_elcc_chars_scenario_id,
    )

    # Import module-specific results
    # Load in the required operational modules
    imported_prm_modules = load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m], "import_results_into_database"):
            imported_prm_modules[prm_m].import_results_into_database(
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
            )


def process_results(db, c, scenario_id, subscenarios, quiet):
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
        project_portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        project_prm_zone_scenario_id=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
        project_elcc_chars_scenario_id=subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
    )

    # Import module-specific results
    # Load in the required operational modules
    imported_prm_modules = load_prm_type_modules(required_prm_type_modules)

    for prm_m in required_prm_type_modules:
        if hasattr(imported_prm_modules[prm_m], "process_model_results"):
            imported_prm_modules[prm_m].process_model_results(
                db=db,
                c=c,
                scenario_id=scenario_id,
                subscenarios=subscenarios,
                quiet=quiet,
            )
