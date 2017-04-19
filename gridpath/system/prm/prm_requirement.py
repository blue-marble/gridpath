#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
PRM requirement for each PRM zone
"""

import csv
import os.path
import pandas as pd

from pyomo.environ import Set, Param, NonNegativeReals, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.PRM_ZONE_PERIODS_WITH_REQUIREMENT = \
        Set(dimen=2, within=m.PRM_ZONES * m.PERIODS)
    m.prm_requirement_mw = Param(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "prm_requirement.tab"),
                     index=m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
                     param=m.prm_requirement_mw,
                     select=("prm_zone", "period",
                             "prm_requirement_mw")
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    pass
