#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate capacity costs.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """
    Sum up all capacity costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """
    # Add costs to objective function
    def total_capacity_cost_rule(mod):
        return sum(mod.Capacity_Cost_in_Period[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.PROJECT_OPERATIONAL_PERIODS)
    m.Total_Capacity_Costs = Expression(rule=total_capacity_cost_rule)
    getattr(d, total_cost_components).append("Total_Capacity_Costs")
