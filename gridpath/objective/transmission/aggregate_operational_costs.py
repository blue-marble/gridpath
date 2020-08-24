#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates transmission-line-timepoint-level operational costs
for use in the objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    Add total transmission hurdle costs to cost components
    :param d:
    :return:
    """

    getattr(d, total_cost_components).append("Total_Hurdle_Cost")


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
            (mod.Hurdle_Cost_Pos_Dir[tx, tmp] +
             mod.Hurdle_Cost_Neg_Dir[tx, tmp])
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for (tx, tmp) in mod.TX_OPR_TMPS)

    m.Total_Hurdle_Cost = Expression(rule=total_hurdle_cost_rule)


