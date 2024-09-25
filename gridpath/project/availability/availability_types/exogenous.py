# Copyright 2016-2024 Blue Marble Analytics LLC.
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
(un)availability schedule, i.e. a capacity derate for each timepoint in
which the project may be operated. If fully derated in a given timepoint,
the available project capacity will be 0 in that timepoint and all
operational decision variables will therefore also be constrained to 0 in the
optimization.

"""

import csv
import os.path
from pyomo.environ import Param, Set, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df, subset_init_by_set_membership
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    get_expected_dtypes,
    validate_dtypes,
    validate_values,
    validate_missing_inputs,
)
from gridpath.project.common_functions import (
    determine_project_subset,
)


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
    | | :code:`avl_exog_cap_derate_independent`                               |
    | | *Defined over*: :code:`AVL_EXOG_OPR_TMPS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The pre-specified availability derate (e.g. for maintenance/planned     |
    | outages) that does not depend on weather. Defaults to 1 if not          |
    | specified. Availaibility can also be more than 1.                       |
    +-------------------------------------------------------------------------+
    | | :code:`avl_exog_cap_derate_weather`                                   |
    | | *Defined over*: :code:`AVL_EXOG_OPR_TMPS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The pre-specified availability derate (e.g. for maintenance/planned     |
    | outages) that depends on weather. Defaults to 1 if not specified.       |
    | Availaibility can also be more than 1.                                  |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.AVL_EXOG = Set(within=m.PROJECTS)

    m.AVL_EXOG_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod, superset="PRJ_OPR_TMPS", index=0, membership_set=mod.AVL_EXOG
        ),
    )

    # Required Params
    ###########################################################################

    # For hybrids, this is the derate applied to the generator component
    m.avl_exog_cap_derate_independent = Param(
        m.AVL_EXOG_OPR_TMPS, within=NonNegativeReals, default=1
    )

    m.avl_exog_cap_derate_weather = Param(
        m.AVL_EXOG_OPR_TMPS, within=NonNegativeReals, default=1
    )

    m.avl_exog_hyb_stor_cap_derate_independent = Param(
        m.AVL_EXOG_OPR_TMPS, within=NonNegativeReals, default=1
    )


# Availability Type Methods
###############################################################################


def availability_derate_cap_rule(mod, g, tmp):
    """ """
    return (
        mod.avl_exog_cap_derate_independent[g, tmp]
        * mod.avl_exog_cap_derate_weather[g, tmp]
    )


def availability_derate_hyb_stor_cap_rule(mod, g, tmp):
    """ """
    return mod.avl_exog_hyb_stor_cap_derate_independent[g, tmp]


# Input-Output
###############################################################################


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
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Figure out which projects have this availability type
    project_subset = determine_project_subset(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        column="availability_type",
        type="exogenous",
        prj_or_tx="project",
    )

    data_portal.data()["AVL_EXOG"] = {None: project_subset}

    # Availability derates
    # Get any derates from the project_availability.tab file if it exists;
    # if it does not exist, all projects will get 1 as derate; if it does
    # exist but projects are not specified in it, they will also get 1
    # assigned as their derate
    # The test examples do not currently have a
    # project_availability_exogenous_x.tab, but use the default instead
    availability_independent_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_availability_exogenous_independent.tab",
    )

    if os.path.exists(availability_independent_file):
        data_portal.load(
            filename=availability_independent_file,
            param=(
                m.avl_exog_cap_derate_independent,
                m.avl_exog_hyb_stor_cap_derate_independent,
            ),
        )

    availability_weather_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_availability_exogenous_weather.tab",
    )

    if os.path.exists(availability_weather_file):
        data_portal.load(
            filename=availability_weather_file,
            param=m.avl_exog_cap_derate_weather,
        )


# Database
###############################################################################


def get_inputs_from_database(
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
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """

    ind_sql = f"""
        SELECT project, timepoint, availability_derate_independent, 
        hyb_stor_cap_availability_derate_independent
        -- Select only projects, periods, timepoints from the relevant 
        -- portfolio, relevant opchar scenario id, operational type, 
        -- and temporal scenario id
        FROM 
            (SELECT project, stage_id, timepoint
            FROM project_operational_timepoints
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
            AND project_operational_chars_scenario_id = {subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID}
            AND temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            AND (project_specified_capacity_scenario_id = {subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID}
                 OR project_new_cost_scenario_id = {subscenarios.PROJECT_NEW_COST_SCENARIO_ID})
            AND subproblem_id = {subproblem}
            AND stage_id = {stage}
            ) as projects_periods_timepoints_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_availability_scenario_id and have 'exogenous' as 
        -- their availability type and a non-null 
        -- exogenous_availability_scenario_id, i.e. they have 
        -- timepoint-level availability inputs in the 
        -- inputs_project_availability_exogenous table
        INNER JOIN (
            SELECT project, exogenous_availability_independent_scenario_id
            FROM inputs_project_availability
            WHERE project_availability_scenario_id = {subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID}
            AND availability_type = 'exogenous'
            AND exogenous_availability_independent_scenario_id IS NOT NULL
            ) AS avail_char
        USING (project)
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective availability_derate (and no others) from 
        -- inputs_project_availability_exogenous
        LEFT OUTER JOIN
            inputs_project_availability_exogenous_independent
        USING (exogenous_availability_independent_scenario_id, project, 
                stage_id, timepoint)
        WHERE availability_iteration = {availability_iteration}
        ;
    """

    c1 = conn.cursor()
    independent_availabilities = c1.execute(ind_sql)

    weather_sql = f"""
        SELECT project, timepoint, availability_derate_weather
        -- Select only projects, periods, timepoints from the relevant 
        -- portfolio, relevant opchar scenario id, operational type, 
        -- and temporal scenario id
        FROM 
            (SELECT project, stage_id, timepoint
            FROM project_operational_timepoints
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
            AND project_operational_chars_scenario_id = {subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID}
            AND temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            AND (project_specified_capacity_scenario_id = {subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID}
                 OR project_new_cost_scenario_id = {subscenarios.PROJECT_NEW_COST_SCENARIO_ID})
            AND subproblem_id = {subproblem}
            AND stage_id = {stage}
            ) as projects_periods_timepoints_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_availability_scenario_id and have 'exogenous' as 
        -- their availability type and a non-null 
        -- exogenous_availability_scenario_id, i.e. they have 
        -- timepoint-level availability inputs in the 
        -- inputs_project_availability_exogenous table
        INNER JOIN (
            SELECT project, exogenous_availability_weather_scenario_id
            FROM inputs_project_availability
            WHERE project_availability_scenario_id = {subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID}
            AND availability_type = 'exogenous'
            AND exogenous_availability_weather_scenario_id IS NOT NULL
            ) AS avail_char
        USING (project)
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective availability_derate (and no others) from 
        -- inputs_project_availability_exogenous
        LEFT OUTER JOIN
            inputs_project_availability_exogenous_weather
        USING (exogenous_availability_weather_scenario_id, project, stage_id, 
        timepoint)
        WHERE weather_iteration = {weather_iteration}
        ;
    """

    c2 = conn.cursor()
    weather_availabilities = c2.execute(weather_sql)

    return independent_availabilities, weather_availabilities


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
    :param scenario_directory:
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    independent_availabilities, weather_availabilities = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    independent_availabilities = independent_availabilities.fetchall()
    weather_availabilities = weather_availabilities.fetchall()

    if independent_availabilities:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "project_availability_exogenous_independent.tab",
            ),
            "w",
            newline="",
        ) as availability_tab_file:
            writer = csv.writer(
                availability_tab_file, delimiter="\t", lineterminator="\n"
            )

            writer.writerow(
                [
                    "project",
                    "timepoint",
                    "availability_derate_independent",
                    "hyb_stor_cap_availability_derate_independent",
                ]
            )

            for row in independent_availabilities:
                row = ["." if i is None else i for i in row]
                writer.writerow(row)

    if weather_availabilities:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "project_availability_exogenous_weather.tab",
            ),
            "w",
            newline="",
        ) as availability_tab_file:
            writer = csv.writer(
                availability_tab_file, delimiter="\t", lineterminator="\n"
            )

            writer.writerow(["project", "timepoint", "availability_derate_weather"])

            for row in weather_availabilities:
                row = ["." if i is None else i for i in row]
                writer.writerow(row)


# Validation
###############################################################################


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
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    independent_availabilities, weather_availabilities = get_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    df = cursor_to_df(independent_availabilities)
    idx_cols = ["project", "timepoint"]
    value_cols = ["availability_derate_independent"]

    # Check data types availability
    expected_dtypes = get_expected_dtypes(
        conn,
        [
            "inputs_project_availability",
            "inputs_project_availability_exogenous_independent",
        ],
    )
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_availability_exogenous_independent",
        severity="High",
        errors=dtype_errors,
    )

    # Check for missing inputs
    msg = (
        "If not specified, availability is assumed to be 100%. If you "
        "don't want to specify any availability derates, simply leave the "
        "exogenous_availability_scenario_id empty and this message will "
        "disappear."
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_availability_exogenous_independent",
        severity="Low",
        errors=validate_missing_inputs(df, value_cols, idx_cols, msg),
    )

    # Check for correct sign
    if "availability" not in error_columns:
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            weather_iteration=weather_iteration,
            hydro_iteration=hydro_iteration,
            availability_iteration=availability_iteration,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_availability_exogenous_independent",
            severity="High",
            errors=validate_values(df, value_cols, min=0, max=1),
        )
