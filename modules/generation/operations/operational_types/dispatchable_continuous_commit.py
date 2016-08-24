#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

from pyomo.environ import Var

from ..auxiliary import make_gen_tmp_var_df


def add_module_specific_components(m):
    """
    Add a continuous commit variable to represent the fraction of fleet
    capacity that is on.
    :param m:
    :return:
    """

    m.Commit_Continuous = Var(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
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


def commitment_rule(mod, g, tmp):
    return mod.Commit_Continuous[g, tmp]


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
        <= mod.capacity[g] * mod.Commit_Continuous[g, tmp]


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
        >= mod.Commit_Continuous[g, tmp] * mod.capacity[g] \
        * mod.min_stable_level[g]


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
        return None
    else:
        return mod.Commit_Continuous[g, tmp] \
            - mod.Commit_Continuous[g, mod.previous_timepoint[tmp]]


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
        return mod.Commit_Continuous[g, mod.previous_timepoint[tmp]] \
            - mod.Commit_Continuous[g, tmp]


def fix_commitment(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Continuous[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Continuous[g, tmp].fixed = True


def export_module_specific_results(mod):
    """
    Export commitment decisions.
    :param mod:
    :return:
    """

    continuous_commit_df = \
        make_gen_tmp_var_df(mod,
                            "DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS",
                            "TIMEPOINTS",
                            "Commit_Continuous",
                            "commit_continuous")

    mod.module_specific_df.append(continuous_commit_df)
