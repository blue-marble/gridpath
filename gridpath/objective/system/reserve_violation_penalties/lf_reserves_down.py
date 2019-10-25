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
        "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
        "LF_Reserves_Down_Violation_MW",
        "lf_reserves_down_violation_penalty_per_mw",
        "LF_Reserves_Down_Penalty_Costs"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "load_following_down_balancing_areas.tab",
                            "lf_reserves_down_violation_penalty_per_mw"
                            )
