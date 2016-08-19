#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

from pyomo.environ import Constraint


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


def startup_rule(mod, g, tmp):
    """
    Must-run generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Must-run generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """
    Must-run generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Must-run generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )
