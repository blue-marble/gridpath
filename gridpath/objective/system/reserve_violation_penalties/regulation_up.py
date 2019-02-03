#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


from __future__ import absolute_import

from .aggregate_reserve_violation_penalties import \
    generic_add_model_components, generic_load_model_data


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "REGULATION_UP_ZONES",
        "REGULATION_UP_ZONE_TIMEPOINTS",
        "Regulation_Up_Violation_MW",
        "regulation_up_violation_penalty_per_mw",
        "Regulation_Up_Penalty_Costs"
        )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            "regulation_up_balancing_areas.tab",
                            "regulation_up_violation_penalty_per_mw"
                            )
