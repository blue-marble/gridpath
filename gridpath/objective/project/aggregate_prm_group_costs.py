#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate capacity threshold costs.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, di, dc):
    """
    Sum up all PRM group costs and add to the objective function.
    :param m:
    :param di:
    :return:
    """

    # TODO: change the name of the expression and of this module
    # Add costs to objective function
    def total_capacity_threshold_cost_rule(mod):
        return sum(mod.PRM_Group_Costs[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for g in mod.PRM_COST_GROUPS
                   for p in mod.PERIODS)
    m.Total_PRM_Group_Costs = Expression(
        rule=total_capacity_threshold_cost_rule)

    record_dynamic_components(dynamic_components=dc)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total prm group costs to cost components
    """

    getattr(dynamic_components, total_cost_components).append(
        "Total_PRM_Group_Costs")
