#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations** package contains modules to describe the
operational capabilities, constraints, and costs of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.
"""

from builtins import next
from builtins import zip
import csv
from pandas import read_csv
import numpy as np
import pandas as pd
import os.path
from pyomo.environ import Set, Param, PositiveReals, Reals, NonNegativeReals

from gridpath.auxiliary.auxiliary import is_number, check_dtypes, \
    get_expected_dtypes, check_column_sign_positive, \
    write_validation_to_database, load_operational_type_modules
from gridpath.project.common_functions import append_to_input_file


# TODO: should we take this out of __init__.py
#   can we create operations.py like we have capacity.py and put it there?
def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`FUEL_PRJS`                                                     |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The list projects that consume fuel.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PRJ_PRD_SGMS`                                             |
    |                                                                         |
    | Three-dimensional set describing fuel projects and their heat rate      |
    | curve segment IDs for each operational period. Unless the project's     |
    | heat rate is constant, the heat rate can be defined by multiple         |
    | piecewise linear segments.                                              |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PRJ_OPR_TMPS`                                             |
    |                                                                         |
    | Two-dimensional set describing fuel projects, and the timepoints in     |
    | which the project could be operational.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PRJ_SGMS_OPR_TMPS`                                        |
    |                                                                         |
    | Three-dimensional set describing fuel projects, their heat rate curve   |
    | segment IDs, and the timepoints in which the project could be           |
    | operational. The fuel burn constraint is applied over this set.         |
    +-------------------------------------------------------------------------+
    | | :code:`VOM_PRJS_PRDS_SGMS`                                            |
    |                                                                         |
    | Three-dimensional set describing projects and their variable O&M cost   |
    | curve segment IDs for each operational period. Unless the project's     |
    | variable O&M is constant, the variable O&M cost can be defined by       |
    | multiple piecewise linear segments.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`VOM_PRJS_OPR_TMPS_SGMS`                                        |
    |                                                                         |
    | Three-dimensional set describing projects, their variable O&M cost      |
    | curve segment IDs, and the timepoints in which the project could be     |
    | operational. The variable O&M cost constraint is applied over this set. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Input Params                                                            |
    +=========================================================================+
    | | :code:`variable_om_cost_per_mwh`                                      |
    | | *Defined over*: :code:`PROJECTS`                                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The variable operations and maintenance (O&M) cost for each project in  |
    | $ per MWh.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`fuel`                                                          |
    | | *Defined over*: :code:`FUEL_PRJS`                                     |
    | | *Within*: :code:`FUELS`                                               |
    |                                                                         |
    | This param describes each fuel project's fuel.                          |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_burn_slope_mmbtu_per_mwh`                                 |
    | | *Defined over*: :code:`FUEL_PRJ_PRD_SGMS`                             |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear fuel burn for    |
    | each project's heat rate segment in each operational period. The units  |
    | are MMBtu of fuel burn per MWh of electricity generation.               |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_burn_intercept_mmbtu_per_mw_hr`                           |
    | | *Defined over*: :code:`FUEL_PRJ_PRD_SGMS`                             |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | This param describes the intercept of the piecewise linear fuel burn    |
    | for each project's heat rate segment in each operational period. The    |
    | units are MMBtu of fuel burn per MW of operational capacity per hour    |
    | (multiply by operational capacity and timepoint duration to get fuel    |
    | burn in MMBtu).                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`vom_slope_cost_per_mwh`                                        |
    | | *Defined over*: :code:`VOM_PRJS_PRDS_SGMS`                            |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear variable O&M     |
    | cost for each project's variable O&M cost segment in each operational   |
    | period. The units are cost of variable O&M per MWh of electricity       |
    | generation.                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`vom_intercept_cost_per_mw_hr`                                  |
    | | *Defined over*: :code:`VOM_PRJS_PRDS_SGMS`                            |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | This param describes the intercept of the piecewise linear variable O&M |
    | cost for each project's variable O&M cost segment in each operational   |
    | period. The units are cost of variable O&M per MW of operational        |
    | capacity per hour (multiply by operational capacity and timepoint       |
    | duration to get actual cost).                                           |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    # TODO: implement check for which generator types can have fuels
    # TODO: re-think how to deal with fuel projects; it's awkward to import
    #  fuel & heat rate params here, but use them in the operational_type
    #  modules with an 'if in FUEL_PRJS'
    m.FUEL_PRJS = Set(
        within=m.PROJECTS
    )

    m.FUEL_PRJ_PRD_SGMS = Set(
        dimen=3
    )

    m.FUEL_PRJ_OPR_TMPS = Set(
        dimen=2,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.FUEL_PRJS)
    )

    m.FUEL_PRJ_SGMS_OPR_TMPS = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PRJ_OPR_TMPS
            for _g, p, s in mod.FUEL_PRJ_PRD_SGMS
            if g in mod.FUEL_PRJS and g == _g and mod.period[tmp] == p)
    )

    m.VOM_PRJS_PRDS_SGMS = Set(
        dimen=3,
        ordered=True
    )

    m.VOM_PRJS_OPR_TMPS_SGMS = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PRJ_OPR_TMPS
            for _g, p, s in mod.VOM_PRJS_PRDS_SGMS
            if g == _g and mod.period[tmp] == p)
    )

    # Input Params
    ###########################################################################

    m.variable_om_cost_per_mwh = Param(m.PROJECTS, within=NonNegativeReals)

    m.fuel = Param(
        m.FUEL_PRJS,
        within=m.FUELS
    )

    m.fuel_burn_slope_mmbtu_per_mwh = Param(
        m.FUEL_PRJ_PRD_SGMS,
        within=PositiveReals
    )

    m.fuel_burn_intercept_mmbtu_per_mw_hr = Param(
        m.FUEL_PRJ_PRD_SGMS,
        within=Reals
    )

    m.vom_slope_cost_per_mwh = Param(
        m.VOM_PRJS_PRDS_SGMS,
        within=PositiveReals
    )

    m.vom_intercept_cost_per_mw_hr = Param(
        m.VOM_PRJS_PRDS_SGMS,
        within=Reals
    )


# Input-Output
###############################################################################


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    # Get column names as a few columns will be optional;
    # won't load data if column does not exist
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "projects.tab")
              ) as prj_file:
        reader = csv.reader(prj_file, delimiter="\t", lineterminator="\n")
        headers = next(reader)

    # Get modelled periods
    # TODO: could we simply use m.PRJ_OPR_PRDS?
    periods = read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "periods.tab"),
        sep="\t"
    )
    periods = set(periods["period"])

    # variable_om_cost_per_mwh (all projects have it, so it's defined here)
    var_cost_df = read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "variable_om_cost_per_mwh"]
    )
    var_cost_dict = dict(
        zip(var_cost_df["project"], var_cost_df["variable_om_cost_per_mwh"])
    )
    data_portal.data()["variable_om_cost_per_mwh"] = var_cost_dict

    # Heat Rate Curves
    if "fuel" in headers:
        # TODO: read_csv seems to fail silently if file not found; check and
        #  implement validation
        hr_df = read_csv(
            os.path.join(scenario_directory, str(subproblem), str(stage),
                         "inputs", "heat_rate_curves.tab"),
            sep="\t"
        )

        pr_df = read_csv(
            os.path.join(scenario_directory, str(subproblem), str(stage),
                         "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "fuel"]
        )
        pr_df = pr_df[pr_df["fuel"] != "."]
        projects = pr_df["project"].tolist()

        fuels_dict = dict(zip(projects, pr_df["fuel"]))

        slope_dict, intercept_dict = \
            get_slopes_intercept_by_project_period_segment(
                hr_df, "average_heat_rate_mmbtu_per_mwh", projects, periods)

        fuel_project_segments = list(slope_dict.keys())

        data_portal.data()["FUEL_PRJS"] = {None: projects}
        data_portal.data()["FUEL_PRJ_PRD_SGMS"] = {None: fuel_project_segments}
        data_portal.data()["fuel"] = fuels_dict
        data_portal.data()["fuel_burn_slope_mmbtu_per_mwh"] = slope_dict
        data_portal.data()["fuel_burn_intercept_mmbtu_per_mw_hr"] = \
            intercept_dict

    # Variable O7M curves
    vom_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "variable_om_curves.tab"),
        sep="\t"
    )
    vom_projects = vom_df["project"].unique().tolist()

    slope_dict, intercept_dict = \
        get_slopes_intercept_by_project_period_segment(
            vom_df, "average_variable_om_cost_per_mwh", vom_projects, periods)

    vom_project_segments = list(slope_dict.keys())

    data_portal.data()["VOM_PRJS_PRDS_SGMS"] = {None: vom_project_segments}
    data_portal.data()["vom_slope_cost_per_mwh"] = slope_dict
    data_portal.data()["vom_intercept_cost_per_mw_hr"] = intercept_dict


def get_slopes_intercept_by_project_period_segment(
        df, input_col, projects, periods):
    """
    Given a DataFrame with the average heat rates or variable O&M curves by
    load point fraction for each project in each period, calculate the slope
    and intercept for the fuel burn or variable O&M cost curves for the
    segments defined by the load points (for each project and period). If the
    period in the DataFrame is zero, set the same slope and intercept for each
    of the modeling periods.
    fractions.

    :param df: DataFrame with columns [project, period, load_point_fraction,
        input_col]
    :param input_col: string with the name of the column in the DataFrame that
        has the average heat rate or variable O&M rate.
    :param projects: list of all the projects to be included
    :param periods: set of all the modeling periods to  be included
    :return: (slope_dict, intercept_dict), with slope_dict and
        intercept_dict a dictionary of the fuel burn / variable O&M cost slope
        and intercept by (project, period, segment).

    """

    slope_dict = {}
    intercept_dict = {}

    for project in projects:
        df_slice = df[df["project"] == project]
        slice_periods = set(df_slice["period"])

        if slice_periods == set([0]):
            p_iterable = [0]
        elif periods.issubset(slice_periods):
            p_iterable = periods
        else:
            raise ValueError(
                """{} for project '{}' isn't specified for all 
                modelled periods. Set period to 0 if inputs are the 
                same for each period or make sure all modelled periods 
                are included.""".format(input_col, project)
            )

        for period in p_iterable:
            df_slice_p = df_slice[df_slice["period"] == period]
            df_slice_p = df_slice_p.sort_values(by=["load_point_fraction"])
            load_points = df_slice_p["load_point_fraction"].values
            averages = df_slice_p[input_col].values

            slopes, intercepts = calculate_slope_intercept(
                project, load_points, averages
            )
            sgms = range(len(slopes))

            # If period is 0, create same inputs for all periods
            if period == 0:
                slope_dict.update(
                    {(project, p, sgms[i]): slope
                     for i, slope in enumerate(slopes)
                     for p in periods}
                )
                intercept_dict.update(
                    {(project, p, sgms[i]): intercept
                     for i, intercept in enumerate(intercepts)
                     for p in periods}
                )
            # If not, create inputs for just this period
            else:
                slope_dict.update(
                    {(project, period, sgms[i]): slope
                     for i, slope in enumerate(slopes)}
                )
                intercept_dict.update(
                    {(project, period, sgms[i]): intercept
                     for i, intercept in enumerate(intercepts)}
                )

    return slope_dict, intercept_dict


def calculate_slope_intercept(project, load_points, heat_rates):
    """
    Calculates slope and intercept for a set of load points and corresponding
    average heat rates or variable O&M rates.
    Note that the intercept will be normalized to the
    operational capacity (Pmax) and the timepoint duration.
    :param project: the project name (for error messages)
    :param load_points: NumPy array with the loading points in fraction of Pmax
    :param heat_rates: NumPy array with the corresponding *average* heat rates
    in MMBtu per MWh or variable O&M in cost/MWh
    :return: slopes, intercepts: tuple with the array of slopes and intercepts
    for each segment. If more than one loading point, the array will have
    one less element than the amount of load points.

    """

    n_points = len(load_points)

    # Data checks
    assert len(load_points) == len(heat_rates)
    if np.any(load_points <= 0) or np.any(heat_rates <= 0):
        raise ValueError(
            """
            Load points and average heat rates should be positive
            numbers. Check heat rate curve inputs for project '{}'.
            """.format(project)
        )
    if n_points == 0:
        raise ValueError(
            """
            Model requires at least one load point and one average
            heat rate input for each fuel project. It seems like
            there are no heat rate inputs for project '{}'.
            """.format(project)
        )

    # if just one point, assume constant heat rate (no intercept)
    if n_points == 1:
        slopes = np.array([heat_rates[0]])
        intercepts = np.array([0])
    else:
        fuel_burn = load_points * heat_rates
        incr_loads = np.diff(load_points)
        incr_fuel_burn = np.diff(fuel_burn)
        slopes = incr_fuel_burn / incr_loads
        intercepts = fuel_burn[:-1] - slopes * load_points[:-1]

        # Data Checks
        if np.any(incr_loads <= 0):
            raise ValueError(
                """
                Load points in curve should be strictly
                increasing. Check curve inputs for project '{}'.
                """.format(project)
            )
        if np.any(incr_fuel_burn <= 0):
            raise ValueError(
                """
                Total fuel burn or variable O&M cost should be strictly 
                increasing between load points. Check heat rate curve inputs
                for project '{}'.
                """.format(project)
            )
        if np.any(np.diff(slopes) <= 0):
            raise ValueError(
                """
                The fuel burn or variable O&M cost as a function of power 
                output should be a convex function, i.e. the incremental 
                heat rate or variable O&M rate should
                be positive and strictly increasing. Check curve inputs for 
                project '{}'.
                """.format(project)
            )

    return slopes, intercepts


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
    proj_opchar = c.execute("""
        SELECT project, fuel, variable_cost_per_mwh,
        min_stable_level_fraction, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        ramp_up_when_on_rate,
        ramp_down_when_on_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, maximum_duration_hours,
        aux_consumption_frac_capacity, aux_consumption_frac_power,
        last_commitment_stage
        -- Get only the subset of projects in the portfolio with their 
        -- capacity types based on the project_portfolio_scenario_id 
        FROM
        (SELECT project, capacity_type
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}) as portfolio_tbl
        LEFT OUTER JOIN
        -- Select the operational characteristics based on the 
        -- project_operational_chars_scenario_id
        inputs_project_operational_chars
        USING (project)
        WHERE project_operational_chars_scenario_id = {}
        ;
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
        )
    )

    # Get heat rate curves;
    # Select only heat rate curves of projects in the portfolio
    # Use left outer join so we include all projects, even those without a
    # heat rate scenario_id match (for input validation)
    c1 = conn.cursor()
    heat_rates = c1.execute(
        """
        SELECT project, fuel, heat_rate_curves_scenario_id, period,
        load_point_fraction, average_heat_rate_mmbtu_per_mwh
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, fuel, heat_rate_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) AS op_char
        USING(project)
        LEFT OUTER JOIN
        inputs_project_heat_rate_curves
        USING(project, heat_rate_curves_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    # Get variable O&M curves;
    # Select only variable OM curves of projects in the portfolio
    # Use left outer join so we include all projects, even those without a
    # variable O&M scenario_id match (for input validation)
    c3 = conn.cursor()
    variable_om = c3.execute(
        """
        SELECT project, variable_om_curves_scenario_id, period,  
        load_point_fraction, average_variable_om_cost_per_mwh
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, variable_om_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        -- only select variable OM curves inputs with matching projects
        -- (will return all projects in portfolio with Nulls if no scenario_id 
        -- match)
        LEFT OUTER JOIN
        inputs_project_variable_om_curves
        USING(project, variable_om_curves_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        AND variable_om_curves_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return proj_opchar, heat_rates, variable_om


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    heat_rate_curves.tab and variable_om_curves.tab files
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    proj_opchar, heat_rates, variable_om = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Update the projects.tab file
    new_columns = [
        "fuel", "variable_om_cost_per_mwh",
        "min_stable_level_fraction",
        "unit_size_mw",
        "startup_cost_per_mw", "shutdown_cost_per_mw",
        "startup_fuel_mmbtu_per_mw",
        "startup_plus_ramp_up_rate",
        "shutdown_plus_ramp_down_rate",
        "ramp_up_when_on_rate",
        "ramp_down_when_on_rate",
        "min_up_time_hours", "min_down_time_hours",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours", "maximum_duration_hours",
        "aux_consumption_frac_capacity", "aux_consumption_frac_power",
        "last_commitment_stage"
    ]
    append_to_input_file(
        inputs_directory=os.path.join(scenario_directory, str(subproblem), str(stage),
                                      "inputs"),
        input_file="projects.tab",
        query_results=proj_opchar,
        index_n_columns=1,
        new_column_names=new_columns
    )

    # Convert heat rates to dataframe and pre-process data
    # (filter out only projects with fuel; select columns, convert periods
    # type to integer)
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )
    fuel_mask = pd.notna(hr_df["fuel"])
    columns = ["project", "period", "load_point_fraction",
               "average_heat_rate_mmbtu_per_mwh"]
    hr_df = hr_df[columns][fuel_mask].astype({"period": int})
    heat_rates = hr_df.values

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "heat_rate_curves.tab"),
              "w", newline="") as \
            heat_rate_tab_file:
        writer = csv.writer(heat_rate_tab_file, delimiter="\t",
                            lineterminator="\n")

        writer.writerow(["project", "period", "load_point_fraction",
                         "average_heat_rate_mmbtu_per_mwh"])

        for row in heat_rates:
            writer.writerow(row)

    # Convert variable O&M curves to dataframe and pre-process data
    # (remove the variable O&M scenario ID column)
    vom_df = pd.DataFrame(
        data=variable_om.fetchall(),
        columns=[s[0] for s in variable_om.description]
    )
    columns = ["project", "period", "load_point_fraction",
               "average_variable_om_cost_per_mwh"]
    variable_om = vom_df[columns].values

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "variable_om_curves.tab"),
              "w", newline="") as variable_om_tab_file:
        writer = csv.writer(variable_om_tab_file, delimiter="\t",
                            lineterminator="\n")

        writer.writerow(["project", "period", "load_point_fraction",
                         "average_variable_om_cost_per_mwh"])

        for row in variable_om:
            writer.writerow(row)


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

    validation_results = []

    # Get the project input data
    proj_opchar, heat_rates, variable_om = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Convert input data into DataFrame
    prj_df = pd.DataFrame(
        data=proj_opchar.fetchall(),
        columns=[s[0] for s in proj_opchar.description]
    )
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )
    vom_df = pd.DataFrame(
        data=variable_om.fetchall(),
        columns=[s[0] for s in variable_om.description]
    )

    # Check data types operational chars:
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_operational_chars"]
    )

    dtype_errors, error_columns = check_dtypes(prj_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "High",
             "Invalid data type",
             error
             )
        )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in prj_df.columns if expected_dtypes[c] ==
                       "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    sign_errors = check_column_sign_positive(prj_df, valid_numeric_columns)
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
    if "min_stable_level_fraction" not in error_columns:
        validation_errors = validate_min_stable_level(prj_df)
        for error in validation_errors:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 subproblem,
                 stage,
                 __name__,
                 "PROJECT_OPERATIONAL_CHARS",
                 "inputs_project_operational_chars",
                 "High",
                 "Invalid min_stable_level_fraction",
                 error
                 )
            )

    # Check data types heat_rates and variable_om:
    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    sub_hr_df = hr_df[hr_curve_mask][
        ["project", "load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
    ]
    vom_curve_mask = pd.notna(vom_df["variable_om_curves_scenario_id"])
    sub_vom_df = vom_df[vom_curve_mask][
        ["project", "load_point_fraction", "average_variable_om_cost_per_mwh"]
    ]

    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_portfolios", "inputs_project_operational_chars",
               "inputs_project_heat_rate_curves",
               "inputs_project_variable_om_curves"]
    )
    dtype_errors, error_columns = check_dtypes(sub_hr_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_HEAT_RATE_CURVES",
             "inputs_project_heat_rate_curves",
             "High",
             "Invalid data type",
             error
             )
        )
    dtype_errors, error_columns = check_dtypes(sub_vom_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_VARIABLE_OM_CURVES",
             "inputs_project_variable_om_curves",
             "High",
             "Invalid data type",
             error
             )
        )

    # Check valid numeric columns in heat rates are non-negative
    numeric_columns = [c for c in sub_hr_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    sign_errors = check_column_sign_positive(sub_hr_df, valid_numeric_columns)
    for error in sign_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_HEAT_RATE_CURVES",
             "inputs_project_heat_rate_curves",
             "High",
             "Invalid numeric sign",
             error
             )
        )

    # Check valid numeric columns in variable OM are non-negative
    numeric_columns = [c for c in sub_vom_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    sign_errors = check_column_sign_positive(sub_vom_df, valid_numeric_columns)
    for error in sign_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_VARIABLE_OM_CURVES",
             "inputs_project_variable_om_curves",
             "High",
             "Invalid numeric sign",
             error
             )
        )

    # Check for consistency between fuel and heat rate curve inputs
    # 1. Make sure projects with fuel have a heat rate scenario specified
    # 2. Make sure projects without fuel have no heat rate scenario specified
    validation_errors = validate_fuel_vs_heat_rates(hr_df)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "High"
             "Missing/Unnecessary heat rate scenario inputs",
             error
             )
        )

    # Check that specified hr scenarios actually have inputs in the hr table
    # and check that specified heat rate curves inputs are valid:
    validation_errors = validate_heat_rate_curves(hr_df)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_HEAT_RATE_CURVES",
             "inputs_project_heat_rate_curves",
             "High",
             "Invalid/Missing heat rate curves inputs",
             error
             )
        )

    # Check that specified vom scenarios actually have inputs in the vom table
    # and check that specified vom curves inputs are valid:
    validation_errors = validate_vom_curves(vom_df)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_VARIABLE_OM_CURVES",
             "inputs_project_variable_om_curves",
             "High",
             "Invalid/Missing variable O&M curves inputs",
             error
             )
        )

    # TODO: check that if there is a "0" for the period for a given
    #  project there are zeroes everywhere for that project.

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def validate_min_stable_level(df):
    """
    Check 0 < min stable fraction <= 1
    :param df:
    :return:
    """
    results = []

    invalids = ((df["min_stable_level_fraction"] <= 0) |
                (df["min_stable_level_fraction"] > 1))
    if invalids.any():
        bad_projects = df["project"][invalids].values
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': expected 0 < min_stable_level <= 1"
            .format(print_bad_projects)
        )

    return results


def validate_fuel_vs_heat_rates(hr_df):
    """
    Make sure projects with fuel have a heat rate scenario specified.
    Conversely, if no fuel is specified, make sure there is no heat rate
    scenario specified.
    :param hr_df:
    :return:
    """
    results = []

    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    fuel_mask = pd.notna(hr_df["fuel"])

    invalids = fuel_mask & ~hr_curve_mask
    if invalids.any():
        bad_projects = hr_df["project"][invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Missing heat_rate_curves_scenario_id"
            .format(print_bad_projects)
        )

    invalids = ~fuel_mask & hr_curve_mask
    if invalids.any():
        bad_projects = pd.unique(hr_df["project"][invalids])
        print_bad_projects = ", ".join(bad_projects)
        results.append(
             "Project(s) '{}': No fuel specified so no heat rate expected"
             .format(print_bad_projects)
        )

    return results


def validate_heat_rate_curves(hr_df):
    """
    1. Check that specified heat rate scenarios actually have inputs in the
       heat rate curves table
    2. Check that specified heat rate curves inputs are valid:
        - strictly increasing load points
        - increasing total fuel burn
        - convex fuel burn curve
    :param hr_df:
    :return:
    """
    results = []

    fuel_mask = pd.notna(hr_df["fuel"])
    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    load_point_mask = pd.notna(hr_df["load_point_fraction"])

    # Check for missing inputs in heat rates curves table
    invalids = hr_curve_mask & ~load_point_mask
    if invalids.any():
        bad_projects = hr_df["project"][invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Expected at least one load point"
            .format(print_bad_projects)
        )

    # Check that each project has convex heat rates etc.
    relevant_mask = fuel_mask & load_point_mask
    hr_df = hr_df[relevant_mask]
    for project in hr_df["project"].unique():
        for period in hr_df[hr_df["project"] == project]["period"].unique():
            # read in the power setpoints and average heat rates
            hr_slice = hr_df[(hr_df["project"] == project)
                             & (hr_df["period"] == period)]
            hr_slice = hr_slice.sort_values(by=["load_point_fraction"])
            load_points = hr_slice["load_point_fraction"].values
            heat_rates = hr_slice["average_heat_rate_mmbtu_per_mwh"].values

            if len(load_points) > 1:
                incr_loads = np.diff(load_points)

                if np.any(incr_loads == 0):
                    # note: primary key should already prohibit this
                    results.append(
                        "Project(s) '{}': load points can not be identical"
                        .format(project)
                    )

                else:
                    fuel_burn = load_points * heat_rates
                    incr_fuel_burn = np.diff(fuel_burn)
                    slopes = incr_fuel_burn / incr_loads

                    if np.any(incr_fuel_burn <= 0):
                        results.append(
                            "Project(s) '{}': Total fuel burn should increase "
                            "with increasing load"
                            .format(project)
                        )
                    if np.any(np.diff(slopes) <= 0):
                        results.append(
                            "Project(s) '{}': Fuel burn should be convex, "
                            "i.e. marginal heat rate should increase with "
                            "increading load"
                            .format(project)
                        )

    return results


def validate_vom_curves(vom_df):
    """
    1. Check that specified variable O&M scenarios actually have inputs in the
       variable O&M curves table
    2. Check that specified variable O&M curves inputs are valid:
        - strictly increasing load points
        - increasing total variable O&M cost
        - convex variable O&M curve
    :param vom_df:
    :return:
    """
    results = []

    vom_curve_mask = pd.notna(vom_df["variable_om_curves_scenario_id"])
    load_point_mask = pd.notna(vom_df["load_point_fraction"])

    # Check for missing inputs in heat rates curves table
    invalids = vom_curve_mask & ~load_point_mask
    if invalids.any():
        bad_projects = vom_df["project"][invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Expected at least one load point"
            .format(print_bad_projects)
        )

    # Check that each project has convex variable O&M rates etc.
    vom_df = vom_df[load_point_mask]
    for project in vom_df["project"].unique():
        for period in vom_df[vom_df["project"] == project]["period"].unique():
            # read in the power setpoints and average variable O&M
            vom_slice = vom_df[(vom_df["project"] == project)
                               & (vom_df["period"] == period)]
            vom_slice = vom_slice.sort_values(by=["load_point_fraction"])
            load_points = vom_slice["load_point_fraction"].values
            vom = vom_slice["average_variable_om_cost_per_mwh"].values

            if len(load_points) > 1:
                incr_loads = np.diff(load_points)

                if np.any(incr_loads == 0):
                    # note: primary key should already prohibit this
                    results.append(
                        "Project(s) '{}': load points can not be identical"
                        .format(project)
                    )

                else:
                    vom_cost = load_points * vom
                    incr_vom_cost = np.diff(vom_cost)
                    slopes = incr_vom_cost / incr_loads

                    if np.any(incr_vom_cost <= 0):
                        results.append(
                            "Project(s) '{}': Total variable O&M cost should "
                            "increase with increasing load"
                            .format(project)
                        )
                    if np.any(np.diff(slopes) <= 0):
                        results.append(
                            "Project(s) '{}': Variable O&M cost should be "
                            "convex, i.e. variable O&M rate should increase "
                            "with increasing load"
                            .format(project)
                        )

    return results
