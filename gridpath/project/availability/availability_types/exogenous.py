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
For each project assigned this *availability type*, the user may specify an
(un)availability schedule, i.e. a capacity derate of 0 to 1 for each
timepoint in which the project may be operated. If fully derated in a given
timepoint, the available project capacity will be 0 in that timepoint and all
operational decision variables will therefore also be constrained to 0 in the
optimization.

"""

import csv
import os.path
from pyomo.environ import Param, Set, PercentFraction

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import write_validation_to_database, \
    get_expected_dtypes, validate_dtypes, validate_values, \
    validate_missing_inputs
from gridpath.project.common_functions import determine_project_subset


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`AVL_EXOG`                                                      |
    |                                                                         |
    | The set of projects of the :code:`exogenous` availability type.         |
    +-------------------------------------------------------------------------+
    | | :code:`AVL_EXOG_OPR_TMPS`                                             |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`exogenous`              |
    | availability type and their operational timepoints.                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`avl_exog_derate`                                               |
    | | *Defined over*: :code:`AVL_EXOG_OPR_TMPS`                             |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The pre-specified availability derate (e.g. for maintenance/planned     |
    | outages). Defaults to 1 if not specified.                               |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.AVL_EXOG = Set(within=m.PROJECTS)

    # TODO: factor out this lambda rule, as it is used in all operational type
    #  modules and availability type modules
    m.AVL_EXOG_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: list(
            set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
                if g in mod.AVL_EXOG)
        )
    )

    # Required Params
    ###########################################################################

    m.avl_exog_derate = Param(
        m.AVL_EXOG_OPR_TMPS,
        within=PercentFraction,
        default=1
    )


# Availability Type Methods
###############################################################################

def availability_derate_rule(mod, g, tmp):
    """
    """
    return mod.avl_exog_derate[g, tmp]


# Input-Output
###############################################################################

def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage
):
    """
    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Figure out which projects have this availability type
    project_subset = determine_project_subset(
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage, column="availability_type",
        type="exogenous"
    )

    data_portal.data()["AVL_EXOG"] = {None: project_subset}

    # Availability derates
    # Get any derates from the project_availability.tab file if it exists;
    # if it does not exist, all projects will get 1 as a derate; if it does
    # exist but projects are not specified in it, they will also get 1
    # assigned as their derate
    # The test examples do not currently have a
    # project_availability_exogenous.tab, but use the default instead
    availability_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "project_availability_exogenous.tab"
    )

    if os.path.exists(availability_file):
        data_portal.load(
            filename=availability_file,
            param=m.avl_exog_derate
        )
    else:
        pass


# Database
###############################################################################

def get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage

    sql = """
        SELECT project, timepoint, availability_derate
        -- Select only projects, periods, timepoints from the relevant 
        -- portfolio, relevant opchar scenario id, operational type, 
        -- and temporal scenario id
        FROM 
            (SELECT project, stage_id, timepoint
            FROM project_operational_timepoints
            WHERE project_portfolio_scenario_id = {}
            AND project_operational_chars_scenario_id = {}
            AND temporal_scenario_id = {}
            AND (project_specified_capacity_scenario_id = {}
                 OR project_new_cost_scenario_id = {})
            AND subproblem_id = {}
            AND stage_id = {}
            ) as projects_periods_timepoints_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_availability_scenario_id and have 'exogenous' as 
        -- their availability type and a non-null 
        -- exogenous_availability_scenario_id, i.e. they have 
        -- timepoint-level availability inputs in the 
        -- inputs_project_availability_exogenous table
        INNER JOIN (
            SELECT project, exogenous_availability_scenario_id
            FROM inputs_project_availability
            WHERE project_availability_scenario_id = {}
            AND availability_type = '{}'
            AND exogenous_availability_scenario_id IS NOT NULL
            ) AS avail_char
        USING (project)
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective availability_derate (and no others) from 
        -- inputs_project_availability_exogenous
        left outer JOIN
            inputs_project_availability_exogenous
        USING (exogenous_availability_scenario_id, project, stage_id, 
        timepoint)
        ;
    """.format(
        subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
        subscenarios.TEMPORAL_SCENARIO_ID,
        subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
        subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
        subproblem,
        stage,
        subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID,
        "exogenous",
    )

    c = conn.cursor()
    availabilities = c.execute(sql)

    return availabilities


def write_model_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param scenario_directory:
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    availabilities = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    ).fetchall()

    if availabilities:
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "project_availability_exogenous.tab"),
                  "w", newline="") as availability_tab_file:
            writer = csv.writer(availability_tab_file, delimiter="\t", lineterminator="\n")

            writer.writerow(["project", "timepoint", "availability_derate"])

            for row in availabilities:
                row = ["." if i is None else i for i in row]
                writer.writerow(row)


# Validation
###############################################################################

def validate_model_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    availabilities = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    df = cursor_to_df(availabilities)
    idx_cols = ["project", "timepoint"]
    value_cols = ["availability_derate"]

    # Check data types availability
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_availability",
               "inputs_project_availability_exogenous"])
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_availability_exogenous",
        severity="High",
        errors=dtype_errors
    )

    # Check for missing inputs
    msg = "If not specified, availability is assumed to be 100%. If you " \
          "don't want to specify any availability derates, simply leave the " \
          "exogenous_availability_scenario_id empty and this message will " \
          "disappear."
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_availability_exogenous",
        severity="Low",
        errors=validate_missing_inputs(df, value_cols, idx_cols, msg)
    )

    # Check for correct sign
    if "availability" not in error_columns:
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_availability_exogenous",
            severity="High",
            errors=validate_values(df, value_cols, min=0, max=1)
        )
