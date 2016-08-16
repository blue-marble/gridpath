#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os

from pyomo.environ import *


def power_provision_rule(mod, g, tmp):
    """
    Power provision for must run generators is their capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.capacity[g]


def max_power_rule(mod, g, tmp):
    """
    No variables to constrain for must-run generators.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return Constraint.Skip


def min_power_rule(mod, g, tmp):
    """
    No variables to constrain for must-run generators.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return Constraint.Skip