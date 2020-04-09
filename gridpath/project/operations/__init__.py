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
from pyomo.environ import Set, Param, PositiveReals, Reals

from gridpath.auxiliary.auxiliary import is_number, check_dtypes, \
    get_expected_dtypes, check_column_sign_positive, \
    write_validation_to_database, load_operational_type_modules
from gridpath.project.common_functions import append_to_projects_input_file


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
    | | :code:`FUEL_PRJ_SGMS`                                                 |
    |                                                                         |
    | Two-dimensional set describing fuel projects and their heat rate curve  |
    | segment IDs. Unless the project's heat rate is constant, the heat rate  |
    | can be defined by multiple piecewise linear segments.                   |
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
    | | :code:`VOM_PRJS_SGMS`                                                 |
    |                                                                         |
    | Two-dimensional set describing projects and their variable O&M cost     |
    | curve segment IDs. Unless the project's variable O&M is constant,       |
    | the variable O&M cost can be defined by multiple piecewise linear       |
    | segments.                                                               |
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
    | | :code:`fuel`                                                          |
    | | *Defined over*: :code:`FUEL_PRJS`                                     |
    | | *Within*: :code:`FUELS`                                               |
    |                                                                         |
    | This param describes each fuel project's fuel.                          |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_burn_slope_mmbtu_per_mwh`                                 |
    | | *Defined over*: :code:`FUEL_PRJ_SGMS`                                 |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear fuel burn for    |
    | each project's heat rate segment. The units are MMBtu of fuel burn per  |
    | MWh of electricity generation.                                          |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_burn_intercept_mmbtu_per_mw_hr`                           |
    | | *Defined over*: :code:`FUEL_PRJ_SGMS`                                 |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | This param describes the intercept of the piecewise linear fuel burn    |
    | for each project's heat rate segment. The units are MMBtu of fuel burn  |
    | per MW of operational capacity per hour (multiply by operational        |
    | capacity and timepoint duration to get fuel burn in MMBtu).             |
    +-------------------------------------------------------------------------+
    | | :code:`vom_slope_cost_per_mwh`                                        |
    | | *Defined over*: :code:`VOM_PRJS_SGMS`                                 |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear variable O&M     |
    | cost for each project's variable O&M cost segment. The units are cost   |
    | of variable O&M per MWh of electricity generation.                      |
    +-------------------------------------------------------------------------+
    | | :code:`vom_intercept_cost_per_mw_hr`                                  |
    | | *Defined over*: :code:`VOM_PRJS_SGMS`                                 |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | This param describes the intercept of the piecewise linear variable O&M |
    | cost for each project's variable O&M cost segment. The units are cost   |
    | of variable O&M per MW of operational capacity per hour (multiply by    |
    | operational capacity and timepoint duration to get actual cost).        |
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

    m.FUEL_PRJ_SGMS = Set(
        dimen=2
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
            for _g, s in mod.FUEL_PRJ_SGMS
            if g in mod.FUEL_PRJS and g == _g)
    )

    m.VOM_PRJS_SGMS = Set(
        dimen=2,
        ordered=True
    )

    m.VOM_PRJS_OPR_TMPS_SGMS = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PRJ_OPR_TMPS
            for _g, s in mod.VOM_PRJS_SGMS
            if g == _g)
    )

    # Input Params
    ###########################################################################

    m.fuel = Param(
        m.FUEL_PRJS,
        within=m.FUELS
    )

    m.fuel_burn_slope_mmbtu_per_mwh = Param(
        m.FUEL_PRJ_SGMS,
        within=PositiveReals
    )

    m.fuel_burn_intercept_mmbtu_per_mw_hr = Param(
        m.FUEL_PRJ_SGMS,
        within=Reals
    )

    m.vom_slope_cost_per_mwh = Param(
        m.VOM_PRJS_SGMS,
        within=PositiveReals
    )

    m.vom_intercept_cost_per_mw_hr = Param(
        m.VOM_PRJS_SGMS,
        within=Reals
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """

    # Get column names as a few columns will be optional;
    # won't load data if column does not exist
    with open(os.path.join(scenario_directory, subproblem, stage, "inputs",
                           "projects.tab")
              ) as prj_file:
        reader = csv.reader(prj_file, delimiter="\t", lineterminator="\n")
        headers = next(reader)

    def determine_fuel_prj_sgms():
        # TODO: read_csv seems to fail silently if file not found; check and
        #  implement validation
        hr_df = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "heat_rate_curves.tab"),
            sep="\t"
        )

        pr_df = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "fuel"]
        )
        pr_df = pr_df[pr_df["fuel"] != "."]

        fuels_dict = dict(zip(pr_df["project"], pr_df["fuel"]))
        slope_dict = {}
        intercept_dict = {}
        for project in fuels_dict.keys():
            # read in the power setpoints and average heat rates
            hr_slice = hr_df[hr_df["project"] == project]
            hr_slice = hr_slice.sort_values(by=["load_point_fraction"])
            load_points = hr_slice["load_point_fraction"].values
            heat_rates = hr_slice["average_heat_rate_mmbtu_per_mwh"].values

            slopes, intercepts = calculate_slope_intercept(
                project, load_points, heat_rates
            )

            slope_dict.update(slopes)
            intercept_dict.update(intercepts)

        return fuels_dict, slope_dict, intercept_dict

    if "fuel" in headers:
        fuels_dict, slope_dict, intercept_dict = determine_fuel_prj_sgms()
        fuel_projects = list(fuels_dict.keys())
        fuel_project_segments = list(slope_dict.keys())

        data_portal.data()["FUEL_PRJS"] = {None: fuel_projects}
        data_portal.data()["FUEL_PRJ_SGMS"] = {None: fuel_project_segments}
        data_portal.data()["fuel"] = fuels_dict
        data_portal.data()["fuel_burn_slope_mmbtu_per_mwh"] = slope_dict
        data_portal.data()["fuel_burn_intercept_mmbtu_per_mw_hr"] = \
            intercept_dict

    # Variable OM curves
    vom_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "variable_om_curves.tab"),
        sep="\t"
    )

    slope_dict = {}
    intercept_dict = {}
    for project in vom_df["project"].unique():
        # read in the power setpoints and average heat rates
        vom_slice = vom_df[vom_df["project"] == project]
        vom_slice = vom_slice.sort_values(by=["load_point_fraction"])
        load_points = vom_slice["load_point_fraction"].values
        vom = vom_slice["average_variable_om_cost_per_mwh"].values

        slopes, intercepts = calculate_slope_intercept(
            project, load_points, vom
        )

        slope_dict.update(slopes)
        intercept_dict.update(intercepts)

    vom_project_segments = list(slope_dict.keys())

    data_portal.data()["VOM_PRJS_SGMS"] = {None: vom_project_segments}
    data_portal.data()["vom_slope_cost_per_mwh"] = slope_dict
    data_portal.data()["vom_intercept_cost_per_mw_hr"] = intercept_dict


def calculate_slope_intercept(project, load_points, heat_rates):
    """
    Calculates slope and intercept for a set of load points and corresponding
    average heat rates or variable O&M rates.
    Note that the intercept will be normalized to the
    operational capacity (Pmax) and the timepoint duration.
    :param project: the project name
    :param load_points: NumPy array with the loading points in fraction of Pmax
    :param heat_rates: NumPy array with the corresponding *average* heat rates
    in MMBtu per MWh or variable O&M in cost/MWh
    :return: (slope_dict, intercept_dict): Tuple with dictionary containing
    resp. the slope and intercepts, with (project, segement_ID) as the key.
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

    # calculate the slope and intercept for each pair of load points
    slope_dict = {}
    intercept_dict = {}
    # if just one point, assume constant heat rate (no intercept)
    if n_points == 1:
        slope_dict[(project, 0)] = heat_rates[0]
        intercept_dict[(project, 0)] = 0
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

        for i in range(n_points - 1):
            slope_dict[(project, i)] = slopes[i]
            intercept_dict[(project, i)] = intercepts[i]

    return slope_dict, intercept_dict


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
    proj_opchar = c.execute("""
        SELECT project, fuel,
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
        -- Get only the subset of projects in the portfolio with their 
        -- capacity types based on the project_portfolio_scenario_id 
        FROM (SELECT project, capacity_type
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
    c1 = conn.cursor()
    heat_rates = c1.execute(
        """
        SELECT project, fuel, heat_rate_curves_scenario_id, 
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

    # Get heat rate curves;
    # Select only variable OM curves of projects in the portfolio
    c3 = conn.cursor()
    variable_om = c3.execute(
        """
        SELECT project, load_point_fraction, average_variable_om_cost_per_mwh
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, variable_om_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        -- only select variable OM curves inputs with matching project and 
        -- vom_curves_scenario_id
        INNER JOIN
        inputs_project_variable_om_curves
        USING(project, variable_om_curves_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        AND variable_om_curves_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return proj_opchar, heat_rates, variable_om


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    heat_rate_curves.tab and variable_om_curves.tab files
    :param inputs_directory: local directory where .tab files will be saved
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
        "fuel", "min_stable_level_fraction", "unit_size_mw",
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
    append_to_projects_input_file(
        inputs_directory=inputs_directory,
        query_results=proj_opchar,
        new_columns=new_columns
    )

    # Convert heat rates to dataframes and pre-process data
    # (filter out only projects with fuel; select columns)
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )
    fuel_mask = pd.notna(hr_df["fuel"])
    columns = ["project", "load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
    heat_rates = hr_df[columns][fuel_mask].values

    with open(os.path.join(inputs_directory, "heat_rate_curves.tab"),
              "w", newline="") as \
            heat_rate_tab_file:
        writer = csv.writer(heat_rate_tab_file, delimiter="\t",
                            lineterminator="\n")

        writer.writerow(["project", "load_point_fraction",
                         "average_heat_rate_mmbtu_per_mwh"])

        for row in heat_rates:
            writer.writerow(row)

    with open(os.path.join(inputs_directory, "variable_om_curves.tab"),
              "w", newline="") as variable_om_tab_file:
        writer = csv.writer(variable_om_tab_file, delimiter="\t",
                            lineterminator="\n")

        writer.writerow(["project", "load_point_fraction",
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
    heat_rates, variable_om = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Convert input data into DataFrame
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )
    vom_df = pd.DataFrame(
        data=variable_om.fetchall(),
        columns=[s[0] for s in variable_om.description]
    )

    # Check data types heat_rates and variable_om:
    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    sub_hr_df = hr_df[hr_curve_mask][
        ["project", "load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
    ]
    vom_curve_mask = pd.notna(hr_df["variable_om_curves_scenario_id"])
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

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


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
    for project in pd.unique(hr_df["project"][relevant_mask]):
        # read in the power setpoints and average heat rates
        hr_slice = hr_df[hr_df["project"] == project]
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
    for project in pd.unique(vom_df["project"][load_point_mask]):
        # read in the power setpoints and average variable O&M
        vom_slice = vom_df[vom_df["project"] == project]
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
                        "Project(s) '{}': Variable O&M cost should be convex, "
                        "i.e. variable O&M rate should increase with "
                        "increasing load"
                        .format(project)
                    )

    return results
