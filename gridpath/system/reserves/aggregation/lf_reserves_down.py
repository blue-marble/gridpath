#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

from .reserve_aggregation import generic_add_model_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "lf_reserves_down_zone",
        "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
        "LF_RESERVES_DOWN_PROJECTS",
        "Provide_LF_Reserves_Down_MW",
        "Total_LF_Reserves_Down_Provision_MW"
        )
