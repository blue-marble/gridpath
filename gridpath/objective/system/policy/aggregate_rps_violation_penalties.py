#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
This module adds RPS shortage penalty costs to the objective function.
"""

import os.path
from pyomo.environ import Param, Expression, NonNegativeReals

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    Here, we aggregate total penalty costs for not meeting the RPS constraint.
    """

    def total_penalty_costs_rule(mod):
        return sum(mod.RPS_Shortage_MWh_Expression[z, p]
                   * mod.rps_violation_penalty_per_mwh[z]
                   * mod.number_years_represented[p]
                   * mod.discount_factor[p]
                   for (z, p) in mod.RPS_ZONE_PERIODS_WITH_RPS)
    m.Total_RPS_Balance_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)
    getattr(d, total_cost_components).append(
        "Total_RPS_Balance_Penalty_Costs"
    )
