#!/usr/bin/env python
import os

from pyomo.environ import *


def add_model_components(m):
    m.TIMEPOINTS = Set(within=NonNegativeIntegers)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "timepoints.tab"),
                     set=m.TIMEPOINTS
                     )
