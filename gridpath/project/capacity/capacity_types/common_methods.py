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

import csv
import os.path
import pandas as pd

from db.common_functions import spin_on_database_lock
from gridpath.project.common_functions import get_column_row_value


def relevant_periods_by_project_vintage(
    periods, period_start_year, period_end_year, vintage, lifetime_yrs
):
    """
    :param periods: the study periods in a list
    :param period_start_year: dictionary of the start year of a period
        by period
    :param period_end_year: dictionary of the end year of a period
        by period
    :param vintage: the project vintage
    :param lifetime_yrs: the project-vintage lifetime
    :return: the operational or financial periods given the study periods and
        the project vintage and lifetime

    Given the list of study periods and the project's vintage and lifetime (either
    the operational lifetime or the financial lifetime), this function returns the
    list of periods in which a project with this vintage and lifetime will be
    operational (based on the operational lifetime) or incurring an annualized capital
    cost (based on the financial lifetime) respectively. When a project is
    operational, it incurs annual fixed O&M costs.

    Two conditions must be met for a period to be operational / incurring costs for a
    project of a certain vintage:
    1) project vintage (i.e. first operational year) must be before or equal
    to the start year of the period
    2) project last lifetime year must be **after** the period end year.

    The end year of the period is exclusive (i.e. the last day of a period
    with end year 2030 is actually 2020-12-29). With the current
    formulation, a project with a 10 year lifetime of the 2020 vintage is
    assumed to be operational / incurring costs on 2020-01-01 and remain operational
    / incurring costs through 2029-12-31 (vintage 2020, last lifetime year 2030
    exclusive). It will be operational / incurring costs in a period with a start
    year of 2020 and end year of 2030.

    If either the vintage or the last lifetime year is within the period,
    the period is assumed to not be operational / incurring capital costs for the
    project.
    """
    # No relevant periods if vintage does not belong to the project set;
    # this shouldn't happen as we (should) enforce VINTAGES within PERIODS.
    if vintage not in periods:
        return []
    else:
        first_lifetime_year = period_start_year[vintage]
        last_lifetime_year = period_start_year[vintage] + lifetime_yrs
        relevant_periods = list()
        for p in periods:
            if (
                first_lifetime_year <= period_start_year[p]
                and last_lifetime_year >= period_end_year[p]
            ):
                relevant_periods.append(p)

    return relevant_periods


def project_relevant_periods(
    project_vintages_set, relevant_periods_by_project_vintage_set
):
    """
    :param project_vintages_set: the possible project-vintages when capacity
        can be built
    :param relevant_periods_by_project_vintage_set: the project operational
        periods based on vintage
    :return: all study periods when the project could be operational

    Get the periods in which each project COULD be operational (or incurring
    capital costs) given all project-vintages and relevant periods by
    project-vintage (the lifetime is allowed to differ by vintage).
    """
    return sorted(
        list(
            set(
                (g, p)
                for (g, v) in project_vintages_set
                for p in relevant_periods_by_project_vintage_set[g, v]
            )
        )
    )


def project_vintages_relevant_in_period(
    project_vintage_set, relevant_periods_by_project_vintage_set, period
):
    """
    :param project_vintage_set: possible project-vintages when capacity
        could be built
    :param relevant_periods_by_project_vintage_set: the periods when
        project capacity of a particular vintage could be operational (or incurring
        capital costs)
    :param period: the period we're in
    :return: all vintages that could be operational (or incurring capital costs) in a
        period

    Get the project vintages that COULD be operational (or incurring capital costs) in
    each period.
    """
    project_vintages = list()
    for prj, v in project_vintage_set:
        if period in relevant_periods_by_project_vintage_set[prj, v]:
            project_vintages.append((prj, v))

    return project_vintages


# Specified projects common functions
def spec_get_inputs_from_database(conn, subscenarios, capacity_type):
    """
    Get the various capacity and fixed cost parameters for projects with
    "specified" capacity types.
    """
    c = conn.cursor()
    spec_project_params = c.execute(
        """
        SELECT project,
        period,
        specified_capacity_mw,
        hyb_gen_specified_capacity_mw,
        hyb_stor_specified_capacity_mw,
        specified_capacity_mwh,
        fuel_production_capacity_fuelunitperhour,
        fuel_release_capacity_fuelunitperhour,
        fuel_storage_capacity_fuelunit,
        fixed_cost_per_mw_yr,
        hyb_gen_fixed_cost_per_mw_yr,
        hyb_stor_fixed_cost_per_mw_yr,
        fixed_cost_per_mwh_year,
        fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_fixed_cost_per_fuelunit_yr
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal_scenario_id}) as relevant_periods
        INNER JOIN
        (SELECT project, period,
        specified_capacity_mw,
        hyb_gen_specified_capacity_mw,
        hyb_stor_specified_capacity_mw,
        specified_capacity_mwh,
        fuel_production_capacity_fuelunitperhour,
        fuel_release_capacity_fuelunitperhour,
        fuel_storage_capacity_fuelunit
        FROM inputs_project_specified_capacity
        WHERE project_specified_capacity_scenario_id = {project_specified_capacity_scenario_id}) as capacity
        USING (project, period)
        INNER JOIN
        (SELECT project, period,
        fixed_cost_per_mw_yr,
        hyb_gen_fixed_cost_per_mw_yr,
        hyb_stor_fixed_cost_per_mw_yr,
        fixed_cost_per_mwh_year,
        fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_fixed_cost_per_fuelunit_yr
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {project_specified_fixed_cost_scenario_id}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {project_portfolio_scenario_id}
        AND capacity_type = '{capacity_type}'
        ;""".format(
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
            project_specified_capacity_scenario_id=subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            project_specified_fixed_cost_scenario_id=subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID,
            project_portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            capacity_type=capacity_type,
        )
    )

    return spec_project_params


def spec_write_tab_file(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    spec_project_params,
):
    spec_params_filepath = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "spec_capacity_period_params.tab",
    )
    # If spec_capacity_period_params.tab file already exists, append
    # rows to it
    if os.path.isfile(spec_params_filepath):
        with open(spec_params_filepath, "a") as f:
            writer_a = csv.writer(f, delimiter="\t", lineterminator="\n")
            write_from_query(spec_project_params=spec_project_params, writer=writer_a)
    # If spec_capacity_period_params.tab file does not exist,
    # write header first, then add input data
    else:
        with open(spec_params_filepath, "w", newline="") as f:
            writer_w = csv.writer(f, delimiter="\t", lineterminator="\n")
            # Write header
            writer_w.writerow(
                [
                    "project",
                    "period",
                    "specified_capacity_mw",
                    "hyb_gen_specified_capacity_mw",
                    "hyb_stor_specified_capacity_mw",
                    "specified_capacity_mwh",
                    "fuel_production_capacity_fuelunitperhour",
                    "fuel_release_capacity_fuelunitperhour",
                    "fuel_storage_capacity_fuelunit",
                    "fixed_cost_per_mw_yr",
                    "hyb_gen_fixed_cost_per_mw_yr",
                    "hyb_stor_fixed_cost_per_mw_yr",
                    "fixed_cost_per_mwh_yr",
                    "fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr",
                    "fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr",
                    "fuel_storage_capacity_fixed_cost_per_fuelunit_yr",
                ]
            )

            # Write input data
            write_from_query(spec_project_params=spec_project_params, writer=writer_w)


def write_from_query(spec_project_params, writer):
    """
    Helper function for writing the spec project param inputs to avoid
    redundant code in spec_write_tab_file().
    """
    for row in spec_project_params:
        [
            project,
            period,
            specified_capacity_mw,
            hyb_gen_specified_capacity_mw,
            hyb_stor_specified_capacity_mw,
            specified_capacity_mwh,
            fuel_prod_cap,
            fuel_rel_cap,
            fuel_stor_cap,
            fixed_cost_per_mw_yr,
            hyb_gen_fixed_cost_per_mw_yr,
            hyb_stor_fixed_cost_per_mw_yr,
            fixed_cost_per_mwh_year,
            fuel_prod_fom,
            fuel_rel_fom,
            fuel_stor_fom,
        ] = row
        writer.writerow(
            [
                project,
                period,
                specified_capacity_mw,
                hyb_gen_specified_capacity_mw,
                hyb_stor_specified_capacity_mw,
                specified_capacity_mwh,
                fuel_prod_cap,
                fuel_rel_cap,
                fuel_stor_cap,
                fixed_cost_per_mw_yr,
                hyb_gen_fixed_cost_per_mw_yr,
                hyb_stor_fixed_cost_per_mw_yr,
                fixed_cost_per_mwh_year,
                fuel_prod_fom,
                fuel_rel_fom,
                fuel_stor_fom,
            ]
        )


def spec_determine_inputs(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    capacity_type,
):
    # Determine the relevant projects
    project_list = list()

    df = pd.read_csv(
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
        usecols=["project", "capacity_type"],
    )

    for row in zip(df["project"], df["capacity_type"]):
        if row[1] == capacity_type:
            project_list.append(row[0])

    # Determine the operational periods & params for each project/period
    project_period_list = list()
    spec_capacity_mw_dict = dict()
    hyb_gen_spec_capacity_mw_dict = dict()
    hyb_stor_spec_capacity_mw_dict = dict()
    spec_capacity_mwh_dict = dict()
    spec_fuel_prod_cap_dict = dict()
    spec_fuel_rel_cap_dict = dict()
    spec_fuel_stor_cap_dict = dict()
    spec_fixed_cost_per_mw_yr_dict = dict()
    hyb_gen_spec_fixed_cost_per_mw_yr_dict = dict()
    hyb_stor_spec_fixed_cost_per_mw_yr_dict = dict()
    spec_fixed_cost_per_mwh_yr_dict = dict()
    spec_fuel_prod_fixed_cost_dict = dict()
    spec_fuel_rel_fixed_cost_dict = dict()
    spec_fuel_stor_fixed_cost_dict = dict()

    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "spec_capacity_period_params.tab",
        ),
        sep="\t",
    )

    for row in zip(
        df["project"],
        df["period"],
        df["specified_capacity_mw"],
        df["hyb_gen_specified_capacity_mw"],
        df["hyb_stor_specified_capacity_mw"],
        df["specified_capacity_mwh"],
        df["fuel_production_capacity_fuelunitperhour"],
        df["fuel_release_capacity_fuelunitperhour"],
        df["fuel_storage_capacity_fuelunit"],
        df["fixed_cost_per_mw_yr"],
        df["hyb_gen_fixed_cost_per_mw_yr"],
        df["hyb_stor_fixed_cost_per_mw_yr"],
        df["fixed_cost_per_mwh_yr"],
        df["fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr"],
        df["fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr"],
        df["fuel_storage_capacity_fixed_cost_per_fuelunit_yr"],
    ):
        if row[0] in project_list:
            project_period_list.append((row[0], row[1]))
            spec_capacity_mw_dict[(row[0], row[1])] = float(row[2])
            hyb_gen_spec_capacity_mw_dict[(row[0], row[1])] = float(row[3])
            hyb_stor_spec_capacity_mw_dict[(row[0], row[1])] = float(row[4])
            spec_capacity_mwh_dict[(row[0], row[1])] = float(row[5])
            spec_fuel_prod_cap_dict[(row[0], row[1])] = float(row[6])
            spec_fuel_rel_cap_dict[(row[0], row[1])] = float(row[7])
            spec_fuel_stor_cap_dict[(row[0], row[1])] = float(row[8])
            spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = float(row[9])
            hyb_gen_spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = float(row[10])
            hyb_stor_spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = float(row[11])
            spec_fixed_cost_per_mwh_yr_dict[(row[0], row[1])] = float(row[12])
            spec_fuel_prod_fixed_cost_dict[(row[0], row[1])] = float(row[13])
            spec_fuel_rel_fixed_cost_dict[(row[0], row[1])] = float(row[14])
            spec_fuel_stor_fixed_cost_dict[(row[0], row[1])] = float(row[15])

    # Quick check that all relevant projects from projects.tab have capacity
    # params specified
    projects_w_params = [gp[0] for gp in project_period_list]
    diff = list(set(project_list) - set(projects_w_params))

    if diff:
        raise ValueError(
            "Missing capacity/fixed cost inputs for the "
            "following projects: {}".format(diff)
        )

    main_dict = dict()
    main_dict["specified_capacity_mw"] = spec_capacity_mw_dict
    main_dict["hyb_gen_specified_capacity_mw"] = hyb_gen_spec_capacity_mw_dict
    main_dict["hyb_stor_specified_capacity_mw"] = hyb_stor_spec_capacity_mw_dict
    main_dict["specified_capacity_mwh"] = spec_capacity_mwh_dict
    main_dict["fuel_production_capacity_fuelunitperhour"] = spec_fuel_prod_cap_dict
    main_dict["fuel_release_capacity_fuelunitperhour"] = spec_fuel_rel_cap_dict
    main_dict["fuel_storage_capacity_fuelunit"] = spec_fuel_stor_cap_dict
    main_dict["fixed_cost_per_mw_yr"] = spec_fixed_cost_per_mw_yr_dict
    main_dict["hyb_gen_fixed_cost_per_mw_yr"] = hyb_gen_spec_fixed_cost_per_mw_yr_dict
    main_dict["hyb_stor_fixed_cost_per_mw_yr"] = hyb_stor_spec_fixed_cost_per_mw_yr_dict
    main_dict["fixed_cost_per_mwh_yr"] = spec_fixed_cost_per_mwh_yr_dict
    main_dict["fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr"] = (
        spec_fuel_prod_fixed_cost_dict
    )
    main_dict["fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr"] = (
        spec_fuel_rel_fixed_cost_dict
    )
    main_dict["fuel_storage_capacity_fixed_cost_per_fuelunit_yr"] = (
        spec_fuel_stor_fixed_cost_dict
    )

    return project_period_list, main_dict


def read_results_file_generic(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    capacity_type,
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param capacity_type:
    :return:
    """

    # Get the results CSV as dataframe
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_period.csv",
        )
    )

    # Filter by capacity type and aggregate by technology
    capacity_results_agg_df = (
        df.loc[df["capacity_type"] == capacity_type]
        .groupby(by=["load_zone", "technology", "period"], as_index=True)
        .sum(numeric_only=True)
    )

    return capacity_results_agg_df


def write_summary_results_generic(
    results_df, columns, summary_results_file, title, empty_title
):
    # Rename column header
    results_df.columns = columns

    with open(summary_results_file, "a") as outfile:
        outfile.write(f"\n--> {title} <--\n")
        if results_df.empty:
            outfile.write(f"{empty_title}\n")
        else:
            results_df.to_string(outfile, float_format="{:,.2f}".format)
            outfile.write("\n")


def get_units(scenario_directory):
    units_df = pd.read_csv(
        os.path.join(scenario_directory, "units.csv"), index_col="metric"
    )
    power_unit = units_df.loc["power", "unit"]
    energy_unit = units_df.loc["energy", "unit"]
    fuel_unit = units_df.loc["fuel_energy", "unit"]

    return power_unit, energy_unit, fuel_unit
