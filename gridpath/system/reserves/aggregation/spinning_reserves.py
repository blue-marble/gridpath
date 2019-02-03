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
        "spinning_reserves_zone",
        "SPINNING_RESERVES_ZONE_TIMEPOINTS",
        "SPINNING_RESERVES_PROJECTS",
        "Provide_Spinning_Reserves_MW",
        "Total_Spinning_Reserves_Provision_MW"
        )
