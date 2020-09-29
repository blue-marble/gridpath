#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    def total_penalty_costs_rule(mod):
        return sum(mod.Local_Capacity_Shortage_MW_Expression[z, p]
                   * mod.local_capacity_violation_penalty_per_mw[z]
                   * mod.number_years_represented[p]
                   * mod.discount_factor[p]
                   for (z, p) in
                   mod.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT)
    m.Total_Local_Capacity_Shortage_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add local capacity shortage penalty costs to cost components
    """

    getattr(dynamic_components, total_cost_components).append(
        "Total_Local_Capacity_Shortage_Penalty_Costs"
    )
