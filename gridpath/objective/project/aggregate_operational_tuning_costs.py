#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Tuning costs to prevent undesirable behavior when problem is degenerate.
E.g. since the cost incurred by hydro over the course of a horizon is the same 
regardless of exact dispatch, cases may arise when the project is ramped 
unnecessarily unless there's a cost on the ramp. This aggregates the tuning 
costs imposed on hydro to prevent this behavior.
"""

from pyomo.environ import Param, Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param di:
    :return:
    """

    def total_ramp_tuning_cost_rule(mod):
        """
        Ramp tuning costs for all projects
        :param mod:
        :return:
        """
        return sum(
            (mod.Ramp_Up_Tuning_Cost[g, tmp] +
             mod.Ramp_Down_Tuning_Cost[g, tmp])
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for (g, tmp)
            in mod.PRJ_OPR_TMPS
        )

    m.Total_Ramp_Tuning_Cost = Expression(
        rule=total_ramp_tuning_cost_rule
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add tuning costs to cost components
    """

    getattr(dynamic_components, total_cost_components).append(
        "Total_Ramp_Tuning_Cost")
