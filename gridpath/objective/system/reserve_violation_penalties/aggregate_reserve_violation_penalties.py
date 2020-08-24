#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def generic_determine_dynamic_components(
        d,
        objective_function_reserve_penalty_cost_component
):
    """
    Add total reserve penalty to cost components dynamic components

    :param d:
    :param objective_function_reserve_penalty_cost_component:
    :return:
    """
    getattr(d, total_cost_components).append(
        objective_function_reserve_penalty_cost_component)


def generic_add_model_components(
        m,
        d,
        reserve_zone_set,
        reserve_violation_expression,
        reserve_violation_penalty_param,
        objective_function_reserve_penalty_cost_component
):
    """
    Aggregate reserve violation penalty costs
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_violation_expression:
    :param reserve_violation_penalty_param:
    :param objective_function_reserve_penalty_cost_component:
    :return:
    """
    # Add violation penalty costs incurred to objective function
    def penalty_costs_rule(mod):
        return sum(getattr(mod, reserve_violation_expression)[ba, tmp]
                   * getattr(mod, reserve_violation_penalty_param)[ba]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (ba, tmp)
                   in getattr(mod, reserve_zone_set) * mod.TMPS
                   )
    setattr(m, objective_function_reserve_penalty_cost_component,
            Expression(rule=penalty_costs_rule))
