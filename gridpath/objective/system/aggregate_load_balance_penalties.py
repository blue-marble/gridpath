#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import os.path
from pyomo.environ import Param, Expression, NonNegativeReals

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_penalty_costs_rule(mod):
        return sum((mod.Unserved_Energy_MW[z, tmp]
                    * mod.unserved_energy_penalty_per_mw[z] +
                    mod.Overgeneration_MW[z, tmp]
                    * mod.overgeneration_penalty_per_mw[z])
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for z in mod.LOAD_ZONES for tmp in mod.TIMEPOINTS)
    m.Total_Load_Balance_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)
    getattr(d, total_cost_components).append(
        "Total_Load_Balance_Penalty_Costs"
    )
