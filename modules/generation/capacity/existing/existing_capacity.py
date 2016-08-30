#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, NonNegativeReals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.GENERATORS = Set()

    m.capacity_mw = Param(m.GENERATORS, within=NonNegativeReals)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "capacity_mw"),
                     param=m.capacity_mw
                     )


def view_loaded_data(instance):
    print "Viewing data"
    for g in instance.GENERATORS:
        print(g, instance.capacity[g])