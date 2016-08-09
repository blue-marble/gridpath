#!/usr/bin/env python

from pyomo.environ import *

def add_model_components(m):
    m.LOAD_ZONES = Set(initialize=["Zone1"])

