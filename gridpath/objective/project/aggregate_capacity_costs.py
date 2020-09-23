#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates all project capacity costs and adds them to the
objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param di: the DynamicComponents class object we are adding components to

    Here, we sum up all capacity-related costs and add them to the
    objective-function dynamic components.

    :math:`Total\_Capacity\_Costs =
    \sum_{(r, p)\in {RP}}{Capacity\_Cost\_in\_Period_{r, p} \\times
    discount\_factor_p \\times number\_years\_represented_p}`

    """
    # Add costs to objective function
    def total_capacity_cost_rule(mod):
        return sum(mod.Capacity_Cost_in_Period[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.PRJ_OPR_PRDS)
    m.Total_Capacity_Costs = Expression(rule=total_capacity_cost_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total capacity costs to cost components
    """

    getattr(dynamic_components, total_cost_components).append(
        "Total_Capacity_Costs")
