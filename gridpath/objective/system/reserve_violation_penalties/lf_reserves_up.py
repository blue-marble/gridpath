#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


from __future__ import absolute_import

from .aggregate_reserve_violation_penalties import \
    generic_determine_dynamic_components, generic_add_model_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    generic_determine_dynamic_components(d, "LF_Reserves_Up_Penalty_Costs")


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "LF_RESERVES_UP_ZONES",
        "LF_Reserves_Up_Violation_MW_Expression",
        "lf_reserves_up_violation_penalty_per_mw",
        "LF_Reserves_Up_Penalty_Costs"
        )
