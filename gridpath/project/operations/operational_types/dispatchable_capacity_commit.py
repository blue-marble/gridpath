#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of dispatchable generators with 'capacity commitment,' i.e.
commit some level of capacity below the total capacity. This approach can
be good for modeling 'fleets' of generators, e.g. a total 2000 MW of 500-MW
units, so if 2000 MW are committed 4 generators (x 500 MW) are committed.
Integer commitment is not enforced as capacity commitment with this approach is
continuous.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Constraint, Param, NonNegativeReals, \
    PercentFraction, Expression, Integers, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :param d:
    :return:
    """

    # Sets and params
    m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "dispatchable_capacity_commit")
    )

    m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS))
    
    m.unit_size_mw = Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
                           within=NonNegativeReals)
    m.disp_cap_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction)
    m.dispcapcommit_ramp_rate_up_frac_of_capacity_per_hour = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcapcommit_ramp_rate_down_frac_of_capacity_per_hour = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcapcommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=Integers, default=1)
    m.dispcapcommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=Integers, default=1)

    # Variables
    # Dispatch
    m.Provide_Power_DispCapacityCommit_MW = \
        Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    # Commitment
    m.Commit_Capacity_MW = \
        Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals
            )

    # Operational constraints
    def commit_capacity_constraint_rule(mod, g, tmp):
        """
        Can't commit more capacity than available in each timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Commit_Capacity_MW[g, tmp] \
            <= mod.Capacity_MW[g, mod.period[tmp]]
    m.Commit_Capacity_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=commit_capacity_constraint_rule)

    def max_power_rule(mod, g, tmp):
        """
        Power plus upward services cannot exceed capacity.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Commit_Capacity_MW[g, tmp]
    m.DispCapCommit_Max_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= mod.Commit_Capacity_MW[g, tmp] \
            * mod.disp_cap_commit_min_stable_level_fraction[g]
    m.DispCapCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )

    # Optional
    # Constrain ramps

    def ramp_up_constraint_rule(mod, g, tmp):
        """
        The ramp up (power provided in the current timepoint minus power
        provided in the previous timepoint) cannot exceed a prespecified
        ramp rate (expressed as fraction of capacity)
        Two components:
        1) if we are turning generators on, we will allow the extra ramp of
        going from 0 to minimum stable level (if generators are turning off,
        the ramp up allowed is reduced since committed capacity in current
        minus committed capacity in previous timepoint will be negative)
        2) units committed in the current timepoint could have ramped up at a
        certain rate since the previous timepoint
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif mod.dispcapcommit_ramp_rate_up_frac_of_capacity_per_hour[g] >= \
                (1-mod.disp_cap_commit_min_stable_level_fraction[g]):
            return Constraint.Skip  # constraint won't bind, so don't create
        else:
            return (
                mod.Provide_Power_DispCapacityCommit_MW[g, tmp]
                - mod.Provide_Power_DispCapacityCommit_MW[
                g, mod.previous_timepoint[tmp]]
                   ) \
                / mod.number_of_hours_in_timepoint[tmp] \
                <= \
                (mod.Commit_Capacity_MW[g, tmp]
                    - mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]) \
                * mod.disp_cap_commit_min_stable_level_fraction[g] \
                + \
                mod.Commit_Capacity_MW[g, tmp] \
                * mod.dispcapcommit_ramp_rate_up_frac_of_capacity_per_hour[g]
    m.DispCapCommit_Ramp_Up_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_constraint_rule
    )

    def ramp_down_constraint_rule(mod, g, tmp):
        """
        The ramp down (power provided in the current timepoint minus power
        provided in the previous timepoint) cannot exceed a prespecified
        ramp rate (expressed as fraction of capacity)
        Two components:
        1) if we are turning generators off, we will allow the extra ramp of
        going from minimum stable level to 0 (if generators are turning on,
        the ramp up allowed is reduced since committed capacity in current
        minus committed capacity in previous timepoint will be positive)
        2) units committed in the current timepoint could have ramped down at a
        certain rate since the previous timepoint
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif mod.dispcapcommit_ramp_rate_down_frac_of_capacity_per_hour[g] >= \
                (1-mod.disp_cap_commit_min_stable_level_fraction[g]):
            return Constraint.Skip  # constraint won't bind, so don't create
        else:
            return (
                mod.Provide_Power_DispCapacityCommit_MW[g, tmp]
                - mod.Provide_Power_DispCapacityCommit_MW[
                g, mod.previous_timepoint[tmp]]
                   ) \
                / mod.number_of_hours_in_timepoint[tmp] \
                >= \
                (mod.Commit_Capacity_MW[g, tmp]
                    - mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]) \
                * mod.disp_cap_commit_min_stable_level_fraction[g] \
                + \
                mod.Commit_Capacity_MW[g, tmp] \
                * \
                - mod.dispcapcommit_ramp_rate_down_frac_of_capacity_per_hour[g]
    m.DispCapCommit_Ramp_Down_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_constraint_rule
    )

    # Constrain up and down time
    # Startup and shutdown variables, must be non-negative
    m.DispCapCommit_Startup_MW = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )
    m.DispCapCommit_Shutdown_MW = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    def startup_constraint_rule(mod, g, tmp):
        """
        When units are shut off, DispCapCommit_Startup_MW will be 0 (as it
        has to be non-negative)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return mod.DispCapCommit_Startup_MW[g, tmp] \
                >= mod.Commit_Capacity_MW[g, tmp] \
                - mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]

    m.DispCapCommit_Startup_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_constraint_rule
    )

    def shutdown_constraint_rule(mod, g, tmp):
        """
        When units are turned on, DispCapCommit_Shutdown_MW will be 0 (as it
        has to be non-negative)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return mod.DispCapCommit_Shutdown_MW[g, tmp] \
                >= mod.Commit_Capacity_MW[g, tmp] \
                - mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]

    m.DispCapCommit_Shutdown_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_constraint_rule
    )

    def min_up_time_constraint_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # TODO: enforce subhourly?
        elif mod.dispcapcommit_min_up_time_hours[g] <= 1:
            return Constraint.Skip
        else:
            relevant_tmps = list()
            current_tmp = tmp

            for n in range(1,
                           int(mod.dispcapcommit_min_up_time_hours[g] /
                               mod.number_of_hours_in_timepoint[tmp]) + 1):
                relevant_tmps.append(current_tmp)
                # If horizon is 'linear' and we reach the first timepoint,
                # skip the constraint
                if current_tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp]] \
                        and mod.boundary[mod.horizon[tmp]] == "linear":
                    return Constraint.Skip
                else:
                    current_tmp = mod.previous_timepoint[current_tmp]

            units_turned_on_min_up_time_or_less_hours_ago = \
                sum(mod.DispCapCommit_Startup_MW[g, tp]
                    for tp in relevant_tmps)

            return mod.Commit_Capacity_MW[g, tmp] \
                >= units_turned_on_min_up_time_or_less_hours_ago

    m.DispCapCommit_Min_Up_Time_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_up_time_constraint_rule
    )

    def min_down_time_constraint_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # TODO: enforce subhourly?
        if mod.dispcapcommit_min_up_time_hours[g] <= 1:
            return Constraint.Skip
        else:
            relevant_tmps = list()
            current_tmp = tmp

            for n in range(1,
                           int(mod.dispcapcommit_min_down_time_hours[g] /
                               mod.number_of_hours_in_timepoint[tmp]) + 1):
                relevant_tmps.append(current_tmp)
                # If horizon is 'linear' and we reach the first timepoint,
                # skip the constraint
                if current_tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp]] \
                        and mod.boundary[mod.horizon[tmp]] == "linear":
                    return Constraint.Skip
                else:
                    current_tmp = mod.previous_timepoint[current_tmp]

            units_turned_off_min_up_time_or_less_hours_ago = \
                sum(mod.DispCapCommit_Shutdown_MW[g, tp]
                    for tp in relevant_tmps)

            return mod.Capacity_MW[g, mod.period[tmp]] \
                - mod.Commit_Capacity_MW[g, tmp] \
                >= units_turned_off_min_up_time_or_less_hours_ago

    m.DispCapCommit_Min_Down_Time_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_down_time_constraint_rule
    )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispCapacityCommit_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Number of units committed is the committed capacity divided by the unit
    size
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Commit_Capacity_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down and use energy (fuel) later
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: figure out how this should work with fleets (unit size here or in data)
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
    return ((mod.Commit_Capacity_MW[g, tmp]/mod.unit_size_mw[g])
            * mod.minimum_input_mmbtu_per_hr[g]
            + (mod.Provide_Power_DispCapacityCommit_MW[g, tmp] -
               (mod.Commit_Capacity_MW[g, tmp]
                * mod.disp_cap_commit_min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
            ) * mod.fuel_price_per_mmbtu[mod.fuel[g]]


# TODO: startup/shutdown cost per unit won't work without additional info
# about unit size vs total fleet size if modeling a fleet with this module
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
        return (mod.Commit_Capacity_MW[g, tmp]
                - mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]
                ) \
               / mod.unit_size_mw[g]


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
        return (mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]
                - mod.Commit_Capacity_MW[g, tmp]) \
               / mod.unit_size_mw[g]


def fix_commitment(mod, g, tmp):
    """
    Fix committed capacity based on number of committed units and unit size
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Capacity_MW[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Capacity_MW[g, tmp].fixed = True


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

    unit_size_mw = dict()
    min_stable_fraction = dict()
    ramp_rate_up = dict()
    ramp_rate_down = dict()
    min_up_time = dict()
    min_down_time = dict()

    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["ramp_rate_up_frac_of_capacity_per_hour",
                        "ramp_rate_down_frac_of_capacity_per_hour",
                        "min_up_time_hours", "min_down_time_hours"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", 
            usecols=["project", "operational_type", "unit_size_mw", 
                     "min_stable_level_fraction"] + used_columns
            )

    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["unit_size_mw"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "dispatchable_capacity_commit":
            unit_size_mw[row[0]] = float(row[2])
            min_stable_fraction[row[0]] = float(row[3])
        else:
            pass

    data_portal.data()["unit_size_mw"] = unit_size_mw
    data_portal.data()["disp_cap_commit_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional, will default to 1 if not specified
    if "ramp_rate_up_frac_of_capacity_per_hour" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "ramp_rate_up_frac_of_capacity_per_hour"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                ramp_rate_up[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_ramp_rate_up_frac_of_capacity_per_hour"] = \
            ramp_rate_up

    if "ramp_rate_down_frac_of_capacity_per_hour" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "ramp_rate_down_frac_of_capacity_per_hour"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                ramp_rate_down[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_ramp_rate_down_frac_of_capacity_per_hour"] = \
            ramp_rate_down
        
    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "min_up_time_hours"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                min_up_time[row[0]] = int(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_min_up_time_hours"] = \
            min_up_time
        
    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "min_down_time_hours"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                min_down_time[row[0]] = int(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_min_down_time_hours"] = \
            min_down_time


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
                           "dispatch_capacity_commit.csv"), "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "power_mw", "committed_mw", "committed_units"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                value(mod.Provide_Power_DispCapacityCommit_MW[p, tmp]),
                value(mod.Commit_Capacity_MW[p, tmp]),
                value(mod.Commit_Capacity_MW[p, tmp])/mod.unit_size_mw[p]
            ])
