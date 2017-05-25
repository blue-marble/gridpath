#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """

    """
    m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS",
    )

    m.storage_specified_power_capacity_mw = \
        Param(m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
              within=NonNegativeReals)

    m.storage_specified_energy_capacity_mwh = \
        Param(m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
              within=NonNegativeReals)

    m.storage_specified_fixed_cost_per_mw_yr = \
        Param(m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
              within=NonNegativeReals)

    m.storage_specified_fixed_cost_per_mwh_yr = \
        Param(m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
              within=NonNegativeReals)


def capacity_rule(mod, g, p):
    return mod.storage_specified_power_capacity_mw[g, p]


def energy_capacity_rule(mod, g, p):
    return mod.storage_specified_energy_capacity_mwh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    
    :param mod: 
    :param g: 
    :param p: 
    :return: 
    """
    return mod.storage_specified_power_capacity_mw[g, p] \
        * mod.storage_specified_fixed_cost_per_mw_yr[g, p] \
        + mod.storage_specified_energy_capacity_mwh[g, p] \
        * mod.storage_specified_fixed_cost_per_mwh_yr[g, p]


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "storage_specified_capacities.tab"),
                     index=
                     m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
                     select=("project", "period",
                             "storage_specified_power_capacity_mw",
                             "storage_specified_energy_capacity_mwh",
                             "storage_specified_fixed_cost_per_mw_yr",
                             "storage_specified_fixed_cost_per_mwh_yr"),
                     param=(m.storage_specified_power_capacity_mw,
                            m.storage_specified_energy_capacity_mwh,
                            m.storage_specified_fixed_cost_per_mw_yr,
                            m.storage_specified_fixed_cost_per_mwh_yr)
                     )


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    storage_specified_capacities.tab
    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

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
        AND existing_capacity_mw > 0) as capacity
        USING (project, period)
        LEFT OUTER JOIN
        (SELECT project, period,
        annual_fixed_cost_per_kw_year * 1000 AS annual_fixed_cost_per_mw_year,
        annual_fixed_cost_per_kwh_year * 1000 AS annual_fixed_cost_per_mwh_year
        FROM inputs_project_existing_fixed_cost
        WHERE project_existing_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 
        'storage_specified_no_economic_retirement';""".format(
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    with open(os.path.join(inputs_directory,
                           "storage_specified_capacities.tab"), "w") as \
            storage_specified_capacities_tab_file:
        writer = csv.writer(storage_specified_capacities_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "period",
             "storage_specified_power_capacity_mw",
             "storage_specified_energy_capacity_mwh",
             "storage_specified_fixed_cost_per_mw_yr",
             "storage_specified_fixed_cost_per_mwh_yr"]
        )

        for row in stor_capacities:
            writer.writerow(row)
