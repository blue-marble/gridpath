#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations** package contains modules to describe the
operational capabilities, constraints, and costs of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.

*startup_ramp* \ :sub:`g, l`\ -- the project's upward ramp rate limit during
startup of type l, defined as a fraction of its capacity per minute. If this
param, adjusted for timepoint duration, is smaller than
*min_stable_level_fraction*, the unit will have a startup trajectory spanning
multiple timepoints. \n

"""

# changes made:
# 1. split out start and stop expression since there can now be multiple
# starts

from builtins import next
from builtins import zip
import csv
from pandas import read_csv
import numpy as np
import pandas as pd
import os.path
from pyomo.environ import Set, Param, PositiveReals, Reals, NonNegativeReals, \
    PercentFraction
from gridpath.auxiliary.auxiliary import is_number, check_dtypes, \
    get_expected_dtypes, check_column_sign_positive, \
    write_validation_to_database

# TODO validation:
#  make sure that if one of the startup types entries for a project has "."
#  inputs, that all startup types for that project have it


# TODO: should we take this out of __init__.py
#   can we create operations.py like we have capacity.py and put it there?
def add_model_components(m, d):
    """
    :param m:
    :param d:
    :return:
    """

    # ---------------------- FUELS -------------------------- #

    # TODO: implement check for which generator types can have fuels
    # TODO: re-think how to deal with fuel projects; it's awkward to import
    #  fuel & heat rate params here, but use them in the operational_type
    #  modules with an 'if in FUEL_PROJECTS'
    # 1. Sets
    m.FUEL_PROJECTS = Set(within=m.PROJECTS)
    m.FUEL_PROJECT_SEGMENTS = Set(dimen=2)

    m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FUEL_PROJECTS))

    m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            for _g, s in mod.FUEL_PROJECT_SEGMENTS
            if g in mod.FUEL_PROJECTS and g == _g)
    )

    # 2. Params
    m.fuel = Param(m.FUEL_PROJECTS, within=m.FUELS)
    m.fuel_burn_intercept_mmbtu_per_hr = Param(
        m.FUEL_PROJECT_SEGMENTS, within=Reals)
    m.fuel_burn_slope_mmbtu_per_mwh = Param(
        m.FUEL_PROJECT_SEGMENTS, within=PositiveReals)

    # ----------------------- SHUTDOWN ----------------------- #

    # 1. Sets
    m.SHUTDOWN_COST_PROJECTS = Set(within=m.PROJECTS)
    m.SHUTDOWN_FUEL_PROJECTS = Set(within=m.FUEL_PROJECTS)
    m.SHUTDOWN_PROJECTS = m.SHUTDOWN_COST_PROJECTS | m.SHUTDOWN_FUEL_PROJECTS

    m.SHUTDOWN_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.SHUTDOWN_PROJECTS)
    )

    m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.SHUTDOWN_PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.SHUTDOWN_COST_PROJECTS)
    )

    m.SHUTDOWN_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.SHUTDOWN_PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.SHUTDOWN_FUEL_PROJECTS)
    )

    # 2. Params
    m.shutdown_cost_per_mw = Param(
        m.SHUTDOWN_COST_PROJECTS, within=NonNegativeReals
    )
    m.shutdown_fuel_mmbtu_per_mw = Param(
        m.SHUTDOWN_FUEL_PROJECTS, within=NonNegativeReals
    )

    # ------------------------ STARTUP ---------------------- #
    # with optional multiple types (hottest to coldest)

    # 1. Sets

    m.STARTUP_PROJECTS = Set(within=m.PROJECTS)
    m.STARTUP_RAMP_PROJECTS = Set(within=m.STARTUP_PROJECTS)
    m.STARTUP_COST_PROJECTS = Set(within=m.STARTUP_PROJECTS)
    m.STARTUP_FUEL_PROJECTS = Set(within=m.STARTUP_PROJECTS & m.FUEL_PROJECTS)

    m.STARTUP_PROJECTS_TYPES = Set(dimen=2, ordered=True)
    m.STARTUP_RAMP_PROJECTS_TYPES = Set(dimen=2, ordered=True)
    m.STARTUP_COST_PROJECTS_TYPES = Set(dimen=2, ordered=True)
    m.STARTUP_FUEL_PROJECTS_TYPES = Set(dimen=2, ordered=True)

    m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.STARTUP_COST_PROJECTS)
    )

    m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.STARTUP_FUEL_PROJECTS)
    )

    m.STARTUP_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES = Set(
        dimen=3,
        rule=lambda mod:
            set((g, tmp, s) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                for _g, s in mod.STARTUP_PROJECTS_TYPES
                if (g == _g))
    )

    m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES = Set(
        dimen=3,
        rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.STARTUP_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES
                if g in mod.STARTUP_COST_PROJECTS)
    )

    m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES = Set(
        dimen=3,
        rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.STARTUP_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES
                if g in mod.STARTUP_FUEL_PROJECTS)
    )

    def get_startup_types_by_project(mod, g):
        """
        Get indexed set of startup types by project, ordered from hottest to
        coldest.
        :param mod:
        :param g:
        :return:
        """
        types = list(s for (_g, s) in mod.STARTUP_PROJECTS_TYPES if g == _g)
        return types

    # TODO: change 'initalize' to 'rule' to be consistent?
    m.STARTUP_TYPES_BY_STARTUP_PROJECT = Set(
        m.STARTUP_PROJECTS,
        initialize=get_startup_types_by_project,
        ordered=True
    )

    m.STARTUP_TYPES_BY_STARTUP_RAMP_PROJECT = Set(
        m.STARTUP_RAMP_PROJECTS,
        initialize=get_startup_types_by_project,
        ordered=True
    )

    m.STARTUP_TYPES_BY_STARTUP_COST_PROJECT = Set(
        m.STARTUP_COST_PROJECTS,
        initialize=get_startup_types_by_project,
        ordered=True
    )

    m.STARTUP_TYPES_BY_STARTUP_FUEL_PROJECT = Set(
        m.STARTUP_FUEL_PROJECTS,
        initialize=get_startup_types_by_project,
        ordered=True
    )

    # 2. Params
    m.down_time_hours = Param(
        m.STARTUP_PROJECTS_TYPES, within=NonNegativeReals)
    m.startup_ramp_rate = Param(
        m.STARTUP_RAMP_PROJECTS_TYPES, within=PercentFraction)
    m.startup_cost_per_mw = Param(
        m.STARTUP_COST_PROJECTS_TYPES, within=NonNegativeReals)
    m.startup_fuel_mmbtu_per_mw = Param(
        m.STARTUP_FUEL_PROJECTS_TYPES, within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Get column names as a few columns will be optional;
    # won't load data if column does not exist
    with open(os.path.join(scenario_directory, subproblem, stage, "inputs",
                           "projects.tab")
              ) as prj_file:
        reader = csv.reader(prj_file, delimiter="\t")
        headers = next(reader)

    # SHUTDOWN PROJECTS
    df = read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
    )

    shutdown_cost_projects = set()
    shutdown_fuel_projects = set()

    shutdown_costs = dict()
    shutdown_fuel_mmbtus = dict()

    shutdown_cost_bool = ("shutdown_cost_per_mw" in headers)
    shutdown_fuel_bool = ("shutdown_fuel_mmbtu_per_mw" in headers)
    for i, row in df.iterrows():
        project = row["project"]
        if shutdown_cost_bool:
            shutdown_cost_per_mw = row["shutdown_cost_per_mw"]
            if shutdown_cost_per_mw != ".":
                shutdown_cost_projects.add(project)
                shutdown_costs[project] = float(shutdown_cost_per_mw)
                # WARNING: obscure Pyomo error without the float wrapper!
        if shutdown_fuel_bool:
            shutdown_fuel_mmbtu_per_mw = row["shutdown_fuel_mmbtu_per_mw"]
            if shutdown_fuel_mmbtu_per_mw != ".":
                shutdown_fuel_projects.add(project)
                shutdown_fuel_mmbtus[project] = float(shutdown_fuel_mmbtu_per_mw)

    if shutdown_cost_projects:
        data_portal.data()["SHUTDOWN_COST_PROJECTS"] = \
            {None: shutdown_cost_projects}
        data_portal.data()["shutdown_cost_per_mw"] = shutdown_costs
    if shutdown_fuel_projects:
        data_portal.data()["SHUTDOWN_FUEL_PROJECTS"] = \
            {None: shutdown_fuel_projects}
        data_portal.data()["shutdown_fuel_mmbtu_per_mw"] = shutdown_fuel_mmbtus

    # STARTUP_PROJECTS
    df = read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "startup_chars.tab"),
        sep="\t"
    )

    startup_projects = set()
    startup_ramp_projects = set()
    startup_cost_projects = set()
    startup_fuel_projects = set()

    startup_projects_types = list()
    startup_ramp_projects_types = list()
    startup_cost_projects_types = list()
    startup_fuel_projects_types = list()

    down_time_hours_dict = dict()
    startup_ramps = dict()
    startup_costs = dict()
    startup_fuel_mmbtus = dict()

    for i, row in df.iterrows():
        project = row["project"]
        startup_type_id = row["startup_type_id"]
        down_time_hours = row["down_time_hours"]
        startup_plus_ramp_up_rate = row["startup_plus_ramp_up_rate"]
        startup_cost_per_mw = row["startup_cost_per_mw"]
        startup_fuel_mmbtu_per_mw = row["startup_fuel_mmbtu_per_mw"]

        if down_time_hours != ".":
            startup_projects.add(project)
            startup_projects_types.append((project, startup_type_id))
            down_time_hours_dict[(project, startup_type_id)] = \
                float(down_time_hours)
        if startup_plus_ramp_up_rate != ".":
            startup_ramp_projects.add(project)
            startup_ramp_projects_types.append((project, startup_type_id))
            startup_ramps[(project, startup_type_id)] = \
                float(startup_plus_ramp_up_rate)
        if startup_cost_per_mw != ".":
            startup_cost_projects.add(project)
            startup_cost_projects_types.append((project, startup_type_id))
            startup_costs[(project, startup_type_id)] = \
                float(startup_cost_per_mw)
        if startup_fuel_mmbtu_per_mw != ".":
            startup_fuel_projects.add(project)
            startup_fuel_projects_types.append((project, startup_type_id))
            startup_fuel_mmbtus[(project, startup_type_id)] = \
                float(startup_fuel_mmbtu_per_mw)

    if startup_projects:
        data_portal.data()["STARTUP_PROJECTS"] = {None: startup_projects}
        data_portal.data()["STARTUP_PROJECTS_TYPES"] = \
            {None: startup_projects_types}
        data_portal.data()["down_time_hours"] = down_time_hours_dict

    if startup_ramp_projects:
        data_portal.data()["STARTUP_RAMP_PROJECTS"] = \
            {None: startup_ramp_projects}
        data_portal.data()["STARTUP_RAMP_PROJECTS_TYPES"] = \
            {None: startup_ramp_projects_types}
        data_portal.data()["startup_ramp_rate"] = startup_ramps

    if startup_cost_projects:
        data_portal.data()["STARTUP_COST_PROJECTS"] = \
            {None: startup_cost_projects}
        data_portal.data()["STARTUP_COST_PROJECTS_TYPES"] = \
            {None: startup_cost_projects_types}
        data_portal.data()["startup_cost_per_mw"] = startup_costs

    if startup_fuel_projects:
        data_portal.data()["STARTUP_FUEL_PROJECTS"] = \
            {None: startup_fuel_projects}
        data_portal.data()["STARTUP_FUEL_PROJECTS_TYPES"] = \
            {None: startup_fuel_projects_types}
        data_portal.data()["startup_fuel_mmbtu_per_mw"] = startup_fuel_mmbtus

    # FUEL_PROJECT_SEGMENTS
    def determine_fuel_project_segments():
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
            hr_slice = hr_slice.sort_values(by=["load_point_mw"])
            load_points = hr_slice["load_point_mw"].values
            heat_rates = hr_slice["average_heat_rate_mmbtu_per_mwh"].values

            slopes, intercepts = calculate_heat_rate_slope_intercept(
                project, load_points, heat_rates
            )

            slope_dict.update(slopes)
            intercept_dict.update(intercepts)

        return fuels_dict, slope_dict, intercept_dict

    if "fuel" in headers:
        fuels_dict, slope_dict, intercept_dict = \
            determine_fuel_project_segments()
        fuel_projects = list(fuels_dict.keys())
        fuel_project_segments = list(slope_dict.keys())

        data_portal.data()["FUEL_PROJECTS"] = \
            {None: fuel_projects}
        data_portal.data()["FUEL_PROJECT_SEGMENTS"] = \
            {None: fuel_project_segments}
        data_portal.data()["fuel"] = fuels_dict
        data_portal.data()["fuel_burn_slope_mmbtu_per_mwh"] = slope_dict
        data_portal.data()["fuel_burn_intercept_mmbtu_per_hr"] = intercept_dict


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Get heat rate curves;
    # Select only heat rate curves of projects in the portfolio
    c1 = conn.cursor()
    heat_rates = c1.execute(
        """
        SELECT project, fuel, heat_rate_curves_scenario_id, 
        load_point_mw, average_heat_rate_mmbtu_per_mwh
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

    c2 = conn.cursor()
    startup_chars = c2.execute(
        """
        SELECT project, startup_chars_scenario_id, 
        startup_type_id, down_time_hours, startup_plus_ramp_up_rate, 
        startup_cost_per_mw, startup_fuel_mmbtu_per_mw
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, startup_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) AS op_char
        USING(project)
        LEFT OUTER JOIN
        inputs_project_startup_chars
        USING(project, startup_chars_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return heat_rates, startup_chars


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
    heat_rates, startup_chars = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Convert input data into DataFrame
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )

    # Check data types heat_rates:
    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    sub_hr_df = hr_df[hr_curve_mask][
        ["project", "load_point_mw", "average_heat_rate_mmbtu_per_mwh"]
    ]

    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_portfolios", "inputs_project_operational_chars",
               "inputs_project_heat_rate_curves"]
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
             "Invalid/Missing heat rate curves inputs",
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
    1. Check that specified heat rate scenarios actually have inputs in the heat
       rate curves table
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
    load_point_mask = pd.notna(hr_df["load_point_mw"])

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
        hr_slice = hr_slice.sort_values(by=["load_point_mw"])
        load_points = hr_slice["load_point_mw"].values
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
                        "Project(s) '{}': Total fuel burn should increase with increasing load"
                        .format(project)
                    )
                if np.any(np.diff(slopes) <= 0):
                    results.append(
                        "Project(s) '{}': Fuel burn should be convex, i.e. marginal heat rate should increase with increading load"
                        .format(project)
                    )

    return results


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    heat_rate_curves.tab files
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    heat_rates, startup_chars = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # HEAT RATES
    # Convert heat rates to dataframes and pre-process data
    # (filter out only projects with fuel; select columns)
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )
    fuel_mask = pd.notna(hr_df["fuel"])
    columns = ["project", "load_point_mw", "average_heat_rate_mmbtu_per_mwh"]
    heat_rates = hr_df[columns][fuel_mask].values

    with open(os.path.join(inputs_directory, "heat_rate_curves.tab"),
              "w", newline="") as \
            heat_rate_tab_file:
        writer = csv.writer(heat_rate_tab_file, delimiter="\t")

        writer.writerow(["project", "load_point_mw",
                         "average_heat_rate_mmbtu_per_mwh"])

        for row in heat_rates:
            writer.writerow(row)

    # STARTUP CHARS
    with open(os.path.join(inputs_directory, "startup_chars.tab"),
              "w", newline="") as \
            start_chars_tab_file:
        writer = csv.writer(start_chars_tab_file, delimiter="\t")

        writer.writerow(["project", "startup_type_id", "down_time_hours",
                         "startup_plus_ramp_up_rate", "startup_cost_per_mw",
                         "startup_fuel_mmbtu_per_mw"])

        for row in startup_chars:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def calculate_heat_rate_slope_intercept(project, load_points, heat_rates):
    """
    Calculates slope and intercept for a set of load points and corresponding
    average heat rates.
    :param project: the project name
    :param load_points: NumPy array with the loading points in MW
    :param heat_rates: NumPy array with the corresponding heat rates in MMBtu
    per MWh
    :return:
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
                Load points in heat rate curve should be strictly
                increasing. Check heat rate curve inputs for project '{}'.
                """.format(project)
            )
        if np.any(incr_fuel_burn <= 0):
            raise ValueError(
                """
                Total fuel burn should be strictly increasing between
                load points. Check heat rate curve inputs for project '{}'.
                """.format(project)
            )
        if np.any(np.diff(slopes) <= 0):
            raise ValueError(
                """
                The fuel burn as a function of power output should be
                a convex function, i.e. the incremental heat rate should
                be positive and strictly increasing. Check heat rate
                curve inputs for project '{}'.
                """.format(project)
            )

        for i in range(n_points - 1):
            slope_dict[(project, i)] = slopes[i]
            intercept_dict[(project, i)] = intercepts[i]

    return slope_dict, intercept_dict
