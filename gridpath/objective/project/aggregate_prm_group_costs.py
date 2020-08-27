#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate capacity threshold costs.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    Add total prm group costs to cost components
    :param d:
    :return:
    """

    getattr(d, total_cost_components).append("Total_PRM_Group_Costs")


def add_model_components(m, d):
    """
    Sum up all PRM group costs and add to the objective function.
    :param m:
    :param d:
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
