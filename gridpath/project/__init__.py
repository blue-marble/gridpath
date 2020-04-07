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
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import required_capacity_modules, \
    required_availability_modules, required_operational_modules, \
    headroom_variables, footroom_variables
from gridpath.auxiliary.auxiliary import check_dtypes, get_expected_dtypes, \
    check_column_sign_positive, write_validation_to_database, check_prj_column


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    :param d: the dynamic components class object we'll be adding to
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
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "projects.tab"),
        sep="\t"
    )

    # Required modules are the unique set of generator capacity types
    # This list will be used to know which capacity type modules to load
    setattr(d, required_capacity_modules,
            project_df.capacity_type.unique()
            )

    # Required availability types
    setattr(d, required_availability_modules,
            project_df.availability_type.unique()
            )

    # Required operational modules
    # Will be determined based on operational_types specified in the data
    # (in projects.tab)
    setattr(d, required_operational_modules,
            project_df.operational_type.unique()
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


def add_model_components(m, d):
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
    |                                                                         |
    | This param describes each project's capacity type, which determines how |
    | the available capacity of the project is defined (depending on the      |
    | type, it could be a fixed for each period or a decision variable).      |
    +-------------------------------------------------------------------------+
    | | :code:`operational_type`                                              |
    | | *Defined over*: :code:`PROJECTS`                                      |
    |                                                                         |
    | This param describes each project's operational type, which determines  |
    | how the project operates, e.g. whether it is fuel-based dispatchable    |
    | generator, a baseload project, a variable generation project, a storage |
    | project, etc.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`availability_type`                                             |
    | | *Defined over*: :code:`PROJECTS`                                      |
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
    | | :code:`variable_om_cost_per_mwh`                                      |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The variable operations and maintenance (O&M) cost for each project in  |
    | $ per MWh.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`technology`                                                    |
    | | *Defined over*: :code:`PROJECTS`                                      |
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
    m.capacity_type = Param(m.PROJECTS)
    m.operational_type = Param(m.PROJECTS)
    m.availability_type = Param(m.PROJECTS)
    m.balancing_type_project = Param(m.PROJECTS, within=m.BLN_TYPES)
    m.variable_om_cost_per_mwh = Param(m.PROJECTS, within=NonNegativeReals)
    m.technology = Param(m.PROJECTS, default="unspecified")


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "projects.tab"),
        index=m.PROJECTS,
        select=("project", "load_zone", "capacity_type",
                "availability_type", "operational_type",
                "variable_om_cost_per_mwh",
                "balancing_type_project"),
        param=(m.load_zone, m.capacity_type, m.availability_type,
               m.operational_type, m.variable_om_cost_per_mwh,
               m.balancing_type_project)
    )

    # Technology column is optional (default param value is 'unspecified')
    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    if "technology" in header:
        data_portal.load(
            filename=os.path.join(scenario_directory, subproblem, stage,
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
    c = conn.cursor()

    # TODO: for now, will require project_availability_scenario_id to be
    #  defined; however, we should break down this query and have the
    #  subtype modules write to projects.tab instead of getting everything
    #  in one go here; this will help in a situation when, for example,
    #  we don't have startup costs, so we don't need to have the associated
    #  columns in projects.tab
    projects = c.execute(
        """SELECT project, capacity_type, availability_type, operational_type, 
        balancing_type_project, technology,
        load_zone, fuel, variable_cost_per_mwh,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        ramp_up_when_on_rate,
        ramp_down_when_on_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, maximum_duration_hours,
        last_commitment_stage
        FROM inputs_project_portfolios
        LEFT OUTER JOIN
        (SELECT project, load_zone
        FROM inputs_project_load_zones
        WHERE project_load_zone_scenario_id = {}) as prj_load_zones
        USING (project)
        LEFT OUTER JOIN
        (SELECT project, availability_type
        FROM inputs_project_availability_types
        WHERE project_availability_scenario_id = {}) as prj_av_types
        USING (project)
        LEFT OUTER JOIN
        (SELECT project, operational_type, balancing_type_project, technology,
        fuel, variable_cost_per_mwh,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        ramp_up_when_on_rate,
        ramp_down_when_on_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, maximum_duration_hours,
        last_commitment_stage
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}""".format(
            subscenarios.PROJECT_LOAD_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    # TODO: change all these queries to return dataframes directly using pandas
    #   functions. Then we can also write out the results easier using pandas
    #   to.csv functionality
    # projects_df = pd.read_sql_query(query, conn)
    # return projects_df

    return projects


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    projects.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    projects = get_inputs_from_database(subscenarios, subproblem, stage, conn)

    # TODO: decide how to deal with projects.tab -- currently, a large table
    #  is created with NULL values for projects that don't have certain
    #  params, so we can just get it all here without having to iterate
    #  through the modules that actually need these params
    #  This file could also potentially be split up into smaller files with
    #  just a subset of the params, which would mean that the submodules
    #  won't have to parse the large file

    # TODO: make get_inputs_from_database return dataframe and simplify writing
    #   of the tab files. If going this route, would need to make sure database
    #   columns and tab file column names are the same everywhere
    #   projects.fillna(".", inplace=True)
    #   filename = os.path.join(inputs_directory, "projects.tab")
    #   projects.to_csv(filename, sep="\t", mode="w", newline="")

    with open(os.path.join(inputs_directory, "projects.tab"), "w",
              newline="") as projects_tab_file:
        writer = csv.writer(projects_tab_file,
                            delimiter="\t",
                            lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "capacity_type", "availability_type",
             "operational_type", "balancing_type_project", "technology",
             "load_zone", "fuel", "variable_om_cost_per_mwh",
             "min_stable_level_fraction", "unit_size_mw",
             "startup_cost_per_mw", "shutdown_cost_per_mw",
             "startup_fuel_mmbtu_per_mw",
             "startup_plus_ramp_up_rate",
             "shutdown_plus_ramp_down_rate",
             "ramp_up_when_on_rate",
             "ramp_down_when_on_rate",
             "min_up_time_hours", "min_down_time_hours",
             "charging_efficiency", "discharging_efficiency",
             "minimum_duration_hours", "maximum_duration_hours",
             "last_commitment_stage"
             ]
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
    validation_results = []

    # Get the project inputs
    projects = get_inputs_from_database(subscenarios, subproblem, stage, conn)

    # Convert input data into pandas DataFrame
    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Check data types:
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_portfolios",
               "inputs_project_availability_types",
               "inputs_project_load_zones",
               "inputs_project_operational_chars"]
    )

    dtype_errors, error_columns = check_dtypes(df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS, PROJECT_PORTFOLIO",
             "inputs_project_operational_chars, inputs_project_portfolios",
             "High",
             "Invalid data type",
             error
             )
        )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    sign_errors = check_column_sign_positive(df, valid_numeric_columns)
    for error in sign_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "High",
             "Invalid numeric sign",
             error
             )
        )

    # Check 0 < min stable fraction <= 1
    if "min_stable_level" not in error_columns:
        validation_errors = validate_min_stable_level(df)
        for error in validation_errors:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 subproblem,
                 stage,
                 __name__,
                 "PROJECT_OPERATIONAL_CHARS",
                 "inputs_project_operational_chars",
                 "High",
                 "Invalid min_stable_level",
                 error
                 )
            )

    # Check that we're not combining incompatible cap-types and op-types
    invalid_combos = c.execute(
        """SELECT capacity_type, operational_type 
        FROM mod_capacity_and_operational_type_invalid_combos"""
    ).fetchall()
    validation_errors = validate_op_cap_combos(df, invalid_combos)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS, PROJECT_PORTFOLIO",
             "inputs_project_operational_chars, inputs_project_portfolios",
             "High",
             "Invalid combination of capacity type and operational type",
             error
             )
        )

    # Check that capacity type is valid
    # Note: foreign key already ensures this!
    valid_cap_types = c.execute(
        """SELECT capacity_type from mod_capacity_types"""
    ).fetchall()
    valid_cap_types = [v[0] for v in valid_cap_types]
    validation_errors = check_prj_column(df, "capacity_type", valid_cap_types)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_PORTFOLIO",
             "inputs_project_portfolios",
             "High",
             "Invalid capacity type",
             error
             )
        )

    # Check that operational type is valid
    # Note: foreign key already ensures this!
    valid_op_types = c.execute(
        """SELECT operational_type from mod_operational_types"""
    ).fetchall()
    valid_op_types = [v[0] for v in valid_op_types]
    validation_errors = check_prj_column(df, "operational_type", valid_op_types)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "High",
             "Invalid operational type",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def validate_min_stable_level(df):
    """
    Check 0 < min stable fraction <= 1
    :param df:
    :return:
    """
    results = []

    invalids = ((df["min_stable_level"] <= 0) |
                (df["min_stable_level"] > 1))
    if invalids.any():
        bad_projects = df["project"][invalids].values
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': expected 0 < min_stable_level <= 1"
            .format(print_bad_projects)
        )

    return results


def validate_op_cap_combos(df, invalid_combos):
    """
    Check that there's no mixing of incompatible capacity and operational types
    :param df:
    :param invalid_combos:
    :return:
    """
    results = []
    for combo in invalid_combos:
        bad_combos = ((df["capacity_type"] == combo[0]) &
                      (df["operational_type"] == combo[1]))
        if bad_combos.any():
            bad_projects = df['project'][bad_combos].values
            print_bad_projects = ", ".join(bad_projects)
            results.append(
                "Project(s) '{}': '{}' and '{}'"
                .format(print_bad_projects, combo[0], combo[1])
            )

    return results
