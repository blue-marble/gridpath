#!/usr/bin/env python

from pyomo.environ import *


def add_model_components(m):
    m.GENERATORS = Set(initialize=["Gen1", "Gen2"])
    m.RESERVE_GENERATORS = Set(initialize=["Gen2"])

    m.capacity = Param(m.GENERATORS, initialize={"Gen1": 11, "Gen2": 11})
    m.variable_cost = Param(m.GENERATORS, initialize={"Gen1": 1, "Gen2": 2})