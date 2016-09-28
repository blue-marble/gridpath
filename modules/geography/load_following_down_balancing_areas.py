#!/usr/bin/env python

import os.path
from pyomo.environ import Set


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.LF_RESERVES_DOWN_ZONES = Set()


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
    data_portal.load(
        filename=os.path.join(scenario_directory, "inputs",
                              "load_following_down_balancing_areas.tab"),
        select=("balancing_area",),
        index=m.LF_RESERVES_DOWN_ZONES,
        param=()
    )
