#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    Power plus upward services cannot exceed capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp] + \
        mod.Headroom_Provision_MW[g, tmp] \
        <= mod.capacity_mw[g]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below 0 (no commitment variable).
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp] - \
        mod.Footroom_Provision_MW[g, tmp] \
        >= 0


# TODO: what should these return -- what is the no-commit modeling?
def startup_rule(mod, g, tmp):
    """
    No commit variables, so shouldn't happen
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! No-commit generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! No-commit generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )
