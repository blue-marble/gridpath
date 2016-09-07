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
    return mod.Capacity_MW[g, mod.period[tmp]]


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


# TODO: add data check that inc_heat_rate_mmbtu_per_mwh is 0 for must-run gens
# TODO: change when can-build-new
def fuel_use_rule(mod, g, tmp):
    """
    Output doesn't vary, so this is
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.minimum_input_mmbtu_per_hr[g]


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
