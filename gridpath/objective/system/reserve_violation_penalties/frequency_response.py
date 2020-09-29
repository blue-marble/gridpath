#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import cost_components
from .aggregate_reserve_violation_penalties import \
    generic_record_dynamic_components, generic_add_model_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    # Total freq response requirement
    generic_add_model_components(
        m,
        d,
        scenario_directory, subproblem, stage,
        "FREQUENCY_RESPONSE_BAS",
        "Frequency_Response_Violation_MW_Expression",
        "frequency_response_violation_penalty_per_mw",
        "Frequency_Response_Penalty_Costs"
        )

    # Partial frequency response requirement

    # Add violation penalty costs incurred to objective function
    # Assume violation cost is the same as for the total requirement
    def partial_frequency_response_penalty_costs_rule(mod):
        return sum(mod.Frequency_Response_Partial_Violation_MW[ba, tmp]
                   * mod.frequency_response_violation_penalty_per_mw[ba]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (ba, tmp)
                   in mod.FREQUENCY_RESPONSE_BAS * mod.TMPS
                   )
    m.Frequency_Response_Partial_Penalty_Costs = \
        Expression(rule=partial_frequency_response_penalty_costs_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    generic_record_dynamic_components(dynamic_components,
                                      "Frequency_Response_Penalty_Costs")

    getattr(dynamic_components, cost_components).append(
        "Frequency_Response_Partial_Penalty_Costs")
