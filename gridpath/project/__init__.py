#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The 'project' package contains modules to describe the available
capacity and operational characteristics of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Any

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_dtypes, get_expected_dtypes, validate_values, validate_columns, \
    validate_missing_inputs


def determine_dynamic_inputs(d, scenario_directory, subproblem, stage):
    """
    :param di: the dynamic components class object we'll be adding to
    :param scenario_directory: the base scenario directory
    :param stage: if horizon subproblems exist, the horizon name; NOT USED
    :param stage: if stage subproblems exist, the stage name; NOT USED

    This method adds several project-related 'dynamic components' to the
    Python class object (created in *gridpath.auxiliary.dynamic_components*) we
    use to pass around components that depend on the selected modules and
    the scenario input data.

    First, we get the unique sets of project 'capacity types' and 'operational
    types.' We will use this lists to iterate over the required capacity-type
    and operational-type modules, so that they can add the relevant params,
    sets, variables, etc. to the model, load their data, export their
    results, etc.

    We will also set the keys for the headroom and footroom variable
    dictionaries: the keys are all the projects included in the
    'projects.tab' input file. The values of these dictionaries are
    initially empty lists and will be populated later by each of included
    the reserve (e.g regulation up) modules. E.g. if the user has requested to
    model spinning reserves and project *r* has a value in the column
    associated with the spinning-reserves balancing area, then the name of
    project-level spinning-reserves-provision variable will be added to that
    project's list of variables in the 'headroom_variables' dictionary. For
    downward reserves, the associated variables are added to the
    'footroom_variables' dictionary.
    """

    project_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "projects.tab"),
        sep="\t"
    )

    # From here on, the dynamic components will be further populated by the
    # modules

    # Reserve variables
    # Will be determined based on whether the user has specified the
    # respective reserve module AND based on whether a reserve zone is
    # specified for a project in projects.tab
    # We need to make the dictionaries first; it is the lists for each key
    # that are populated by the modules
    setattr(d, headroom_variables,
            {r: [] for r in project_df.project}
            )
    setattr(d, footroom_variables,
            {r: [] for r in project_df.project}
            )


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`PROJECTS`                                                      |
    |                                                                         |
    | The list of all projects considered in the optimization problem.        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Input Params                                                            |
    +=========================================================================+
    | | :code:`load_zone`                                                     |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`LOAD_ZONES`                                          |
    |                                                                         |
    | This param describes which load zone's load-balance constraint each     |
    | project contributes to.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`capacity_type`                                                 |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`["dr_new", "gen_new_bin", "gen_new_lin",`            |
    | | :code:`"gen_ret_bin", "gen_ret_lin", "gen_spec", "stor_new_bin",`     |
    | | :code:`"stor_new_lin", "stor_spec"]`                                  |
    |                                                                         |
    | This param describes each project's capacity type, which determines how |
    | the available capacity of the project is defined (depending on the      |
    | type, it could be a fixed for each period or a decision variable).      |
    +-------------------------------------------------------------------------+
    | | :code:`operational_type`                                              |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`["dr", "gen_always_on", "gen_commit_bin",`           |
    | | :code:`"gen_commit_cap", "gen_commit_lin", "gen_hydro",`              |
    | | :code:`"gen_hydro_must_take", "gen_must_run", "gen_simple",`          |
    | | :code:`"gen_var", "gen_var_must_take", "stor"]`                       |
    |                                                                         |
    | This param describes each project's operational type, which determines  |
    | how the project operates, e.g. whether it is fuel-based dispatchable    |
    | generator, a baseload project, a variable generation project, a storage |
    | project, etc.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`availability_type`                                             |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`["binary", "continuous", "exogenous"]`               |
    |                                                                         |
    | This param describes each project's availability type, which determines |
    | how the project availability is determined (exogenously or              |
    | endogenously).                                                          |
    +-------------------------------------------------------------------------+
    | | :code:`balancing_type_project`                                        |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`BLN_TYPES`                                           |
    |                                                                         |
    | This param describes each project's balancing type, which determines    |
    | how timepoints are grouped in horizons for that project. See            |
    | :code:`horizons` module for more info.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`technology`                                                    |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`Any`                                                 |
    | | *Default*: :code:`unspecified`                                        |
    |                                                                         |
    | The technology for each project, which is only used for aggregation     |
    | purposes in the results.                                                |
    +-------------------------------------------------------------------------+

    TODO: all projects have VOM for now; is that what makes the most sense?
    TODO: considering technology is only used on the results side, should we
     keep it here?
    """

    # Sets
    ###########################################################################

    m.PROJECTS = Set()

    # Input Params
    ###########################################################################

    m.load_zone = Param(m.PROJECTS, within=m.LOAD_ZONES)
    m.capacity_type = Param(
        m.PROJECTS,
        within=["dr_new", "gen_new_bin", "gen_new_lin", "gen_ret_bin",
                "gen_ret_lin", "gen_spec", "stor_new_bin", "stor_new_lin",
                "stor_spec"]
    )
    m.operational_type = Param(
        m.PROJECTS,
        within=["dr", "gen_always_on", "gen_commit_bin", "gen_commit_cap",
                "gen_commit_lin", "gen_hydro", "gen_hydro_must_take",
                "gen_must_run", "gen_simple", "gen_var",
                "gen_var_must_take", "stor"]
    )
    m.availability_type = Param(
        m.PROJECTS,
        within=["binary", "continuous", "exogenous"]
    )
    m.balancing_type_project = Param(m.PROJECTS, within=m.BLN_TYPES)
    m.technology = Param(m.PROJECTS, within=Any, default="unspecified")


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "projects.tab"),
        index=m.PROJECTS,
        select=("project", "load_zone", "capacity_type",
                "availability_type", "operational_type",
                "balancing_type_project"),
        param=(m.load_zone, m.capacity_type, m.availability_type,
               m.operational_type, m.balancing_type_project)
    )

    # Technology column is optional (default param value is 'unspecified')
    header = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    if "technology" in header:
        data_portal.load(
            filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                                  "inputs", "projects.tab"),
            select=("project", "technology"),
            param=m.technology
        )


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    projects = c.execute(
        """SELECT project, capacity_type, availability_type, operational_type, 
        balancing_type_project, technology, load_zone
        FROM
        -- Get only the subset of projects in the portfolio with their 
        -- capacity types based on the project_portfolio_scenario_id 
        (SELECT project, capacity_type
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}) as portfolio_tbl
        -- Get the load_zones for these projects depending on the
        -- project_load_zone_scenario_id
        LEFT OUTER JOIN
        (SELECT project, load_zone
        FROM inputs_project_load_zones
        WHERE project_load_zone_scenario_id = {}) as prj_load_zones
        USING (project)
        LEFT OUTER JOIN
        -- Get the availability types for these projects depending on the
        -- project_availability_scenario_id
        (SELECT project, availability_type
        FROM inputs_project_availability
        WHERE project_availability_scenario_id = {}) as prj_av_types
        USING (project)
        LEFT OUTER JOIN
        -- Get the operational type, balancing_type, technology, 
        -- and variable cost for these projects depending ont the 
        -- project_operational_chars_scenario_id
        (SELECT project, operational_type, balancing_type_project, technology
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        ;""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_LOAD_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID
        )
    )

    return projects


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    projects.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    projects = get_inputs_from_database(subscenarios, subproblem, stage, conn)

    # TODO: make get_inputs_from_database return dataframe and simplify writing
    #   of the tab files. If going this route, would need to make sure database
    #   columns and tab file column names are the same everywhere
    #   projects.fillna(".", inplace=True)
    #   filename = os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab")
    #   projects.to_csv(filename, sep="\t", mode="w", newline="")

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "w",
              newline="") as projects_tab_file:
        writer = csv.writer(projects_tab_file,
                            delimiter="\t",
                            lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "capacity_type", "availability_type",
             "operational_type", "balancing_type_project", "technology",
             "load_zone"]
        )

        for row in projects:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


# Validation
###############################################################################

def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()

    # Get the project inputs
    projects = get_inputs_from_database(subscenarios, subproblem, stage, conn)

    # Convert input data into pandas DataFrame
    df = cursor_to_df(projects)

    # Check data types:
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_portfolios",
               "inputs_project_availability",
               "inputs_project_load_zones",
               "inputs_project_operational_chars"]
    )

    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars, inputs_project_portfolios",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)

    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_values(df, valid_numeric_columns, min=0)
    )

    # Check that we're not combining incompatible cap-types and op-types
    cols = ["capacity_type", "operational_type"]
    invalid_combos = c.execute(
        """
        SELECT {} FROM mod_capacity_and_operational_type_invalid_combos
        """.format(",".join(cols))
    ).fetchall()

    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars, inputs_project_portfolios",
        severity="High",
        errors=validate_columns(df, cols, invalids=invalid_combos)
    )

    # Check that capacity type is valid
    # Note: foreign key already ensures this!
    valid_cap_types = c.execute(
        """SELECT capacity_type from mod_capacity_types"""
    ).fetchall()
    valid_cap_types = [v[0] for v in valid_cap_types]

    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_portfolios",
        severity="High",
        errors=validate_columns(df, "capacity_type", valids=valid_cap_types)
    )

    # Check that operational type is valid
    # Note: foreign key already ensures this!
    valid_op_types = c.execute(
        """SELECT operational_type from mod_operational_types"""
    ).fetchall()
    valid_op_types = [v[0] for v in valid_op_types]

    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_portfolios",
        severity="High",
        errors=validate_columns(df, "operational_type", valids=valid_op_types)
    )

    # Check that all portfolio projects are present in the availability inputs
    msg = "All projects in the portfolio should have an availability type " \
          "specified in the inputs_project_availability table."
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_availability",
        severity="High",
        errors=validate_missing_inputs(df, "availability_type", msg=msg)
    )

    # Check that all portfolio projects are present in the opchar inputs
    msg = "All projects in the portfolio should have an operational type " \
          "and balancing type specified in the " \
          "inputs_project_operational_chars table."
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_missing_inputs(df,
                                       ["operational_type",
                                        "balancing_type_project"],
                                       msg=msg)
    )

    # Check that all portfolio projects are present in the load zone inputs
    msg = "All projects in the portfolio should have a load zone " \
          "specified in the inputs_project_load_zones table."
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_load_zones",
        severity="High",
        errors=validate_missing_inputs(df, "load_zone", msg=msg)
    )


