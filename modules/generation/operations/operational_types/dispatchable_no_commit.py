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
        mod.Headroom_Provision[g, tmp] \
        <= mod.capacity[g]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below 0 (no commitment variable).
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power[g, tmp] - \
        mod.Footroom_Provision[g, tmp] \
        >= 0


# TODO: should these return 'None' -- what is the no-commit modeling?
def startup_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return None


def shutdown_rule(mod, g, tmp):
    return None
