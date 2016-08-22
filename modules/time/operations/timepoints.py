#!/usr/bin/env python

"""
Smallest unit of time over which operational variables are defined
"""

import os.path

from pyomo.environ import Set, NonNegativeIntegers


def add_model_components(m):
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "timepoints.tab"),
                     index=m.TIMEPOINTS,
                     param=(),
                     select=("TIMEPOINTS",)
                     )
