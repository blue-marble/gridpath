#!/usr/bin/env python

import os.path
from pyomo.environ import Set


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.LOAD_ZONES = Set()


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
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "load_zones.tab"),
                     select=("load_zone",),
                     index=m.LOAD_ZONES,
                     param=()
                     )
