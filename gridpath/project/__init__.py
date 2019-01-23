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
    # This list will be used to know which capacity type modules to load
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
    """
    
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param horizon: 
    :param stage: 
    :return: 
    """
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

    # TODO: decide how to deal with projects.tab -- currently, a large table
    #  is created with NULL values for projects that don't have certain
    # params, so we can just get it all here without having to iterate
    # through the modules that actually need these params
    # This file could also potentially be split up into smaller files with
    # just a subset of the params, which would mean that the submodules
    # won't have to parse the large file
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
             "startup_fuel_mmbtu_per_mw",
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
            startup_fuel_mmbtu_per_mw,
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
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_LOAD_ZONE_SCENARIO_ID,
                subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
            )
        )

        for row in projects:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
