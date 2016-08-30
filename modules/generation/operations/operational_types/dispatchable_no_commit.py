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


# TODO: add data check that minimum_input_mmbtu_per_hr is 0 for no-commit gens
def fuel_use_rule(mod, g, tmp):
    """
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, which is 0 for no-commit generators, so just
    multiply power by the incremental heat rate
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp] * mod.inc_heat_rate_mmbtu_per_mwh[g]


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
