#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate carbon emissions from the transmission-line-timepoint level to
the carbon cap zone - period level.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_hurdle_cost_rule(mod):
        """
        Hurdle costs for all transmission lines across all timepoints
        :param mod:
        :return:
        """
        return sum(
            (mod.Hurdle_Cost_Positive_Direction[tx, tmp] +
             mod.Hurdle_Cost_Negative_Direction[tx, tmp])
            * mod.number_of_hours_in_timepoint[tmp]
            * mod.horizon_weight[mod.horizon[tmp]]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for (tx, tmp) in mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS)

    m.Total_Hurdle_Cost = Expression(rule=total_hurdle_cost_rule)
    getattr(d, total_cost_components).append("Total_Hurdle_Cost")


