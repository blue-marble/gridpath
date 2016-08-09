#!/usr/bin/env python

from pyomo.environ import *

def add_model_components(m):
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, initialize=[1, 2])