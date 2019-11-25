#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations** package contains modules to describe the
operational capabilities, constraints, and costs of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.
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

    # ----------------------- SHUTDOWN ----------------------- #

    # 1. Sets
    m.SHUTDOWN_COST_PROJECTS = Set(within=m.PROJECTS)

    m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.SHUTDOWN_COST_PROJECTS)
    )

    # 2. Params
    m.shutdown_cost_per_mw = Param(m.SHUTDOWN_COST_PROJECTS,
                                   within=PositiveReals)

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

    # ------------------------ STARTUP ---------------------- #
    # with optional multiple types (hottest to coldest)

    # 1. Sets

    # TODO: need to add this to load_data too.
    m.STARTUP_RAMP_PROJECTS = Set(within=m.PROJECTS)
    m.STARTUP_COST_PROJECTS = Set(within=m.PROJECTS)
    m.STARTUP_FUEL_PROJECTS = Set(within=m.FUEL_PROJECTS)

    m.PROJECT_STARTUP_TYPES = Set(dimen=2, ordered=True)

    # m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS = \
    #     Set(dimen=2,
    #         rule=lambda mod:
    #         set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
    #             if g in mod.STARTUP_FUEL_PROJECTS))

    # m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS = \
    #     Set(dimen=2,
    #         rule=lambda mod:
    #         set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
    #             if g in mod.STARTUP_COST_PROJECTS))

    m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES = Set(
        dimen=3,
        rule=lambda mod:
            set((g, tmp, l) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                for _g, l in mod.PROJECT_STARTUP_TYPES
                if (g == _g and g in mod.STARTUP_COST_PROJECTS))
    )

    m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES = Set(
        dimen=3,
        rule=lambda mod:
            set((g, tmp, l) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                for _g, l in mod.PROJECT_STARTUP_TYPES
                if (g == _g and g in mod.STARTUP_FUEL_PROJECTS))
    )

    m.STARTUP_RAMP_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES = Set(
        dimen=3,
        rule=lambda mod:
            set((g, tmp, l) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                for _g, l in mod.PROJECT_STARTUP_TYPES
                if (g == _g and g in mod.STARTUP_RAMP_PROJECTS))
    )

    def get_startup_types_by_project(mod, g):
        """
        Get indexed set of startup types by project, ordered from hottest to
        coldest.
        :param mod:
        :param g:
        :return:
        """
        types = list(l for (_g, l) in mod.PROJECT_STARTUP_TYPES if g == _g)
        return types

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
    # TODO: define narrow set of project_startup_ramp_types etc.?
    #  Need to be able to have projects with no startup costs
    #  is it okay to have the startup cost to be defined by the more wide set
    #  PROJECT_STARTUP_TYPES but then only use it for the more narrow set of
    #  STARTUP_COST_PROJECTS?
    m.down_time_hours = Param(
        m.PROJECT_STARTUP_TYPES, within=NonNegativeReals)
    m.startup_ramp = Param(
        m.PROJECT_STARTUP_TYPES, within=PercentFraction)
    m.startup_cost_per_mw = Param(
        m.PROJECT_STARTUP_TYPES, within=PositiveReals)
    m.startup_fuel_mmbtu_per_mw = Param(
        m.PROJECT_STARTUP_TYPES, within=PositiveReals)


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

    # TODO: what if there are some "." inputs. Wouldn't this lead to string
    #  datatype and bad interpretation of these inputs?
    #  We could have "." inputs if we want say, startup ramps, but no startup
    #  costs.
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "startup_ramps.tab"),
        select=("project",	"startup_type_id",
                "down_time_hours",
                "startup_ramp",
                "startup_cost_per_mw",
                "startup_fuel_mmbtu_per_mw"),
        index=m.PROJECT_STARTUP_TYPES,
        param=(m.down_time_hours, m.startup_ramp,
               m.startup_cost_per_mw, m.startup_fuel_mmbtu_per_mw)
    )
    # TODO: doesn't work with empty DF?
    #  is it because of the load function? empty index shuld work but perhaps
    #  we need the right dimension. Now it is None, but it should be
    #  (None, None)?

    # Get column names as a few columns will be optional;
    # won't load data if column does not exist
    with open(os.path.join(scenario_directory, subproblem, stage, "inputs",
                           "projects.tab")
              ) as prj_file:
        reader = csv.reader(prj_file, delimiter="\t")
        headers = next(reader)

    # STARTUP_RAMP_PROJECTS
    def determine_startup_ramp_projects():
        """
        If numeric values greater than 0 for startup ramps are specified
        for some generators, add those generators to the STARTUP_RAMP_PROJECTS
        subset
        :return:
        """
        startup_ramp_projects = list()

        # TODO: make sure we can deal with empty table or another way to skip
        #  this if no inputs (no input file at all?). Since db table has the
        #  columns, setting up logic to deal with columns possibly not being
        #  there seems less ideal?
        #  should we check validity of the down time duration here too?
        df = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "startup_ramps.tab"),
            sep="\t",
            usecols=["project", "startup_ramp"]
        )
        for row in zip(df["project"],
                       df["startup_ramp"]):
            if is_number(row[1]) and row[0] not in startup_ramp_projects:
                startup_ramp_projects.append(row[0])
            else:
                pass

        return startup_ramp_projects

    data_portal.data()["STARTUP_RAMP_PROJECTS"] = \
        {None: determine_startup_ramp_projects()}

    # STARTUP_COST_PROJECTS
    def determine_startup_cost_projects():
        """
        If numeric values greater than 0 for startup costs are specified
        for some generators, add those generators to the STARTUP_COST_PROJECTS
        subset
        :return:
        """
        startup_cost_projects = list()

        # TODO: make sure we can deal with empty table or another way to skip
        #  this if no inputs (no input file at all?). Since db table has the
        #  columns, setting up logic to deal with columns possibly not being
        #  there seems less ideal?
        #  should we check validity of the duration here too?
        df = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "startup_ramps.tab"),
            sep="\t",
            usecols=["project", "startup_cost_per_mw"]
        )
        for row in zip(df["project"],
                       df["startup_cost_per_mw"]):
            if (is_number(row[1]) and float(row[1]) > 0
                    and row[0] not in startup_cost_projects):
                startup_cost_projects.append(row[0])
            else:
                pass

        return startup_cost_projects

    data_portal.data()["STARTUP_COST_PROJECTS"] = \
        {None: determine_startup_cost_projects()}

    # STARTUP FUEL_PROJECTS
    def determine_startup_fuel_projects():
        """
        E.g. generators that incur fuel burn when starting up. Note: if we
        already are setting a startup ramp trajectory, we can't have a startup
        fuel too since this would be double counting!
        :return:
        """
        startup_fuel_projects = list()

        # TODO: Should we first check whether this is a fuel project?
        df = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "startup_ramps.tab"),
            sep="\t",
            usecols=["project", "startup_fuel_mmbtu_per_mw"]
        )

        for row in zip(df["project"],
                       df["startup_fuel_mmbtu_per_mw"]):
            if row[1] != "." and row[0] not in startup_fuel_projects:
                startup_fuel_projects.append(row[0])
            else:
                pass

        return startup_fuel_projects

    data_portal.data()["STARTUP_FUEL_PROJECTS"] = \
        {None: determine_startup_fuel_projects()}

    # SHUTDOWN_COST_PROJECTS
    def determine_shutdown_cost_projects():
        """
        If numeric values greater than 0 for shutdown costs are specified
        for some generators, add those generators to the
        SHUTDOWN_COST_PROJECTS subset and initialize the respective shutdown
        cost param value
        :return:
        """

        shutdown_cost_projects = list()
        shutdown_cost_per_mw = dict()

        dynamic_components = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "shutdown_cost_per_mw"]
        )
        for row in zip(dynamic_components["project"],
                       dynamic_components["shutdown_cost_per_mw"]):
            if is_number(row[1]) and float(row[1]) > 0:
                shutdown_cost_projects.append(row[0])
                shutdown_cost_per_mw[row[0]] = float(row[1])
            else:
                pass

        return shutdown_cost_projects, shutdown_cost_per_mw

    if "shutdown_cost_per_mw" in headers:
        data_portal.data()["SHUTDOWN_COST_PROJECTS"] = {
            None: determine_shutdown_cost_projects()[0]
        }

        data_portal.data()["shutdown_cost_per_mw"] = \
            determine_shutdown_cost_projects()[1]

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
        data_portal.data()["fuel_burn_slope_mmbtu_per_mwh"] = \
            slope_dict
        data_portal.data()["fuel_burn_intercept_mmbtu_per_hr"] = \
            intercept_dict


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
    c = conn.cursor()
    heat_rates = c.execute(
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

    return heat_rates


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
    heat_rates = get_inputs_from_database(
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
    heat_rates = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

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
