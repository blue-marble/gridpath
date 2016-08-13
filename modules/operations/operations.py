#!/usr/bin/env python
import os
import csv

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """

    # Constrain operations
    def max_power_rule(mod, g, tmp):
        return mod.Provide_Power[g, tmp] + mod.Provide_Headroom[g, tmp] \
               == mod.Max_Power_Availability_in_Timepoint[g, tmp]
    m.Max_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS,
                                        rule=max_power_rule)

    def min_power_rule(mod, g, tmp):
        return mod.Provide_Power[g, tmp] - mod.Provide_Footroom[g, tmp] \
               == mod.Min_Power_Provision_in_Timepoint[g, tmp]
    m.Min_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS,
                                        rule=min_power_rule)
