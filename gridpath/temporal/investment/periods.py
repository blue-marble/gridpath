#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describes the relationships among timepoints in the optimization
"""

import os.path

from pyomo.environ import Set, Param, NonNegativeReals, NonNegativeIntegers


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.PERIODS = Set(within=NonNegativeIntegers, ordered=True)
    m.discount_factor = Param(m.PERIODS, within=NonNegativeReals)
    m.number_years_represented = Param(m.PERIODS, within=NonNegativeReals)

    m.period = Param(m.TIMEPOINTS, within=m.PERIODS)

    m.TIMEPOINTS_IN_PERIOD = \
        Set(m.PERIODS,
            initialize=lambda mod, p:
            set(tmp for tmp in mod.TIMEPOINTS if mod.period[tmp] == p))

    # Figure out which one is the first period and the previous
    # period for each period other than the first period
    m.first_period = Param(within=m.PERIODS,
                           initialize=lambda mod: list(mod.PERIODS)[0])
    m.NOT_FIRST_PERIODS = Set(within=m.PERIODS,
                                initialize=lambda mod: list(mod.PERIODS)[1:])

    m.previous_period = Param(m.NOT_FIRST_PERIODS,
                              initialize=lambda mod, p:
                              list(mod.PERIODS)[list(mod.PERIODS).index(p)-1]
                              )

def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "periods.tab"),
                     select=("PERIODS", "discount_factor",
                             "number_years_represented"),
                     index=m.PERIODS,
                     param=(m.discount_factor, m.number_years_represented)
                     )

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "timepoints.tab"),
                     select=("TIMEPOINTS","period"),
                     index=m.TIMEPOINTS,
                     param=m.period
                     )
