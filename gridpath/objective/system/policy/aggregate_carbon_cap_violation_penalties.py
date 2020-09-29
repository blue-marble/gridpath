#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
This module adds carbon cap overage penalty costs to the objective function.
"""

import os.path
from pyomo.environ import Param, Expression, NonNegativeReals

from gridpath.auxiliary.dynamic_components import cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    Here, we aggregate total penalty costs for not meeting the carbon cap
    constraint.
    """

    def total_penalty_costs_rule(mod):
        return sum(mod.Carbon_Cap_Overage_Expression[z, p]
                   * mod.carbon_cap_violation_penalty_per_emission[z]
                   * mod.number_years_represented[p]
                   * mod.discount_factor[p]
                   for (z, p) in mod.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP)
    m.Total_Carbon_Cap_Balance_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total carbon cap penalty costs to cost components

    """

    getattr(dynamic_components, cost_components).append(
        "Total_Carbon_Cap_Balance_Penalty_Costs"
    )
