#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, PercentFraction

from gridpath.auxiliary.auxiliary import check_dtypes, get_expected_dtypes
from gridpath.project.maintenance.maintenance_types.common_functions import \
    determine_project_subset


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Sets
    m.EXOGENOUS_MAINTENANCE_PROJECTS = Set(within=m.PROJECTS)

    # TODO: factor out this lambda rule, as it is used in all operational type
    #  modules and maintenance type modules
    m.EXOGENOUS_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.EXOGENOUS_MAINTENANCE_PROJECTS
            )
    )
    
    # Availability derate (e.g. for maintenance/planned outages)
    # This can be optionally loaded from external data, but defaults to 1
    m.availability_derate = Param(
        m.EXOGENOUS_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction, default=1
    )


def maintenance_derate_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.availability_derate[g, tmp]


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
    # Figure out which projects have this maintenance type
    projects_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs", "projects.tab"
    )
    header = pd.read_csv(
        projects_file, sep="\t", header=None, nrows=1
    ).values[0]

    # If "maintenance_type" is among the column headers, use that to
    # determine; otherwise, assign "exogenous_maintenance" to all projects
    # (this is the default for the maintenance_type param defined in the
    # project __init__.py module)
    if "maintenance_type" in header:
        project_subset = determine_project_subset(
            scenario_directory=scenario_directory,
            subproblem=subproblem, stage=stage, column="maintenance_type",
            type="exogenous_maintenance"
        )
    else:
        project_subset = \
            pd.read_csv(projects_file, sep="\t")["project"].tolist()

    data_portal.data()["EXOGENOUS_MAINTENANCE_PROJECTS"] = \
        {None: project_subset}

    # Availability derates
    # Get any derates from the project_availability.tab file if it exists;
    # if it does not exists, all projects will get 1 as a derate; if it does
    # exist but projects are not specified in it, they will also get 1
    # assigned as their derate
    availability_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "project_availability.tab"
    )

    if os.path.exists(availability_file):
        data_portal.load(
            filename=availability_file,
            param=m.availability_derate
        )
    else:
        pass


def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """

    # Get project availability if project_availability_scenario_id is not NUL
    c = conn.cursor()
    if subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID is None:
        availabilities = c.execute(
            """SELECT project, timepoint, availability
            FROM inputs_project_availability
            WHERE 1=0"""
        )
    else:
        availabilities = c.execute(
            """SELECT project, timepoint, availability
            FROM inputs_project_availability_exogenous
            INNER JOIN inputs_project_portfolios
            USING (project)
            INNER JOIN
            (SELECT timepoint
            FROM inputs_temporal_timepoints
            WHERE temporal_scenario_id = {}
            AND subproblem_id = {}
            AND stage_id = {}) as relevant_timepoints
            USING (timepoint)
            WHERE project_portfolio_scenario_id = {}
            AND project_availability_scenario_id = {};""".format(
                subscenarios.TEMPORAL_SCENARIO_ID,
                subproblem,
                stage,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
                subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID,
            )
        )

    return availabilities


def write_module_specific_inputs(
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
    availabilities = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)
    # Fetch availability inputs
    availabilities = availabilities.fetchall()

    if availabilities:
        with open(os.path.join(inputs_directory, "project_availability.tab"),
                  "w", newline="") as \
                availability_tab_file:
            writer = csv.writer(availability_tab_file, delimiter="\t")

            writer.writerow(["project", "timepoint", "availability_derate"])

            for row in availabilities:
                writer.writerow(row)


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    availabilities = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn
    )

    av_df = pd.DataFrame(
        data=availabilities.fetchall(),
        columns=[s[0] for s in availabilities.description]
    )

    validation_results = []
    # Check data types availability
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_availability"])
    dtype_errors, error_columns = check_dtypes(av_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_AVAILABILITY",
             "inputs_project_availability",
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
                 "inputs_project_availability",
                 "Invalid availability",
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

    invalids = ((av_df["availability"] < 0) |
                (av_df["availability"] > 1))
    if invalids.any():
        bad_projects = av_df["project"][invalids].values
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': expected 0 <= availability <= 1"
            .format(print_bad_projects)
        )

    return results
