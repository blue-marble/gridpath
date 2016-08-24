#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, NonNegativeReals


def add_model_components(m):
    m.GENERATORS = Set()

    m.capacity = Param(m.GENERATORS, within=NonNegativeReals)
    m.variable_cost = Param(m.GENERATORS, within=NonNegativeReals)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "capacity", "variable_cost"),
                     param=(m.capacity, m.variable_cost)
                     )


def view_loaded_data(instance):
    print "Viewing data"
    for g in instance.GENERATORS:
        print(g, instance.capacity[g])