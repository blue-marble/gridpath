#!/usr/bin/env python
import os
import csv

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """

    # TODO: iterate through generator types and get correct rule instead of
    # if statements
    def power_provision_rule(mod, g, tmp):
        if mod.must_run[g]:
            return mod.Must_Run_Power[g, tmp]
        elif mod.variable[g]:
            return mod.Variable_Power[g, tmp]
        elif mod.dispatchable[g]:
            return mod.Dispatchable_Power[g, tmp]

    m.Power_Provision = Expression(m.GENERATORS, m.TIMEPOINTS,
                                   rule=power_provision_rule)

