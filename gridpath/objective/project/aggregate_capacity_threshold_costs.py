#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate capacity threshold costs.
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
    def total_capacity_threshold_cost_rule(mod):
        return sum(mod.Capacity_Threshold_Cost[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for g in mod.CAPACITY_THRESHOLD_GROUPS
                   for p in mod.PERIODS)
    m.Total_Capacity_Threshold_Costs = Expression(
        rule=total_capacity_threshold_cost_rule)
    getattr(d, total_cost_components).append("Total_Capacity_Threshold_Costs")
