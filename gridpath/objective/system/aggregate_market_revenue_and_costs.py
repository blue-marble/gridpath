#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
This module adds market revenue and costs to the objective function components.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import cost_components, \
    revenue_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    Here, we aggregate total market revenue and costs, and add them as a
    dynamic component to the objective function.

    """
    def total_market_revenue_rule(mod):
        return sum(
            mod.Total_Market_Sales[market, tmp]
            * mod.market_price[market, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for market in mod.MARKETS for tmp in mod.TMPS
        )
    m.Total_Market_Revenue = Expression(rule=total_market_revenue_rule)

    def total_market_cost_rule(mod):
        return sum(
            mod.Total_Market_Purchases[market, tmp]
            * mod.market_price[market, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for market in mod.MARKETS for tmp in mod.TMPS
        )
    m.Total_Market_Cost = Expression(rule=total_market_cost_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total load balance penalty costs to cost components
    """

    getattr(dynamic_components, cost_components).append("Total_Market_Cost")
    getattr(dynamic_components, revenue_components).append(
        "Total_Market_Revenue"
    )
