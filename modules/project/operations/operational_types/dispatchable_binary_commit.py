#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

from pyomo.environ import Var, Set, NonNegativeReals, Binary

from modules.auxiliary.auxiliary import generator_subset_init, \
    make_project_time_var_df


def add_module_specific_components(m, scenario_directory):
    """
    Add a binary commit variable to represent 'on' or 'off' state of a
    generator.
    :param m:
    :param scenario_directory:
    :return:
    """

    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_binary_commit")
    )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS))

    m.Provide_Power_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    m.Commit_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


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
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] + \
        mod.Headroom_Provision_MW[g, tmp] \
        <= mod.Capacity_MW[g, mod.period[tmp]] * mod.Commit_Binary[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below a minimum stable level.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] - \
        mod.Footroom_Provision_MW[g, tmp] \
        >= mod.Commit_Binary[g, tmp] * mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.min_stable_level_fraction[g]


def curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_cost_rule(mod, g, tmp):
    """
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, i.e. a minimum MMBtu input to have the generator
    on plus incremental fuel use for each MWh above the minimum stable level of
    the generator.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return (mod.Commit_Binary[g, tmp]
            * mod.minimum_input_mmbtu_per_hr[g]
            + (mod.Provide_Power_DispBinaryCommit_MW[g, tmp] -
               (mod.Commit_Binary[g, tmp] * mod.Capacity_MW[g, mod.period[tmp]]
                * mod.min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
            ) * mod.fuel_price_per_mmbtu[mod.fuel[g].value]


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
    mod.Commit_Binary[g, tmp] = mod.fixed_commitment[g, tmp].value
    mod.Commit_Binary[g, tmp].fixed = True


def export_module_specific_results(mod, d):
    """
    Export commitment decisions.
    :param mod:
    :param d:
    :return:
    """
    binary_commit_df = \
        make_project_time_var_df(
            mod,
            "DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Commit_Binary",
            ["project", "timepoint"],
            "commit_binary"
        )

    d.module_specific_df.append(binary_commit_df)
