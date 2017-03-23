#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from reserve_aggregation import generic_add_model_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "regulation_up_zone",
        "REGULATION_UP_ZONE_TIMEPOINTS",
        "REGULATION_UP_PROJECTS",
        "Provide_Regulation_Up_MW",
        "Total_Regulation_Up_Provision_MW"
        )
