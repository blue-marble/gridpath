#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'binary-commit' generators,
i.e. generators with on/off commitment decisions.
"""

from builtins import zip
import csv
import os.path
from pandas import read_csv
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Binary, PercentFraction, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


# TODO: ramp rate limits, min up and down time, startups/shutdowns
def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    First, we determine the project subset with 'dispatchable_binary_commit'
    as operational type. This is the *DISPATCHABLE_BINARY_COMMIT_GENERATORS*
    set, which we also designate with :math:`BCG\subset R` and index
    :math:`bcg`.

    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`BCGT\subset RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a
    'dispatchable_binary_commit' project can be operational.

    Commit_Binary is the binary commit variable to represent 'on' or 'off'
    state of a generator.
    """
    # Sets and params
    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_binary_commit")
    )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS))

    m.disp_binary_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction)

    # Variables
    m.Provide_Power_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    m.Commit_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    # Operational constraints
    def max_power_rule(mod, g, tmp):
        """
        Power plus upward services cannot exceed capacity.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.Commit_Binary[g, tmp]
    m.DispBinCommit_Max_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below a minimum stable level.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= mod.Commit_Binary[g, tmp] \
            * mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.disp_binary_commit_min_stable_level_fraction[g]
    m.DispBinCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


# RPS
def rec_provision_rule(mod, g, tmp):
    """
    REC provision dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    return mod.Commit_Binary[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.availability_derate[g, mod.horizon[tmp]] \
        * mod.Commit_Binary[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, i.e. a minimum MMBtu input to have the generator
    on plus incremental fuel use for each MWh above the minimum stable level of
    the generator.
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.Commit_Binary[g, tmp] \
            * mod.minimum_input_mmbtu_per_hr[g] \
            + (mod.Provide_Power_DispBinaryCommit_MW[g, tmp] -
               (mod.Commit_Binary[g, tmp]
                * mod.Capacity_MW[g, mod.period[tmp]]
                * mod.availability_derate[g, mod.horizon[tmp]]
                * mod.disp_binary_commit_min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
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
        return (mod.Commit_Binary[g, tmp]
                - mod.Commit_Binary[g, mod.previous_timepoint[tmp]]) * \
               mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.availability_derate[g, mod.horizon[tmp]]


def ramp_rule(mod, g, tmp):
    """
    
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] - \
               mod.Provide_Power_DispBinaryCommit_MW[
                    g, mod.previous_timepoint[tmp]
                ]


def fix_commitment(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Binary[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Binary[g, tmp].fixed = True


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    min_stable_fraction = dict()
    dynamic_components = \
        read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project", "operational_type",
                               "min_stable_level_fraction"]
            )
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "dispatchable_binary_commit":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass

    data_portal.data()["disp_binary_commit_min_stable_level_fraction"] = \
        min_stable_fraction


def export_module_specific_results(mod, d, scenario_directory, horizon, stage):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "dispatch_binary_commit.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "committed_mw", "committed_units"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp]),
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp])
                * value(mod.Commit_Binary[p, tmp]),
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp])
            ])
