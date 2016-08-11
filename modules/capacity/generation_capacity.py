#!/usr/bin/env python

import os
from pyomo.environ import *


def add_model_components(m):
    m.GENERATORS = Set()

    m.capacity = Param(m.GENERATORS)
    m.variable_cost = Param(m.GENERATORS)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "generation_capacity.tab"),
                     index=m.GENERATORS,
                     param=(m.capacity, m.variable_cost)
                     )


def view_loaded_data(instance):
    print "Viewing data"
    for g in instance.GENERATORS:
        print(g, instance.capacity[g])