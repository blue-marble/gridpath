#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations** package contains modules to describe the
operational capabilities, constraints, and costs of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.
"""

import numpy as np
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Any, NonNegativeReals, Reals, \
    PositiveReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_dtypes, get_expected_dtypes, validate_values
from gridpath.project.common_functions import append_to_input_file


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Variable O&M cost projects (simple)
    m.VAR_OM_COST_SIMPLE_PRJS = Set(within=m.PROJECTS)

    m.variable_om_cost_per_mwh = Param(
        m.VAR_OM_COST_SIMPLE_PRJS, within=NonNegativeReals
    )

    # Variable O&M cost projects (by loading level)
    m.VAR_OM_COST_BY_LL_PRJS_PRDS_SGMS = Set(
        dimen=3, ordered=True
    )
    m.VAR_OM_COST_BY_LL_PRJS = Set(
        initialize=lambda mod: set(
            [prj for (prj, p, s) in mod.VAR_OM_COST_BY_LL_PRJS_PRDS_SGMS]
        )
    )

    m.vom_slope_cost_per_mwh = Param(
        m.VAR_OM_COST_BY_LL_PRJS_PRDS_SGMS,
        within=NonNegativeReals
    )

    m.vom_intercept_cost_per_mw_hr = Param(
        m.VAR_OM_COST_BY_LL_PRJS_PRDS_SGMS,
        within=Reals
    )

    # Startup cost projects (simple)
    m.STARTUP_COST_SIMPLE_PRJS = Set(within=m.PROJECTS)

    m.startup_cost_per_mw = Param(
        m.STARTUP_COST_SIMPLE_PRJS, within=NonNegativeReals
    )

    # Startup cost by startup type projects
    m.STARTUP_COST_BY_ST_PRJS_TYPES = Set(dimen=2, ordered=True)
    m.STARTUP_COST_BY_ST_PRJS = Set(
        initialize=lambda mod: set(
            [p for (p, t) in mod.STARTUP_COST_BY_ST_PRJS_TYPES]
        )
    )

    m.startup_cost_by_st_per_mw = Param(
        m.STARTUP_COST_BY_ST_PRJS_TYPES, within=NonNegativeReals
    )

    # All startup cost projects
    m.STARTUP_COST_PRJS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: set(
            [p for p in mod.STARTUP_COST_SIMPLE_PRJS ] +
            [p for p in mod.STARTUP_COST_BY_ST_PRJS]
        )
    )

    # Shutdown cost projects
    m.SHUTDOWN_COST_PRJS = Set(within=m.PROJECTS)

    m.shutdown_cost_per_mw = Param(
        m.SHUTDOWN_COST_PRJS, within=NonNegativeReals
    )

    # Projects that burn fuel
    m.FUEL_PRJS = Set(within=m.PROJECTS)

    m.fuel = Param(m.FUEL_PRJS, within=Any)
    
    m.FUEL_BY_LL_PRJS_PRDS_SGMS = Set(dimen=3)
    
    m.FUEL_BY_LL_PRJS = Set(
        within=m.FUEL_PRJS,
        initialize=lambda mod: set(
            [prj for (prj, p, s) in mod.FUEL_BY_LL_PRJS_PRDS_SGMS]
        )
    )
    
    m.fuel_burn_slope_mmbtu_per_mwh = Param(
        m.FUEL_BY_LL_PRJS_PRDS_SGMS,
        within=PositiveReals
    )

    m.fuel_burn_intercept_mmbtu_per_mw_hr = Param(
        m.FUEL_BY_LL_PRJS_PRDS_SGMS,
        within=Reals
    )

    # Fuel projects that incur fuel burn on startup
    m.STARTUP_FUEL_PRJS = Set(within=m.FUEL_PRJS)

    m.startup_fuel_mmbtu_per_mw = Param(
        m.STARTUP_FUEL_PRJS, within=NonNegativeReals
    )


# Input-Output
###############################################################################

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
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "projects.tab"),
        select=("project", "variable_om_cost_per_mwh", "fuel",
                "startup_fuel_mmbtu_per_mw", "startup_cost_per_mw",
                "shutdown_cost_per_mw"),
        param=(m.variable_om_cost_per_mwh, m.fuel,
               m.startup_fuel_mmbtu_per_mw, m.startup_cost_per_mw,
               m.shutdown_cost_per_mw)
    )

    data_portal.data()['VAR_OM_COST_SIMPLE_PRJS'] = {
        None: list(data_portal.data()['variable_om_cost_per_mwh'].keys())
    }

    data_portal.data()['FUEL_PRJS'] = {
        None: list(data_portal.data()['fuel'].keys())
    }

    data_portal.data()['STARTUP_FUEL_PRJS'] = {
        None: list(data_portal.data()['startup_fuel_mmbtu_per_mw'].keys())
    }

    data_portal.data()['STARTUP_COST_SIMPLE_PRJS'] = {
        None: list(data_portal.data()['startup_cost_per_mw'].keys())
    }

    data_portal.data()['SHUTDOWN_COST_PRJS'] = {
        None: list(data_portal.data()['shutdown_cost_per_mw'].keys())
    }

    # VOM curves
    vom_curves_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "variable_om_curves.tab"
    )
    periods_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "periods.tab"
    )

    if os.path.exists(vom_curves_file):
        periods = pd.read_csv(periods_file, sep="\t")
        vom_df = pd.read_csv(vom_curves_file, sep="\t")

        periods = set(periods["period"])
        vom_projects = set(vom_df["project"].unique())

        slope_dict, intercept_dict = \
            get_slopes_intercept_by_project_period_segment(
                vom_df, "average_variable_om_cost_per_mwh",
                vom_projects, periods
            )
        vom_project_segments = list(slope_dict.keys())

        data_portal.data()["VAR_OM_COST_BY_LL_PRJS_PRDS_SGMS"] = \
            {None: vom_project_segments}
        data_portal.data()["vom_slope_cost_per_mwh"] = \
            slope_dict
        data_portal.data()["vom_intercept_cost_per_mw_hr"] = \
            intercept_dict

    # Startup chars
    startup_chars_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "startup_chars.tab"
    )

    if os.path.exists(startup_chars_file):
        df = pd.read_csv(startup_chars_file, sep="\t")

        # Note: the rank function requires at least one numeric input in the
        # down_time_cutoff_hours column (can't be all NULL/None).
        if len(df) > 0:
            df["startup_type_id"] = df.groupby("project")[
                "down_time_cutoff_hours"].rank()

        startup_ramp_projects_types = list()
        startup_cost_dict = dict()
        for i, row in df.iterrows():
            project = row["project"]
            startup_type_id = row["startup_type_id"]
            startup_cost = row["startup_cost_per_mw"]

            startup_ramp_projects_types.append((project, startup_type_id))
            startup_cost_dict[(project, startup_type_id)] = \
                float(startup_cost)

        data_portal.data()["STARTUP_COST_BY_ST_PRJS_TYPES"] = \
            {None: startup_ramp_projects_types}
        data_portal.data()["startup_cost_by_st_per_mw"] = startup_cost_dict
        
    # HR curves
    
    hr_curves_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "heat_rate_curves.tab"
    )
    periods_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "periods.tab"
    )
    projects_file = os.path.join(
        scenario_directory, str(subproblem), str(stage),
        "inputs", "projects.tab"
    )

    # Get column names as a few columns will be optional;
    # won't load data if fuel column does not exist
    headers = pd.read_csv(projects_file, nrows=0, sep="\t").columns
    if os.path.exists(hr_curves_file) and "fuel" in headers:

        hr_df = pd.read_csv(hr_curves_file, sep="\t")
        projects = set(hr_df["project"].unique())
        
        periods_df = pd.read_csv(periods_file, sep="\t")
        pr_df = pd.read_csv(projects_file, sep="\t", usecols=["project", "fuel"])
        pr_df = pr_df[(pr_df["fuel"] != ".") & (pr_df["project"].isin(projects))]

        periods = set(periods_df["period"])
        fuel_projects = pr_df["project"].unique()
        fuels_dict = dict(zip(projects, pr_df["fuel"]))

        slope_dict, intercept_dict = \
            get_slopes_intercept_by_project_period_segment(
                hr_df, "average_heat_rate_mmbtu_per_mwh",
                fuel_projects, periods)

        fuel_project_segments = list(slope_dict.keys())

        data_portal.data()["FUEL_BY_LL_PRJS_PRDS_SGMS"] \
            = {None: fuel_project_segments}
        data_portal.data()["fuel_burn_slope_mmbtu_per_mwh"] = slope_dict
        data_portal.data()["fuel_burn_intercept_mmbtu_per_mw_hr"] = \
            intercept_dict


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
        SELECT project, fuel, variable_om_cost_per_mwh,
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

    return proj_opchar


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model inputs
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    proj_opchar = get_inputs_from_database(
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

    # Get the project input data
    proj_opchar = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Convert input data into DataFrame
    prj_df = cursor_to_df(proj_opchar)

    # Check data types operational chars:
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_operational_chars"]
    )

    dtype_errors, error_columns = validate_dtypes(prj_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in prj_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_values(prj_df, valid_numeric_columns, min=0)
    )

    # Check min_stable_level_fraction within (0, 1]
    if "min_stable_level_fraction" not in error_columns:
        write_validation_to_database(
            conn=conn,
            scenario_id=subscenarios.SCENARIO_ID,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_operational_chars",
            severity="Mid",
            errors=validate_values(prj_df, ["min_stable_level_fraction"],
                                   min=0, max=1, strict_min=True)
        )


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
