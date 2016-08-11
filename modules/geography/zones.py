#!/usr/bin/env python
import os

from pyomo.environ import *


def add_model_components(m):
    m.LOAD_ZONES = Set()


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "load_zones.tab"),
                     set=m.LOAD_ZONES
                     )


def view_data(instance):
    print "Viewing data"
    print instance.LOAD_ZONES
    for z in instance.LOAD_ZONES:
        print(z)