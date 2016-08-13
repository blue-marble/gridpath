#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os
import csv

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """

    def max_capacity_rule(mod, g, tmp):
        return mod.capacity[g]

    m.Unconstrained_Max_Power_in_Timepoint = Expression(m.UNCONSTRAINED_GENERATORS, m.TIMEPOINTS,
                                                        rule=max_capacity_rule)

    def min_capacity_rule(mod, g, tmp):
        return 0

    m.Unconstrained_Min_Power_in_Timepoint = Expression(m.UNCONSTRAINED_GENERATORS, m.TIMEPOINTS, rule=min_capacity_rule)

    def max_headroom_rule(mod, g, tmp):
        """
        Components can include upward reserves, regulation
        :param m:
        :param g:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, c)[g, tmp]
                   for c in mod.headroom_variables[g]) \
            <= mod.Provide_Headroom[g, tmp]
    m.Max_Headroom_Constraint = Constraint(m.UNCONSTRAINED_GENERATORS, m.TIMEPOINTS, rule=max_headroom_rule)

    def max_footroom_rule(mod, g, tmp):
        """
        Components can include upward reserves, regulation
        :param m:
        :param g:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, c)[g, tmp]
                   for c in mod.footroom_variables[g]) \
            <= mod.Provide_Footroom[g, tmp]
    m.Max_Footroom_Constraint = Constraint(m.UNCONSTRAINED_GENERATORS, m.TIMEPOINTS, rule=max_footroom_rule)


def export_results(m):
    for g in getattr(m, "UNCONSTRAINED_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Unconstrained_Max_Power_in_Timepoint[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Unconstrained_Max_Power_in_Timepoint[g, tmp].expr)
            )
            print("Unconstrained_Min_Power_in_Timepoint[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Unconstrained_Min_Power_in_Timepoint[g, tmp].expr)
                  )

