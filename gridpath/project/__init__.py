# Copyright 2016-2020 Blue Marble Analytics LLC.
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
The 'project' package contains modules to describe the available
capacity and operational characteristics of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Any, value

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_dtypes,
    get_expected_dtypes,
    validate_values,
    validate_columns,
    validate_missing_inputs,
)

PROJECT_PERIOD_DF = "project_period_df"
PROJECT_TIMEPOINT_DF = "project_timepoint_df"


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
    | | :code:`"stor_new_lin", "stor_spec", "fuel_prod_spec", "fuel_prod_new]`|
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
    | | :code:`"gen_var", "gen_var_must_take", "stor", "fuel_prod", "dac",    |
    | | :code:`"flex_load"]`                                                  |
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
        within=[
            "dr_new",
            "gen_new_bin",
            "gen_new_lin",
            "gen_ret_bin",
            "gen_ret_lin",
            "gen_spec",
            "stor_new_bin",
            "stor_new_lin",
            "stor_spec",
            "gen_stor_hyb_spec",
            "fuel_prod_spec",
            "fuel_prod_new",
        ],
    )
    m.operational_type = Param(
        m.PROJECTS,
        within=[
            "dr",
            "gen_always_on",
            "gen_commit_bin",
            "gen_commit_cap",
            "gen_commit_lin",
            "gen_hydro",
            "gen_hydro_must_take",
            "gen_must_run",
            "gen_simple",
            "gen_var",
            "gen_var_must_take",
            "stor",
            "gen_var_stor_hyb",
            "fuel_prod",
            "dac",
            "flex_load",
        ],
    )
    m.availability_type = Param(
        m.PROJECTS, within=["binary", "continuous", "exogenous"]
    )
    m.balancing_type_project = Param(m.PROJECTS, within=m.BLN_TYPES)
    m.technology = Param(m.PROJECTS, within=Any, default="unspecified")


# Input-Output
###############################################################################


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """ """
    data_portal.load(
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        index=m.PROJECTS,
        select=(
            "project",
            "load_zone",
            "capacity_type",
            "availability_type",
            "operational_type",
            "balancing_type_project",
        ),
        param=(
            m.load_zone,
            m.capacity_type,
            m.availability_type,
            m.operational_type,
            m.balancing_type_project,
        ),
    )

    # Technology column is optional (default param value is 'unspecified')
    header = pd.read_csv(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        sep="\t",
        header=None,
        nrows=1,
    ).values[0]

    if "technology" in header:
        data_portal.load(
            filename=os.path.join(
                scenario_directory,
                str(subproblem),
                str(stage),
                "inputs",
                "projects.tab",
            ),
            select=("project", "technology"),
            param=m.technology,
        )


# Input-Output
###############################################################################


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

    # First create the results dataframes
    # Other modules will update these dataframe with actual results
    # The results dataframes are by index

    # Project-period DF
    project_period_df = pd.DataFrame(
        columns=[
            "project",
            "period",
            "capacity_type",
            "availability_type",
            "operational_type",
            "technology",
            "load_zone",
        ],
        data=[
            [
                prj,
                prd,
                m.capacity_type[prj],
                m.availability_type[prj],
                m.operational_type[prj],
                m.technology[prj],
                m.load_zone[prj],
            ]
            for (prj, prd) in set(m.PRJ_OPR_PRDS | m.PRJ_FIN_PRDS)
        ],
    ).set_index(["project", "period"])

    project_period_df.sort_index(inplace=True)

    # Add the dataframe to the dynamic components to pass to other modules
    setattr(d, PROJECT_PERIOD_DF, project_period_df)

    # Project-timepoint DF
    project_timepoint_df = pd.DataFrame(
        columns=[
            "project",
            "timepoint",
            "period",
            "horizon",
            "capacity_type",
            "availability_type",
            "operational_type",
            "balancing_type",
            "timepoint_weight",
            "number_of_hours_in_timepoint",
            "load_zone",
            "technology",
            "capacity_mw",
        ],
        data=[
            [
                prj,
                tmp,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[prj]],
                m.capacity_type[prj],
                m.availability_type[prj],
                m.operational_type[prj],
                m.balancing_type_project[prj],
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[prj],
                m.technology[prj],
                value(m.Capacity_MW[prj, m.period[tmp]]),
            ]
            for (prj, tmp) in m.PRJ_OPR_TMPS
        ],
    ).set_index(["project", "timepoint"])

    project_timepoint_df.sort_index(inplace=True)

    # Add the dataframe to the dynamic components to pass to other modules
    setattr(d, PROJECT_TIMEPOINT_DF, project_timepoint_df)


# Database
###############################################################################


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
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
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
        )
    )

    return projects


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
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

    projects = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # TODO: make get_inputs_from_database return dataframe and simplify writing
    #   of the tab files. If going this route, would need to make sure database
    #   columns and tab file column names are the same everywhere
    #   projects.fillna(".", inplace=True)
    #   filename = os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab")
    #   projects.to_csv(filename, sep="\t", mode="w", newline="")

    with open(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        "w",
        newline="",
    ) as projects_tab_file:
        writer = csv.writer(projects_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "project",
                "capacity_type",
                "availability_type",
                "operational_type",
                "balancing_type_project",
                "technology",
                "load_zone",
            ]
        )

        for row in projects:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


# Validation
###############################################################################


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
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
    projects = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Convert input data into pandas DataFrame
    df = cursor_to_df(projects)

    # Check data types:
    expected_dtypes = get_expected_dtypes(
        conn,
        [
            "inputs_project_portfolios",
            "inputs_project_availability",
            "inputs_project_load_zones",
            "inputs_project_operational_chars",
        ],
    )

    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars, inputs_project_portfolios",
        severity="High",
        errors=dtype_errors,
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)

    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_values(df, valid_numeric_columns, min=0),
    )

    # Check that we're not combining incompatible cap-types and op-types
    cols = ["capacity_type", "operational_type"]
    invalid_combos = c.execute(
        """
        SELECT {} FROM mod_capacity_and_operational_type_invalid_combos
        """.format(
            ",".join(cols)
        )
    ).fetchall()

    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars, inputs_project_portfolios",
        severity="High",
        errors=validate_columns(df, cols, invalids=invalid_combos),
    )

    # Check that capacity type is valid
    # Note: foreign key already ensures this!
    valid_cap_types = c.execute(
        """SELECT capacity_type from mod_capacity_types"""
    ).fetchall()
    valid_cap_types = [v[0] for v in valid_cap_types]

    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_portfolios",
        severity="High",
        errors=validate_columns(df, "capacity_type", valids=valid_cap_types),
    )

    # Check that operational type is valid
    # Note: foreign key already ensures this!
    valid_op_types = c.execute(
        """SELECT operational_type from mod_operational_types"""
    ).fetchall()
    valid_op_types = [v[0] for v in valid_op_types]

    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_portfolios",
        severity="High",
        errors=validate_columns(df, "operational_type", valids=valid_op_types),
    )

    # Check that all portfolio projects are present in the availability inputs
    msg = (
        "All projects in the portfolio should have an availability type "
        "specified in the inputs_project_availability table."
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_availability",
        severity="High",
        errors=validate_missing_inputs(df, "availability_type", msg=msg),
    )

    # Check that all portfolio projects are present in the opchar inputs
    msg = (
        "All projects in the portfolio should have an operational type "
        "and balancing type specified in the "
        "inputs_project_operational_chars table."
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_missing_inputs(
            df, ["operational_type", "balancing_type_project"], msg=msg
        ),
    )

    # Check that all portfolio projects are present in the load zone inputs
    msg = (
        "All projects in the portfolio should have a load zone "
        "specified in the inputs_project_load_zones table."
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_load_zones",
        severity="High",
        errors=validate_missing_inputs(df, "load_zone", msg=msg),
    )
