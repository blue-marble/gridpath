#!/usr/bin/env python

"""
Smallest unit of time over which operational variables are defined
"""

import os.path

from pyomo.environ import Set, NonNegativeIntegers


def add_model_components(m, d):
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "timepoints.tab"),
                     index=m.TIMEPOINTS,
                     param=(),
                     select=("TIMEPOINTS",)
                     )
