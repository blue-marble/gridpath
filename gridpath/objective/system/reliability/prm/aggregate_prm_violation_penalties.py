#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    Add total prm shortage penalty costs to cost components
    :param d:
    :return:
    """

    getattr(d, total_cost_components).append(
        "Total_PRM_Shortage_Penalty_Costs"
    )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_penalty_costs_rule(mod):
        return sum(mod.PRM_Shortage_MW_Expression[z, p]
                   * mod.prm_violation_penalty_per_mw[z]
                   * mod.number_years_represented[p]
                   * mod.discount_factor[p]
                   for (z, p) in
                   mod.PRM_ZONE_PERIODS_WITH_REQUIREMENT)
    m.Total_PRM_Shortage_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)
