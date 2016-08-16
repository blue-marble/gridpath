#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os
import csv

from pyomo.environ import *


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
        <= mod.capacity[g]


# TODO: add min stable level
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
        >= 0
