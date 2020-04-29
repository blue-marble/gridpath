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
        "REGULATION_DOWN_ZONES",
        "Regulation_Down_Violation_MW_Expression",
        "regulation_down_violation_penalty_per_mw",
        "Regulation_Down_Penalty_Costs"
        )
