#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


from __future__ import absolute_import

from .aggregate_reserve_violation_penalties import \
    generic_determine_dynamic_components, generic_add_model_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    generic_determine_dynamic_components(d, "Spinning_Reserves_Penalty_Costs")


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "SPINNING_RESERVES_ZONES",
        "Spinning_Reserves_Violation_MW_Expression",
        "spinning_reserves_violation_penalty_per_mw",
        "Spinning_Reserves_Penalty_Costs"
        )
