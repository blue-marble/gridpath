#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

from pyomo.environ import Var, Set, Param, Binary

from ..auxiliary import make_gen_tmp_var_df


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
    return mod.Provide_Power_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    return mod.Commit_Binary[g, tmp]


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
        <= mod.capacity_mw[g] * mod.Commit_Binary[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below a minimum stable level.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp] - \
        mod.Footroom_Provision_MW[g, tmp] \
        >= mod.Commit_Binary[g, tmp] * mod.capacity_mw[g] \
        * mod.min_stable_level_fraction[g]


def startup_rule(mod, g, tmp):
    """
    Will be positive when there are more generators committed in the current
    timepoint that there were in the previous timepoint.
    If horizon is circular, the last timepoint of the horizon is the
    previous_timepoint for the first timepoint if the horizon;
    if the horizon is linear, no previous_timepoint is defined for the first
    timepoint of the horizon, so return 'None' here
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        return Non
    else:
        return mod.Commit_Binary[g, tmp] \
            - mod.Commit_Binary[g, mod.previous_timepoint[tmp]]


def shutdown_rule(mod, g, tmp):
    """
    Will be positive when there were more generators committed in the previous
    timepoint that there are in the current timepoint.
    If horizon is circular, the last timepoint of the horizon is the
    previous_timepoint for the first timepoint if the horizon;
    if the horizon is linear, no previous_timepoint is defined for the first
    timepoint of the horizon, so return 'None' here
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        return None
    else:
        return mod.Commit_Binary[g, mod.previous_timepoint[tmp]] \
            - mod.Commit_Binary[g, tmp]


def fix_commitment(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Binary[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Binary[g, tmp].fixed = True


def export_module_specific_results(mod):
    """
    Export commitment decisions.
    """
    continuous_commit_df = \
        make_gen_tmp_var_df(mod,
                            "DISPATCHABLE_BINARY_COMMIT_GENERATORS",
                            "TIMEPOINTS",
                            "Commit_Binary",
                            "commit_binary")

    mod.module_specific_df.append(continuous_commit_df)
