#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

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
import pandas as pd
from pyomo.environ import Param, Set, PercentFraction

from gridpath.auxiliary.auxiliary import check_dtypes, get_expected_dtypes
from gridpath.project.common_functions import determine_project_subset


def add_module_specific_components(m, d):
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
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.AVL_EXOG)
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

def load_module_specific_data(
        m, data_portal, scenario_directory, subproblem, stage
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
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """

    c = conn.cursor()
    availabilities = c.execute("""
        SELECT project, timepoint, availability_derate
        FROM (
        -- Select only projects from the relevant portfolio
        SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}
        ) as portfolio_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_availability_scenario_id and have 'exogenous' as 
        -- their availability type and a non-null 
        -- exogenous_availability_scenario_id, i.e. they have 
        -- timepoint-level availability inputs in the 
        -- inputs_project_availability_exogenous table
        INNER JOIN (
            SELECT project, exogenous_availability_scenario_id
            FROM inputs_project_availability_types
            WHERE project_availability_scenario_id = {}
            AND availability_type = 'exogenous'
            AND exogenous_availability_scenario_id IS NOT NULL
            ) AS avail_char
         USING (project)
         -- Cross join to the timepoints in the relevant 
         -- temporal_scenario_id, subproblem_id, and stage_id
         -- Get the period since we'll need that to get only the operational 
         -- timepoints for a project via an INNER JOIN below
         CROSS JOIN (
            SELECT stage_id, timepoint, period
            FROM inputs_temporal_timepoints
            WHERE temporal_scenario_id = {}
            AND subproblem_id = {}
            AND stage_id = {}
            ) as tmps_tbl
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective availability_derate from the 
        -- inputs_project_availability_exogenous (and no others) through a 
        -- LEFT OUTER JOIN
        LEFT OUTER JOIN
        inputs_project_availability_exogenous
        USING (exogenous_availability_scenario_id, project, stage_id, 
        timepoint)
        -- We also only want timepoints in periods when the project actually 
        -- exists, so we figure out the operational periods for each of the  
        -- projects below and INNER JOIN to that
        INNER JOIN
            (SELECT project, period
            FROM (
                -- Get the operational periods for each 'specified' and 
                -- 'new' project
                SELECT project, period
                FROM inputs_project_specified_capacity
                WHERE project_specified_capacity_scenario_id = {}
                AND specified_capacity_mw > 0
                UNION
                SELECT project, period
                FROM inputs_project_new_cost
                WHERE project_new_cost_scenario_id = {}
                ) as all_operational_project_periods
            -- Only use the periods in temporal_scenario_id via an INNER JOIN
            INNER JOIN (
                SELECT period
                FROM inputs_temporal_periods
                WHERE temporal_scenario_id = {}
                ) as relevant_periods_tbl
            USING (period)
            ) as relevant_op_periods_tbl
        USING (project, period);
        """.format(
        subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID,
        subscenarios.TEMPORAL_SCENARIO_ID,
        subproblem,
        stage,
        subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
        subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
        subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return availabilities


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    :param inputs_directory:
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    availabilities = get_inputs_from_database(
        subscenarios, subproblem, stage, conn
    ).fetchall()

    if availabilities:
        with open(os.path.join(inputs_directory,
                               "project_availability_exogenous.tab"),
                  "w", newline="") as availability_tab_file:
            writer = csv.writer(availability_tab_file, delimiter="\t", lineterminator="\n")

            writer.writerow(["project", "timepoint", "availability_derate"])

            for row in availabilities:
                writer.writerow(row)


# Validation
###############################################################################

def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    availabilities = get_inputs_from_database(
        subscenarios, subproblem, stage, conn
    )

    av_df = pd.DataFrame(
        data=availabilities.fetchall(),
        columns=[s[0] for s in availabilities.description]
    )

    validation_results = []
    # Check data types availability
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_availability_types",
               "inputs_project_availability_exogenous"])
    dtype_errors, error_columns = check_dtypes(av_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_AVAILABILITY",
             "inputs_project_availability_exogenous",
             "Invalid data type",
             error
             )
        )

    if "availability" not in error_columns:
        validation_errors = validate_availability(av_df)
        for error in validation_errors:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 subproblem,
                 stage,
                 __name__,
                 "PROJECT_AVAILABILITY",
                 "inputs_project_availability_exogenous",
                 "Invalid availability (exogenous)",
                 error
                 )
            )


def validate_availability(av_df):
    """
    Check 0 <= availability <= 1
    :param av_df:
    :return:
    """
    results = []

    invalids = ((av_df["availability_derate"] < 0) |
                (av_df["availability_derate"] > 1))
    if invalids.any():
        bad_projects = av_df["project"][invalids].values
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': expected 0 <= avl_exog_derate <= 1"
            .format(print_bad_projects)
        )

    return results
