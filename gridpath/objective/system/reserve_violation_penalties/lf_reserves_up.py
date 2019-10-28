#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


from __future__ import absolute_import

from .aggregate_reserve_violation_penalties import \
    generic_add_model_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "LF_RESERVES_UP_ZONE_TIMEPOINTS",
        "LF_Reserves_Up_Violation_MW",
        "lf_reserves_up_violation_penalty_per_mw",
        "LF_Reserves_Up_Penalty_Costs"
        )
