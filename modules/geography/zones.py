#!/usr/bin/env python

from pyomo.environ import *

def add_model_components(m):
    m.LOAD_ZONES = Set(initialize=["Zone1"])


def view_data(instance):
    print "Viewing data"
    print instance.LOAD_ZONES
    for z in instance.LOAD_ZONES:
        print(z)