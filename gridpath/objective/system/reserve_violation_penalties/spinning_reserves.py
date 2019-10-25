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
        "SPINNING_RESERVES_ZONE_TIMEPOINTS",
        "Spinning_Reserves_Violation_MW",
        "spinning_reserves_violation_penalty_per_mw",
        "Spinning_Reserves_Penalty_Costs"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "spinning_reserves_balancing_areas.tab",
                            "spinning_reserves_violation_penalty_per_mw"
                            )
