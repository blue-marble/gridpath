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

import csv
import os.path
import pandas as pd

from db.common_functions import spin_on_database_lock
from gridpath.project.common_functions import get_column_row_value


# TODO: if vintage is 2020 and lifetime is 30, is the project available in
#  2050 or not -- maybe have options for how this should be treated?


def operational_periods_by_project_vintage(periods, vintage, lifetime):
    """
    :param periods: the study periods
    :param vintage: the project vintage
    :param lifetime: the project-vintage lifetime
    :return: the operational periods given the study periods and
        the project vintage and lifetime

    Given the list of study periods and the project's vintage and lifetime,
    this function returns the list of periods that a project with
    this vintage and lifetime will be operational.
    """
    operational_periods = list()
    for p in periods:
        if vintage <= p < vintage + lifetime:
            operational_periods.append(p)
        else:
            pass
    return operational_periods


def project_operational_periods(project_vintages_set,
                                operational_periods_by_project_vintage_set):
    """
    :param project_vintages_set: the possible project-vintages when capacity
        can be built
    :param operational_periods_by_project_vintage_set: the project operational
        periods based on vintage
    :return: all study periods when the project could be operational

    Get the periods in which each project COULD be operational given all
    project-vintages and operational periods by project-vintage (the
    lifetime is allowed to differ by vintage).
    """
    return set((g, p)
               for (g, v) in project_vintages_set
               for p
               in operational_periods_by_project_vintage_set[g, v]
               )


def project_vintages_operational_in_period(
        project_vintage_set, operational_periods_by_project_vintage_set,
        period):
    """
    :param project_vintage_set: possible project-vintages when capacity
        could be built
    :param operational_periods_by_project_vintage_set: the periods when
        project capacity of a particular vintage could be operational
    :param period: the period we're in
    :return: all vintages that could be operational in a period

    Get the project vintages that COULD be operational in each period.
    """
    project_vintages = list()
    for (prj, v) in project_vintage_set:
        if period in operational_periods_by_project_vintage_set[prj, v]:
            project_vintages.append((prj, v))
        else:
            pass
    return project_vintages


def update_capacity_results_table(
     db, c, results_directory, scenario_id, subproblem, stage, results_file
):
    results = []
    with open(os.path.join(results_directory, results_file), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        header = next(reader)

        for row in reader:
            project = row[0]
            period = row[1]
            new_build_mw = get_column_row_value(header, "new_build_mw", row)
            new_build_mwh = get_column_row_value(header, "new_build_mwh", row)
            new_build_binary = get_column_row_value(header,
                                                    "new_build_binary", row)
            retired_mw = get_column_row_value(header, "retired_mw", row)
            retired_binary = get_column_row_value(header, "retired_binary",
                                                  row)

            results.append(
                (new_build_mw, new_build_mwh, new_build_binary,
                 retired_mw, retired_binary,
                 scenario_id, project, period, subproblem, stage)
            )

    # Update the results table with the module-specific results
    update_sql = """
        UPDATE results_project_capacity
        SET new_build_mw = ?,
        new_build_mwh = ?,
        new_build_binary = ?,
        retired_mw = ?,
        retired_binary = ?
        WHERE scenario_id = ?
        AND project = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """

    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)


# Specified projects common functions
def spec_get_inputs_from_database(conn, subscenarios, capacity_type):
    c = conn.cursor()
    spec_project_params = \
        c.execute(
        """SELECT project, period, specified_capacity_mw,
        specified_capacity_mwh,
        fixed_cost_per_mw_year, fixed_cost_per_mwh_year
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, specified_capacity_mw,
        specified_capacity_mwh, hyb_gen_specified_capacity_mw, 
        hyb_stor_specified_capacity_mw, hyb_stor_specified_capacity_mwh
        FROM inputs_project_specified_capacity
        WHERE project_specified_capacity_scenario_id = {}) as capacity
        USING (project, period)
        INNER JOIN
        (SELECT project, period,
        fixed_cost_per_mw_year,
        fixed_cost_per_mwh_year
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = '{}'
        ;""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            capacity_type
        )
    )
    return spec_project_params


def spec_write_tab_file(
    scenario_directory, subproblem, stage, spec_project_params
):
    # If spec_capacity_period_params.tab file already exists, append
    # rows to it
    if os.path.isfile(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                                   "spec_capacity_period_params.tab")
                      ):
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "spec_capacity_period_params.tab"),
                  "a") as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t", lineterminator="\n")
            for row in spec_project_params:
                [project, period, specified_capacity_mw,
                 specified_capacity_mwh,
                 fixed_cost_per_mw_year, fixed_cost_per_mwh_year] \
                    = row
                writer.writerow(
                    [project, period,
                     specified_capacity_mw,
                     specified_capacity_mwh,
                     fixed_cost_per_mw_year,
                     fixed_cost_per_mwh_year]
                )
    # If spec_capacity_period_params.tab file does not exist,
    # write header first, then add input data
    else:
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "spec_capacity_period_params.tab"),
                  "w", newline="") as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["project", "period",
                 "specified_capacity_mw",
                 "specified_capacity_mwh",
                 "fixed_cost_per_mw_yr",
                 "fixed_cost_per_mwh_yr"]
            )

            # Write input data
            for row in spec_project_params:
                [project, period, specified_capacity_mw,
                 specified_capacity_mwh,
                 fixed_cost_per_mw_year,
                 fixed_cost_per_mwh_year] \
                    = row
                writer.writerow(
                    [project, period,
                     specified_capacity_mw,
                     specified_capacity_mwh,
                     fixed_cost_per_mw_year,
                     fixed_cost_per_mwh_year]
                )


def spec_determine_inputs(
    scenario_directory, subproblem, stage, capacity_type
):

    # Determine the relevant projects
    project_list = list()

    df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "projects.tab"),
        sep="\t",
        usecols=["project", "capacity_type"]
    )

    for row in zip(df["project"],
                   df["capacity_type"]):
        if row[1] == capacity_type:
            project_list.append(row[0])
        else:
            pass

    # Determine the operational periods & params for each project/period
    project_period_list = list()
    spec_capacity_mw_dict = dict()
    spec_capacity_mwh_dict = dict()
    spec_fixed_cost_per_mw_yr_dict = dict()
    spec_fixed_cost_per_mwh_yr_dict = dict()

    df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "spec_capacity_period_params.tab"),
        sep="\t"
    )

    for row in zip(df["project"],
                   df["period"],
                   df["specified_capacity_mw"],
                   df["specified_capacity_mwh"],
                   df["fixed_cost_per_mw_yr"],
                   df["fixed_cost_per_mwh_yr"]):
        if row[0] in project_list:
            project_period_list.append((row[0], row[1]))
            spec_capacity_mw_dict[(row[0], row[1])] = \
                float(row[2])
            spec_capacity_mwh_dict[(row[0], row[1])] = \
                float(row[3])
            spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = \
                float(row[4])
            spec_fixed_cost_per_mwh_yr_dict[(row[0], row[1])] = \
                float(row[5])
        else:
            pass

    # Quick check that all relevant projects from projects.tab have capacity
    # params specified
    projects_w_params = [gp[0] for gp in project_period_list]
    diff = list(set(project_list) - set(projects_w_params))
    if diff:
        raise ValueError("Missing capacity/fixed cost inputs for the "
                         "following gen_spec projects: {}".format(diff))

    return project_period_list, \
        spec_capacity_mw_dict, \
        spec_capacity_mwh_dict, \
        spec_fixed_cost_per_mw_yr_dict, \
        spec_fixed_cost_per_mwh_yr_dict
