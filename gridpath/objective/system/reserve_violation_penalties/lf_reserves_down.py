#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


from __future__ import absolute_import

from .aggregate_reserve_violation_penalties import \
    generic_record_dynamic_components, generic_add_model_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        scenario_directory, subproblem, stage,
        "LF_RESERVES_DOWN_ZONES",
        "LF_Reserves_Down_Violation_MW_Expression",
        "lf_reserves_down_violation_penalty_per_mw",
        "LF_Reserves_Down_Penalty_Costs"
        )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    generic_record_dynamic_components(dynamic_components,
                                      "LF_Reserves_Down_Penalty_Costs")
