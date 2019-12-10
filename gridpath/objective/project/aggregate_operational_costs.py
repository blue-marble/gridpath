#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates all project operational costs and adds them to the
objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we sum up all operational costs and add them to the
    objective-function dynamic components. Operational costs include
    variable O&M costs, fuel costs, startup costs, and shutdown costs.

    :math:`Total\_Variable\_OM\_Cost =
    \sum_{(r, tmp)\in {RT}}{Variable\_OM\_Cost_{r, tmp}
    \\times number\_of\_hours\_in\_timepoint_{tmp}
    \\times horizon\_weight_{h^{tmp}}
    \\times number\_years\_represented_{p^{tmp}}
    \\times discount\_factor_{p^{tmp}}}`

    :math:`Total\_Fuel\_Cost =
    \sum_{(r, tmp)\in {RT}}{Fuel\_Cost_{r, tmp}
    \\times number\_of\_hours\_in\_timepoint_{tmp}
    \\times horizon\_weight_{h^{tmp}}
    \\times number\_years\_represented_{p^{tmp}}
    \\times discount\_factor_{p^{tmp}}}`

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
                   * mod.timepoint_weight[tmp]
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
                   * mod.timepoint_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS)

    m.Total_Fuel_Cost = Expression(rule=total_fuel_cost_rule)
    getattr(d, total_cost_components).append("Total_Fuel_Cost")

    # Startup and shutdown costs
    def total_startup_cost_rule(mod):
        """
        Sum startup costs for the objective function term. Note that there
        can be different startup types depending on the cooling state or the
        "hotness" of the start, i.e. how long the unit has been down.
        :param mod:
        :return:
        """
        return sum(mod.Startup_Cost[g, tmp, l]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.timepoint_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp, l)
                   in mod.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)
    getattr(d, total_cost_components).append("Total_Startup_Cost")

    def total_shutdown_cost_rule(mod):
        """
        Sum shutdown costs for the objective function term. Unlike the startup
        cost, this cost is not dependent on how long the unit has been up.
        :param mod:
        :return:
        """
        return sum(mod.Shutdown_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.timepoint_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)
    getattr(d, total_cost_components).append("Total_Shutdown_Cost")
