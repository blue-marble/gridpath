#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_penalty_costs_rule(mod):
        return sum(mod.Local_Capacity_Shortage_MW[z, p]
                   * mod.local_capacity_shortage_penalty_per_mw[z]
                   * mod.number_years_represented[p]
                   * mod.discount_factor[p]
                   for (z, p) in
                   mod.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT)
    m.Total_Load_Capacity_Shortage_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)
    getattr(d, total_cost_components).append(
        "Total_Load_Capacity_Shortage_Penalty_Costs"
    )
