#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates transmission-line-timepoint-level operational costs
for use in the objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
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
            (mod.Hurdle_Cost_Pos_Dir[tx, tmp] +
             mod.Hurdle_Cost_Neg_Dir[tx, tmp])
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for (tx, tmp) in mod.TX_OPR_TMPS)

    m.Total_Hurdle_Cost = Expression(rule=total_hurdle_cost_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total transmission hurdle costs to cost components
    """

    getattr(dynamic_components, total_cost_components).append(
        "Total_Hurdle_Cost")


