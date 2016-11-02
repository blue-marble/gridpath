#!/usr/bin/env python

"""
Smallest unit of time over which operational variables are defined
"""

import os.path

from pyomo.environ import Param, Set, NonNegativeReals, NonNegativeIntegers


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True)
    m.number_of_hours_in_timepoint = \
        Param(m.TIMEPOINTS, within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "timepoints.tab"),
                     index=m.TIMEPOINTS,
                     param=m.number_of_hours_in_timepoint,
                     select=("TIMEPOINTS", "number_of_hours_in_timepoint")
                     )
