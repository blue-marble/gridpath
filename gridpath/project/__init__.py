#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import required_capacity_modules, \
    required_operational_modules, headroom_variables, footroom_variables


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    project_dynamic_data = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project",
                               "capacity_type",
                               "operational_type"]
        )

    # Required modules are the unique set of generator capacity types
    # This list will be used to know which operational modules to load
    setattr(d, required_capacity_modules,
            project_dynamic_data.capacity_type.unique()
            )

    # Required operational modules
    # Will be determined based on operational_types specified in the data
    # (in projects.tab)
    setattr(d, required_operational_modules,
            project_dynamic_data.operational_type.unique()
            )

    # From here on, the dynamic components will be further populated by the
    # modules
    # Reserve variables
    # Will be determined based on whether the user has specified the
    # respective reserve module AND based on whether a reserve zone is
    # specified for a project in projects.tab
    # We need to make the dictionaries first; it is the lists for each key
    # that are populated by the modules
    setattr(d, headroom_variables,
            {r: [] for r in project_dynamic_data.project}
            )
    setattr(d, footroom_variables,
            {r: [] for r in project_dynamic_data.project}
            )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.PROJECTS = Set()
    m.load_zone = Param(m.PROJECTS, within=m.LOAD_ZONES)
    m.capacity_type = Param(m.PROJECTS)
    m.operational_type = Param(m.PROJECTS)

    # Variable O&M cost
    # TODO: all projects have this for now; is that what makes the most sense?
    m.variable_om_cost_per_mwh = Param(m.PROJECTS, within=NonNegativeReals)

    # Technology
    # This is only used for aggregation purposes in results
    m.technology = Param(m.PROJECTS, default="unspecified")


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     index=m.PROJECTS,
                     select=("project", "load_zone", "capacity_type",
                             "operational_type", "variable_om_cost_per_mwh"),
                     param=(m.load_zone, m.capacity_type,
                            m.operational_type, m.variable_om_cost_per_mwh)
                     )

    # Technology column is optional (default param value is 'unspecified')
    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    if "technology" in header:
        data_portal.load(filename=os.path.join(scenario_directory,
                                               "inputs", "projects.tab"),
                         select=("project", "technology"),
                         param=m.technology
                         )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_tab_file:
        writer = csv.writer(projects_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "capacity_type", "operational_type", "technology",
             "load_zone", "fuel", "variable_om_cost_per_mwh",
             "minimum_input_mmbtu_per_hr", "inc_heat_rate_mmbtu_per_mwh",
             "min_stable_level_fraction", "unit_size_mw",
             "startup_cost_per_mw", "shutdown_cost_per_mw",
             "startup_plus_ramp_up_rate",
             "shutdown_plus_ramp_down_rate",
             "ramp_up_when_on_rate",
             "ramp_down_when_on_rate",
             "min_up_time_hours", "min_down_time_hours",
             "charging_efficiency", "discharging_efficiency",
             "minimum_duration_hours",
             ]
        )

        projects = c.execute(
            """SELECT project, capacity_type, operational_type, technology,
            load_zone, fuel, variable_cost_per_mwh,
            minimum_input_mmbtu_per_hr, inc_heat_rate_mmbtu_per_mwh,
            min_stable_level, unit_size_mw,
            startup_cost_per_mw, shutdown_cost_per_mw,
            startup_plus_ramp_up_rate,
            shutdown_plus_ramp_down_rate,
            ramp_up_when_on_rate,
            ramp_down_when_on_rate,
            min_up_time_hours, min_down_time_hours,
            charging_efficiency, discharging_efficiency,
            minimum_duration_hours
            FROM inputs_project_portfolios
            LEFT OUTER JOIN
            (SELECT project, load_zone
            FROM inputs_project_load_zones
            WHERE load_zone_scenario_id = {}
            AND project_load_zone_scenario_id = {}) as prj_load_zones
            USING (project)
            LEFT OUTER JOIN
            (SELECT project, operational_type, technology,
            fuel, variable_cost_per_mwh,
            minimum_input_mmbtu_per_hr, inc_heat_rate_mmbtu_per_mwh,
            min_stable_level, unit_size_mw,
            startup_cost_per_mw, shutdown_cost_per_mw,
            startup_plus_ramp_up_rate,
            shutdown_plus_ramp_down_rate,
            ramp_up_when_on_rate,
            ramp_down_when_on_rate,
            min_up_time_hours, min_down_time_hours,
            charging_efficiency, discharging_efficiency,
            minimum_duration_hours
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}) as prj_chars
            USING (project)
            WHERE project_portfolio_scenario_id = {}""".format(
                subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_LOAD_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )

        for row in projects:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # variable_generator_profiles.tab
    with open(os.path.join(inputs_directory,
                           "variable_generator_profiles.tab"), "w") as \
            variable_profiles_tab_file:
        writer = csv.writer(variable_profiles_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["GENERATORS", "TIMEPOINTS", "cap_factor"]
        )

        # Select only profiles of projects in the portfolio
        # Select only profiles of projects with 'variable' operational type
        # Select only profiles for timepoints from the correct timepoint
        # scenario
        # Select only timepoints on periods when the project is operational
        # (periods with existing project capacity for existing projects or
        # with costs specified for new projects)
        variable_profiles = c.execute(
            """SELECT project, timepoint, cap_factor
            FROM inputs_project_portfolios
            INNER JOIN
            (SELECT project, variable_generator_profile_scenario_id
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}
            AND (operational_type = 'variable'
            OR operational_type = 'variable_no_curtailment')
            ) AS op_char
            USING (project)
            CROSS JOIN
            (SELECT timepoint, period
            FROM inputs_temporal_timepoints
            WHERE timepoint_scenario_id = {})
            LEFT OUTER JOIN
            inputs_project_variable_generator_profiles
            USING (variable_generator_profile_scenario_id, project, timepoint)
            INNER JOIN
            (SELECT project, period
            FROM
            (SELECT project, period
            FROM inputs_project_existing_capacity
            INNER JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {})
            USING (period)
            WHERE project_existing_capacity_scenario_id = {}
            AND existing_capacity_mw > 0) as existing
            UNION
            SELECT project, period
            FROM inputs_project_new_cost
            INNER JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {})
            USING (period)
            WHERE project_new_cost_scenario_id = {})
            USING (project, period)
            WHERE project_portfolio_scenario_id = {}""".format(
                subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in variable_profiles:
            writer.writerow(row)

    # hydro_conventional_horizon_params.tab
    with open(os.path.join(inputs_directory,
                           "hydro_conventional_horizon_params.tab"),
              "w") as \
            hydro_chars_tab_file:
        writer = csv.writer(hydro_chars_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["hydro_project", "horizon",
             "hydro_average_power_mwa",
             "hydro_min_power_mw",
             "hydro_max_power_mw"]
        )

        # Select only budgets/min/max of projects in the portfolio
        # Select only budgets/min/max of projects with 'hydro_curtailable'
        # or 'hydro_noncurtailable' operational type
        # Select only budgets/min/max for horizons from the correct timepoint
        # scenario
        # Select only horizons on periods when the project is operational
        # (periods with existing project capacity for existing projects or
        # with costs specified for new projects)
        hydro_chars = c.execute(
            """SELECT project, horizon, average_power_mwa, min_power_mw,
            max_power_mw
            FROM inputs_project_portfolios
            INNER JOIN
            (SELECT project, hydro_operational_chars_scenario_id
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}
            AND (operational_type = 'hydro_curtailable' OR
            operational_type = 'hydro_noncurtailable')) AS op_char
            USING (project)
            CROSS JOIN
            (SELECT horizon
            FROM inputs_temporal_horizons
            WHERE timepoint_scenario_id = {})
            LEFT OUTER JOIN
            inputs_project_hydro_operational_chars
            USING (hydro_operational_chars_scenario_id, project, horizon)
            INNER JOIN
            (SELECT project, period
            FROM
            (SELECT project, period
            FROM inputs_project_existing_capacity
            INNER JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {})
            USING (period)
            WHERE project_existing_capacity_scenario_id = {}
            AND existing_capacity_mw > 0) as existing
            UNION
            SELECT project, period
            FROM inputs_project_new_cost
            INNER JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {})
            USING (period)
            WHERE project_new_cost_scenario_id = {})
            USING (project, period)
            WHERE project_portfolio_scenario_id = {}
            """.format(
                subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in hydro_chars:
            writer.writerow(row)

    # existing_generation_period_params.tab
    # TODO: storage currently excluded by selecting NULL energy capacity
    # values: make more robust
    with open(os.path.join(inputs_directory,
                           "existing_generation_period_params.tab"), "w") \
            as existing_project_capacity_tab_file:
        writer = csv.writer(existing_project_capacity_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["GENERATORS", "PERIODS", "existing_capacity_mw",
             "fixed_cost_per_mw_yr"]
        )

        ep_capacities = c.execute(
            """SELECT project, period, existing_capacity_mw,
            annual_fixed_cost_per_mw_year
            FROM inputs_project_portfolios
            CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {}) as relevant_periods
            INNER JOIN
            (SELECT project, period, existing_capacity_mw
            FROM inputs_project_existing_capacity
            WHERE project_existing_capacity_scenario_id = {}
            AND existing_capacity_mw > 0
            AND existing_capacity_mwh IS NULL) as capacity
            USING (project, period)
            LEFT OUTER JOIN
            (SELECT project, period, annual_fixed_cost_per_mw_year
            FROM inputs_project_existing_fixed_cost
            WHERE project_existing_fixed_cost_scenario_id = {}) as fixed_om
            USING (project, period)
            WHERE project_portfolio_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
                subscenarios.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in ep_capacities:
            writer.writerow(row)

    # storage_specified_capacities.tab
    # TODO: storage currently selected by via non-NULL energy capacity values
    with open(os.path.join(inputs_directory,
                           "storage_specified_capacities.tab"), "w") as \
            storage_specified_capacities_tab_file:
        writer = csv.writer(storage_specified_capacities_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["storage_project", "period",
             "storage_specified_power_capacity_mw",
             "storage_specified_energy_capacity_mwh"]
        )

        # TODO: more robust way to get storage projects than selecting non-null
        # rows
        stor_capacities = c.execute(
            """SELECT project, period, existing_capacity_mw,
            existing_capacity_mwh,
            annual_fixed_cost_per_mw_year, annual_fixed_cost_per_mwh_year
            FROM inputs_project_portfolios
            CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {}) as relevant_periods
            INNER JOIN
            (SELECT project, period, existing_capacity_mw,
            existing_capacity_mwh
            FROM inputs_project_existing_capacity
            WHERE project_existing_capacity_scenario_id = {}
            AND existing_capacity_mw > 0
            AND existing_capacity_mwh IS NOT NULL) as capacity
            USING (project, period)
            LEFT OUTER JOIN
            (SELECT project, period, annual_fixed_cost_per_mw_year,
            annual_fixed_cost_per_mwh_year
            FROM inputs_project_existing_fixed_cost
            WHERE project_existing_fixed_cost_scenario_id = {}) as fixed_om
            USING (project, period)
            WHERE project_portfolio_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
                subscenarios.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in stor_capacities:
            writer.writerow(row)

    # new_build_generator_vintage_costs.tab
    with open(os.path.join(inputs_directory,
                           "new_build_generator_vintage_costs.tab"), "w") as \
            new_gen_costs_tab_file:
        writer = csv.writer(new_gen_costs_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["new_build_generator", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr", "min_cumulative_new_build_mw",
             "max_cumulative_new_build_mw"]
        )

        # TODO: select only rows with NULL for cost per kWh-yr for generators
        # only (i.e to exclude storage), but need to make this more robust
        new_gen_costs = c.execute(
            """SELECT project, period, lifetime_yrs,
            annualized_real_cost_per_kw_yr * 1000,
            minimum_cumulative_new_build_mw, maximum_cumulative_new_build_mw
            FROM inputs_project_portfolios
            CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {}) as relevant_periods
            INNER JOIN
            (SELECT project, period, lifetime_yrs,
            annualized_real_cost_per_kw_yr
            FROM inputs_project_new_cost
            WHERE project_new_cost_scenario_id = {}
            AND annualized_real_cost_per_kwh_yr IS NULL) as cost
            USING (project, period)
            LEFT OUTER JOIN
            (SELECT project, period, minimum_cumulative_new_build_mw,
            maximum_cumulative_new_build_mw
            FROM inputs_project_new_potential
            WHERE project_new_potential_scenario_id = {}) as potential
            USING (project, period)
            WHERE project_portfolio_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
                subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in new_gen_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # new_build_storage_vintage_costs.tab
    with open(os.path.join(inputs_directory,
                           "new_build_storage_vintage_costs.tab"), "w") as \
            new_storage_costs_tab_file:
        writer = csv.writer(new_storage_costs_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["new_build_storage", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr",
             "annualized_real_cost_per_mwh_yr",
             "min_cumulative_new_build_mw", "min_cumulative_new_build_mwh",
             "max_cumulative_new_build_mw", "max_cumulative_new_build_mwh"]
        )

        # TODO: select only rows with non NULL for cost per kWh-yr for storage
        # only (not generators), but need to make this more robust
        new_stor_costs = c.execute(
            """SELECT project, period, lifetime_yrs,
            annualized_real_cost_per_kw_yr * 1000,
            annualized_real_cost_per_kwh_yr * 1000,
            minimum_cumulative_new_build_mw, minimum_cumulative_new_build_mwh,
            maximum_cumulative_new_build_mw, maximum_cumulative_new_build_mwh
            FROM inputs_project_portfolios
            CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE timepoint_scenario_id = {}) as relevant_periods
            INNER JOIN
            (SELECT project, period, lifetime_yrs,
            annualized_real_cost_per_kw_yr, annualized_real_cost_per_kwh_yr
            FROM inputs_project_new_cost
            WHERE project_new_cost_scenario_id = {}
            AND annualized_real_cost_per_kwh_yr IS NOT NULL) as cost
            USING (project, period)
            LEFT OUTER JOIN
            (SELECT project, period,
            minimum_cumulative_new_build_mw, minimum_cumulative_new_build_mwh,
            maximum_cumulative_new_build_mw, maximum_cumulative_new_build_mwh
            FROM inputs_project_new_potential
            WHERE project_new_potential_scenario_id = {}) as potential
            USING (project, period)
            WHERE project_portfolio_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
                subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in new_stor_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
