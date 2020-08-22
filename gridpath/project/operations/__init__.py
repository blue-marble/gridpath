#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations** package contains modules to describe the
operational capabilities, constraints, and costs of generation, storage,
and demand-side infrastructure 'projects' in the optimization problem.

In this package, we also create the project fuel burn and cost components to
be passed downstream for aggregation into the system-level constraints and
the objective function.

In the `__init__` module of the package, we specify fuel burn and cost
parameters for each project. The project's operational type uses these
parameters to determine the projects will incur fuel burn and cost in each
operational timepoint. All parameters are optional, i.e. each type can be
used without fuel or variable cost for example. Conversely, the user needs
to ensure that the specified functionality makes sense for the project's
operational type, e.g. even if startup costs are specified for a gen_var
project, that operational type uses the default method for startup costs,
which returns 0, as variable generators do not have the concept of startup
(see the documentation in operational_types.__init__ for the defaults and in
each individual operational type module). When incompatible parameters are
specified for an operational type, GridPath will flag a validation error and
throw a warning (but not an error) at runtime.
"""

import numpy as np
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Any, NonNegativeReals, Reals, \
    PositiveReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_values, get_expected_dtypes, validate_dtypes, \
    validate_piecewise_curves, validate_startup_shutdown_rate_inputs
from gridpath.project.common_functions import append_to_input_file


def add_model_components(m, d):
    """
     The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`VAR_OM_COST_SIMPLE_PRJS`                                       |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which a simple variable O&M cost is specified.  |
    +-------------------------------------------------------------------------+
    | | :code:`VAR_OM_COST_CURVE_PRJS_PRDS_SGMS`                              |
    |                                                                         |
    | Three-dimensional set describing projects, their variable O&M cost      |
    | curve segment IDs, and the periods in which the project could be        |
    | operational.                                                            |
    +-------------------------------------------------------------------------+
    | | :code:`VAR_OM_COST_CURVE_PRJS`                                        |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which a variable O&M cost curve is specified.   |
    +-------------------------------------------------------------------------+
    | | :code:`VAR_OM_COST_ALL_PRJS`                                          |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which a simple variable O&M cost and/or a VOM   |
    | curve is specified.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_COST_SIMPLE_PRJS`                                      |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which a simple startup cost is specified.       |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_BY_ST_PRJS_TYPES`                                      |
    |                                                                         |
    | Two-dimensional set describing projects and their startup types.        |
    | Startup types are ordered from hottest to coldest, e.g. if there are 3  |
    | startup types the hottest start is indicated by 1, and the coldest      |
    | start is indicated by 3.                                                |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_BY_ST_PRJS`                                            |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which startup types are specified.              |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_COST_PRJS`                                             |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | All projects for which startup costs are specified (this is the union   |
    | STARTUP_COST_SIMPLE_PRJS and STARTUP_BY_ST_PRJS.                        |
    +-------------------------------------------------------------------------+
    | | :code:`SHUTDOWN_COST_PRJS`                                            |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which a shutdown cost is specified.             |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PRJS`                                                     |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of projects for which a fuel is specified.                      |
    +-------------------------------------------------------------------------+
    | | :code:`HR_CURVE_PRJS_PRDS_SGMS`                                     |
    |                                                                         |
    | Three-dimensional set describing projects, their heat rate curve        |
    | segment IDs, and the periods in which the project could be operational. |
    +-------------------------------------------------------------------------+
    | | :code:`HR_CURVE_PRJS`                                               |
    | | *Within*: :code:`FUEL_PRJS`                                           |
    |                                                                         |
    | The set of projects for which a heat rate curve is specified.           |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_FUEL_PRJS`                                             |
    | | *Within*: :code:`FUEL_PRJS`                                           |
    |                                                                         |
    | The set of projects for which startup fuel burn is specified.           |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`variable_om_cost_per_mwh`                                      |
    | | *Defined over*: :code:`VAR_OM_COST_SIMPLE_PRJS`                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's variable operations and maintenance cost per MWh of       |
    | power production.                                                       |
    +-------------------------------------------------------------------------+
    | | :code:`vom_slope_cost_per_mwh`                                        |
    | | *Defined over*: :code:`VAR_OM_COST_CURVE_PRJS_PRDS_SGMS`              |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear variable O&M     |
    | cost for each project's variable O&M cost segment in each operational   |
    | period. The units are cost of variable O&M per MWh of electricity       |
    | generation.                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`vom_intercept_cost_per_mw_hr`                                  |
    | | *Defined over*: :code:`VAR_OM_COST_CURVE_PRJS_PRDS_SGMS`              |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | This param describes the intercept of the piecewise linear variable O&M |
    | cost for each project's variable O&M cost segment in each operational   |
    | period. The units are cost of variable O&M per MW of operational        |
    | capacity per hour (multiply by operational capacity and timepoint       |
    | duration to get actual cost).                                           |
    +-------------------------------------------------------------------------+
    | | :code:`startup_cost_per_mw`                                           |
    | | *Defined over*: :code:`STARTUP_COST_SIMPLE_PRJS`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's startup cost per MW of capacity that is started up.       |
    +-------------------------------------------------------------------------+
    | | :code:`startup_cost_by_st_per_mw`                                     |
    | | *Defined over*: :code:`STARTUP_BY_ST_PRJS_TYPES`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's startup cost per MW of capacity that is started up for a  |
    | for a given startup type.                                               |
    +-------------------------------------------------------------------------+
    | | :code:`shutdown_cost_per_mw`                                          |
    | | *Defined over*: :code:`SHUTDOWN_COST_PRJS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's shutdown cost per MW of capacity that is shut down.       |
    +-------------------------------------------------------------------------+
    | | :code:`fuel`                                                          |
    | | *Defined over*: :code:`FUEL_PRJS`                                     |
    | | *Within*: :code:`Any`                                                 |
    |                                                                         |
    | The project's fuel. This will determine emissions (via the fuel's       |
    | carbon intensity) and fuel cost (via the fuel's price).                 |
    +-------------------------------------------------------------------------+
    | | :code:`shutdown_cost_per_mw`                                          |
    | | *Defined over*: :code:`HR_CURVE_PRJS_PRDS_SGMS`                     |
    | | *Within*: :code:`PositiveReals`                                       |
    |                                                                         |
    | This param describes the slope of the piecewise linear fuel burn for    |
    | each project's heat rate segment in each operational period. The units  |
    | are MMBtu of fuel burn per MWh of electricity generation.               |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_burn_intercept_mmbtu_per_mw_hr`                           |
    | | *Defined over*: :code:`HR_CURVE_PRJS_PRDS_SGMS`                     |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | This param describes the intercept of the piecewise linear fuel burn    |
    | for each project's heat rate segment in each operational period. The    |
    | units are MMBtu of fuel burn per MW of operational capacity per hour    |
    | (multiply by operational capacity and timepoint duration to get fuel    |
    | burn in MMBtu).                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`startup_fuel_mmbtu_per_mw`                                     |
    | | *Defined over*: :code:`STARTUP_FUEL_PRJS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fuel expenditure per MW started up.                       |
    +-------------------------------------------------------------------------+
    """

    # Sets
    ###########################################################################
    # Variable O&M cost projects (simple)
    m.VAR_OM_COST_SIMPLE_PRJS = Set(within=m.PROJECTS)

    # Variable O&M cost projects (by loading level)
    m.VAR_OM_COST_CURVE_PRJS_PRDS_SGMS = Set(
        dimen=3, ordered=True
    )
    m.VAR_OM_COST_CURVE_PRJS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: set(
            [prj for (prj, p, s) in mod.VAR_OM_COST_CURVE_PRJS_PRDS_SGMS]
        )
    )

    m.VAR_OM_COST_ALL_PRJS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: set(
            mod.VAR_OM_COST_SIMPLE_PRJS | mod.VAR_OM_COST_CURVE_PRJS
        )
    )

    # Startup cost projects (simple)
    m.STARTUP_COST_SIMPLE_PRJS = Set(within=m.PROJECTS)

    # Startup cost by startup type projects
    m.STARTUP_BY_ST_PRJS_TYPES = Set(dimen=2, ordered=True)
    m.STARTUP_BY_ST_PRJS = Set(
        initialize=lambda mod: set(
            [p for (p, t) in mod.STARTUP_BY_ST_PRJS_TYPES]
        )
    )

    # All startup cost projects
    m.STARTUP_COST_PRJS = Set(
        within=m.PROJECTS,
        initialize=lambda mod: set(
            [p for p in mod.STARTUP_COST_SIMPLE_PRJS ] +
            [p for p in mod.STARTUP_BY_ST_PRJS]
        )
    )

    # Shutdown cost projects
    m.SHUTDOWN_COST_PRJS = Set(within=m.PROJECTS)

    # Projects that burn fuel
    m.FUEL_PRJS = Set(within=m.PROJECTS)

    # Projects with heat rate curves (must be within FUEL_PRJS)
    m.HR_CURVE_PRJS_PRDS_SGMS = Set(dimen=3)

    m.HR_CURVE_PRJS = Set(
        within=m.FUEL_PRJS,
        initialize=lambda mod: set(
            [prj for (prj, p, s) in mod.HR_CURVE_PRJS_PRDS_SGMS]
        )
    )

    # Fuel projects that incur fuel burn on startup
    m.STARTUP_FUEL_PRJS = Set(within=m.FUEL_PRJS)

    # Optional Params
    ###########################################################################
    m.variable_om_cost_per_mwh = Param(
        m.VAR_OM_COST_SIMPLE_PRJS,
        within=NonNegativeReals
    )

    m.vom_slope_cost_per_mwh = Param(
        m.VAR_OM_COST_CURVE_PRJS_PRDS_SGMS,
        within=NonNegativeReals
    )

    m.vom_intercept_cost_per_mw_hr = Param(
        m.VAR_OM_COST_CURVE_PRJS_PRDS_SGMS,
        within=Reals
    )

    m.startup_cost_per_mw = Param(
        m.STARTUP_COST_SIMPLE_PRJS,
        within=NonNegativeReals
    )

    m.startup_cost_by_st_per_mw = Param(
        m.STARTUP_BY_ST_PRJS_TYPES,
        within=NonNegativeReals
    )

    m.shutdown_cost_per_mw = Param(
        m.SHUTDOWN_COST_PRJS,
        within=NonNegativeReals
    )

    m.fuel = Param(
        m.FUEL_PRJS,
        within=Any
    )
    
    m.fuel_burn_slope_mmbtu_per_mwh = Param(
        m.HR_CURVE_PRJS_PRDS_SGMS,
        within=PositiveReals
    )

    m.fuel_burn_intercept_mmbtu_per_mw_hr = Param(
        m.HR_CURVE_PRJS_PRDS_SGMS,
        within=Reals
    )

    m.startup_fuel_mmbtu_per_mw = Param(
        m.STARTUP_FUEL_PRJS,
        within=NonNegativeReals
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

        data_portal.data()["VAR_OM_COST_CURVE_PRJS_PRDS_SGMS"] = \
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

        data_portal.data()["STARTUP_BY_ST_PRJS_TYPES"] = \
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

        slope_dict, intercept_dict = \
            get_slopes_intercept_by_project_period_segment(
                hr_df, "average_heat_rate_mmbtu_per_mwh",
                fuel_projects, periods)

        fuel_project_segments = list(slope_dict.keys())

        data_portal.data()["HR_CURVE_PRJS_PRDS_SGMS"] \
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

    c2 = conn.cursor()
    heat_rates = c2.execute(
        """
        SELECT project, period,
        load_point_fraction, average_heat_rate_mmbtu_per_mwh
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, heat_rate_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_heat_rate_curves
        USING(project, heat_rate_curves_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {}
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    c3 = conn.cursor()
    vom_curves = c3.execute(
        """
        SELECT project, period,  
        load_point_fraction, average_variable_om_cost_per_mwh
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, variable_om_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        -- select only variable OM curves inputs with matching projects
        INNER JOIN
        inputs_project_variable_om_curves
        USING(project, variable_om_curves_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        AND variable_om_curves_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    c4 = conn.cursor()
    startup_chars = c4.execute(
        """
        SELECT project, 
        down_time_cutoff_hours, startup_plus_ramp_up_rate, startup_cost_per_mw
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, startup_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        INNER JOIN
        inputs_project_startup_chars
        USING(project, startup_chars_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        AND startup_chars_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return proj_opchar, heat_rates, vom_curves, startup_chars


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
    proj_opchar, heat_rate_curves, vom_curves, startup_chars = \
        get_inputs_from_database(subscenarios, subproblem, stage, conn)

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

    # Write heat rates file
    hr_df = cursor_to_df(heat_rate_curves)
    if not hr_df.empty:
        hr_df = hr_df.fillna(".")
        fpath = os.path.join(scenario_directory, str(subproblem), str(stage),
                             "inputs", "heat_rate_curves.tab")

        hr_df.to_csv(fpath, index=False, sep="\t")

    # Write VOM file
    vom_df = cursor_to_df(vom_curves)
    if not vom_df.empty:
        vom_df = vom_df.fillna(".")
        fpath = os.path.join(scenario_directory, str(subproblem), str(stage),
                             "inputs", "variable_om_curves.tab")
        vom_df.to_csv(fpath, index=False, sep="\t")

    # Write startup chars file
    su_df = cursor_to_df(startup_chars)
    if not su_df.empty:
        su_df = su_df.fillna(".")
        fpath = os.path.join(scenario_directory, str(subproblem), str(stage),
                             "inputs", "startup_chars.tab")
        su_df.to_csv(fpath, index=False, sep="\t")


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
    proj_opchar, heat_rates, vom_curves, startup_chars = \
        get_inputs_from_database(subscenarios, subproblem, stage, conn)

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

    # Convert input data into DataFrame
    hr_df = cursor_to_df(heat_rates)

    # Check data types heat_rates:
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_heat_rate_curves"]
    )
    dtype_errors, error_columns = validate_dtypes(hr_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_heat_rate_curves",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns in heat rates are non-negative
    numeric_columns = [c for c in hr_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_heat_rate_curves",
        severity="High",
        errors=validate_values(hr_df, valid_numeric_columns, min=0)
    )

    # TODO: make this work w new structure
    # Check for consistency between fuel and heat rate curve inputs:
    # Projects with fuel should have a heat rate scenario specified with
    # associated inputs in the hr curves table, and vice versa for projects
    # with no fuel.
    # fuel_mask = pd.notna(prj_df["fuel"])
    # prjs_w_fuel = prj_df["project"][fuel_mask]
    # prjs_wo_fuel = prj_df["project"][~fuel_mask]
    # prjs_w_hr = hr_df["project"].unique()  # prjs w hr inputs and matching hr id
    # write_validation_to_database(
    #     conn=conn,
    #     scenario_id=subscenarios.SCENARIO_ID,
    #     subproblem_id=subproblem,
    #     stage_id=stage,
    #     gridpath_module=__name__,
    #     db_table="inputs_project_operational_chars, inputs_project_heat_rate_curves",
    #     severity="High",
    #     errors=validate_idxs(actual_idxs=prjs_w_hr,
    #                          req_idxs=prjs_w_fuel,
    #                          invalid_idxs=prjs_wo_fuel,
    #                          msg="Projects with(out) fuel should (not) have "
    #                              "heat rate scenario specified, and should "
    #                              "(not) have inputs for that project-scenario "
    #                              "in the heat rate curves inputs table.")
    # )

    # Check that specified heat rate curves inputs are valid:
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_heat_rate_curves",
        severity="High",
        errors=validate_piecewise_curves(df=hr_df,
                                         x_col="load_point_fraction",
                                         slope_col="average_heat_rate_mmbtu_per_mwh",
                                         y_name="fuel burn")
    )

    # Validate VOM curves
    vom_df = cursor_to_df(vom_curves)

    # Check data types
    expected_dtypes = get_expected_dtypes(
        conn, ["inputs_project_variable_om_curves"]
    )

    dtype_errors, error_columns = validate_dtypes(vom_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_variable_om_curves",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns in variable OM are non-negative
    numeric_columns = [c for c in vom_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_variable_om_curves",
        severity="High",
        errors=validate_values(vom_df, valid_numeric_columns, min=0)
    )

    # Check that specified vom curves inputs are valid:
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_variable_om_curves",
        severity="High",
        errors=validate_piecewise_curves(df=vom_df,
                                         x_col="load_point_fraction",
                                         slope_col="average_variable_om_cost_per_mwh",
                                         y_name="variable O&M cost")
    )

    # Validate startup chars
    # Convert input data to DataFrame
    su_df = cursor_to_df(startup_chars)

    # Get the number of hours in the timepoint (take min if it varies)
    c = conn.cursor()
    tmp_durations = c.execute(
        """SELECT number_of_hours_in_timepoint
           FROM inputs_temporal
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {}
           AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    ).fetchall()
    hrs_in_tmp = min(tmp_durations)

    # Check startup shutdown rate inputs
    # TODO: figure out why we need the df in the validation and refactor this
    cols = [
        "project",
        "fuel",
        "variable_om_cost_per_mwh",
        "operational_type",
        "min_stable_level_fraction",
        "unit_size_mw",
        "startup_cost_per_mw", "shutdown_cost_per_mw",
        "startup_fuel_mmbtu_per_mw",
        "startup_plus_ramp_up_rate", "shutdown_plus_ramp_down_rate",
        "ramp_up_when_on_rate", "ramp_down_when_on_rate",
        "min_up_time_hours, min_down_time_hours",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours", "maximum_duration_hours",
        "aux_consumption_frac_capacity", "aux_consumption_frac_power"
    ]

    sql = """SELECT {}
        FROM inputs_project_portfolios
        INNER JOIN
        inputs_project_operational_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND project_operational_chars_scenario_id = {};
        """.format(
            ",".join(cols),
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
        )

    opchar_df = pd.read_sql(sql, conn)

    su_errors = validate_startup_shutdown_rate_inputs(
        opchar_df, su_df, hrs_in_tmp
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars, inputs_project_startup_chars",
        severity="High",
        errors=su_errors
    )

    # TODO: Check that specified vom scenarios actually have inputs in the vom
    #  table --> would need to get list of projects w vom curve scenario

    # TODO: check that if there is a "0" for the period for a given
    #  project there are zeroes everywhere for that project.

    # TODO: check that there is no overlap between simple and by-type
    #  startup cost


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
