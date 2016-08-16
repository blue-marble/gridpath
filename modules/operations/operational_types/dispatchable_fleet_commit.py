#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os
import csv

from pyomo.environ import *


def add_module_specific_components(m):
    """
    Add a continuous commit variable to represent the fraction of fleet
    capacity that is on.
    :param m:
    :return:
    """

    m.Commit_Fleet_Fraction = Var(m.DISPATCHABLE_FLEET_COMMIT_GENERATORS,
                                  m.TIMEPOINTS,
                                  bounds=(0, 1)
                                  )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    Power plus upward services cannot exceed capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power[g, tmp] + \
        sum(getattr(mod, c)[g, tmp]
            for c in mod.headroom_variables[g]) \
        <= mod.capacity[g] * mod.Commit_Fleet_Fraction[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below a minimum stable level.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power[g, tmp] - \
        sum(getattr(mod, c)[g, tmp]
            for c in mod.footroom_variables[g]) \
        >= mod.Commit_Fleet_Fraction[g, tmp] * mod.capacity[g] \
        * mod.min_stable_level[g]


def export_module_specific_results(mod):
    for g in getattr(mod, "DISPATCHABLE_FLEET_COMMIT_GENERATORS"):
        for tmp in getattr(mod, "TIMEPOINTS"):
            print("Commit_Fleet_Fraction[" + str(g) + ", " + str(tmp) + "]: "
                  + str(mod.Commit_Fleet_Fraction[g, tmp].value)
                  )
