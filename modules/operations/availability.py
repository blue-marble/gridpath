#!/usr/bin/env python
import os
import csv

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """
    # RHS expressions
    # (variables will vary by generator type and will be populated by generator
    # type modules)
    def max_power_availability_rule(mod, g, tmp):
        if mod.must_run[g]:
            return mod.Must_Run_Min_Power_in_Timepoint[g, tmp]
        elif mod.variable[g]:
            return mod.Variable_Max_Power_in_Timepoint[g, tmp]
        else:
            return mod.Unconstrained_Max_Power_in_Timepoint[g, tmp]

    m.Max_Power_Availability_in_Timepoint = \
        Expression(m.GENERATORS,
                   m.TIMEPOINTS,
                   rule=max_power_availability_rule)

    def min_power_provision_rule(mod, g, tmp):
        if mod.must_run[g]:
            return mod.Must_Run_Min_Power_in_Timepoint[g, tmp]
        elif mod.variable[g]:
            return mod.Variable_Min_Power_in_Timepoint[g, tmp]
        else:
            return mod.Unconstrained_Min_Power_in_Timepoint[g, tmp]
    m.Min_Power_Provision_in_Timepoint = \
        Expression(m.GENERATORS,
                   m.TIMEPOINTS,
                   rule=min_power_provision_rule)


def export_results(m):
    for g in getattr(m, "GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print(
                "Max_Power_Availability_in_Timepoint[" + str(g) + ", "
                + str(tmp) + "]: "
                + str(m.Max_Power_Availability_in_Timepoint[g, tmp].expr)
            )