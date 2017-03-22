#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe operational costs.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    # Power production variable costs
    def total_variable_om_cost_rule(mod):
        """
        Power production cost for all generators across all timepoints
        :param mod:
        :return:
        """
        return sum(mod.Variable_OM_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS)

    m.Total_Variable_OM_Cost = Expression(rule=total_variable_om_cost_rule)
    getattr(d, total_cost_components).append("Total_Variable_OM_Cost")

    # Fuel cost
    def total_fuel_cost_rule(mod):
        """
        Fuel costs for all generators across all timepoints
        :param mod:
        :return:
        """
        return sum(mod.Fuel_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS)

    m.Total_Fuel_Cost = Expression(rule=total_fuel_cost_rule)
    getattr(d, total_cost_components).append("Total_Fuel_Cost")

    # Startup and shutdown costs
    def total_startup_cost_rule(mod):
        """
        Sum startup costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Startup_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)
    getattr(d, total_cost_components).append("Total_Startup_Cost")

    def total_shutdown_cost_rule(mod):
        """
        Sum shutdown costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Shutdown_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)
    getattr(d, total_cost_components).append("Total_Shutdown_Cost")
