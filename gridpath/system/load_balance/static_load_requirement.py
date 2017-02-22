#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Param, Var, Constraint, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    load_balance_consumption_components, load_balance_production_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Static load
    m.static_load_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS,
                             within=NonNegativeReals)
    getattr(d, load_balance_consumption_components).append("static_load_mw")


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
                                           "inputs", "load_mw.tab"),
                     param=m.static_load_mw
                     )
