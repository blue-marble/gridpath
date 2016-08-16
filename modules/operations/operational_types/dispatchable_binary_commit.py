#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os
import csv

from pyomo.environ import *


def add_module_specific_components(m):
    """
    Add a binary commit variable to represent 'on' or 'off' state of a
    generator.
    :param m:
    :return:
    """

    m.Commit_Binary = Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
                          m.TIMEPOINTS,
                          within=Binary)


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
        <= mod.capacity[g] * mod.Commit_Binary[g, tmp]


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
        >= mod.Commit_Binary[g, tmp] * mod.capacity[g] \
        * mod.min_stable_level[g]


def export_module_specific_results(mod):
    for g in getattr(mod, "DISPATCHABLE_BINARY_COMMIT_GENERATORS"):
        for tmp in getattr(mod, "TIMEPOINTS"):
            print("Commit_Binary[" + str(g) + ", " + str(tmp) + "]: "
                  + str(mod.Commit_Binary[g, tmp].value)
                  )
