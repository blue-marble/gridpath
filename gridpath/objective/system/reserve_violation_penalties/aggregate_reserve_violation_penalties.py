#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import os.path
from pyomo.environ import Param, Var, Expression, NonNegativeReals

from gridpath.auxiliary.dynamic_components import total_cost_components


def generic_add_model_components(
        m,
        d,
        reserve_zone_set,
        reserve_zone_timepoint_set,
        reserve_violation_variable,
        reserve_violation_penalty_param,
        objective_function_reserve_penalty_cost_component
):
    """
    Aggregate reserve violation penalty costs and add to the objective function
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :param reserve_violation_penalty_param:
    :param objective_function_reserve_penalty_cost_component:
    :return:
    """
    setattr(m, reserve_violation_penalty_param,
            Param(getattr(m, reserve_zone_set),
                  within=NonNegativeReals))

    # Add violation penalty costs incurred to objective function
    # TODO: this needs to be multiplied by hours in timepoint andhorizon weight
    def penalty_costs_rule(mod):
        return sum(getattr(mod, reserve_violation_variable)[ba, tmp]
                   * getattr(mod, reserve_violation_penalty_param)[ba]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (ba, tmp)
                   in getattr(mod, reserve_zone_timepoint_set)
                   )
    setattr(m, objective_function_reserve_penalty_cost_component,
            Expression(rule=penalty_costs_rule))

    getattr(d, total_cost_components).append(
        objective_function_reserve_penalty_cost_component)


def generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            ba_list_filename,
                            reserve_violation_penalty_param
                            ):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param ba_list_filename:
    :param reserve_violation_penalty_param:
    :param requirement_filename:
    :param reserve_zone_timepoint_set:
    :param reserve_requirement_param:
    :return:
    """

    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           ba_list_filename),
                     select=("balancing_area", "violation_penalty_per_mw"),
                     param=getattr(m, reserve_violation_penalty_param)
                     )
