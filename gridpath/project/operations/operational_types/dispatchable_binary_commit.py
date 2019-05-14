#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'binary-commit' generators,
i.e. generators with on/off commitment decisions.
"""

from __future__ import division

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Binary, PercentFraction, Integers, Expression, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    First, we determine the project subset with 'dispatchable_binary_commit'
    as operational type. This is the *DISPATCHABLE_BINARY_COMMIT_GENERATORS*
    set, which we also designate with :math:`BCG\subset R` and index
    :math:`bcg`.

    We define the minimum stable level parameters over :math:`AGO`: \n
    *dispbincommit_min_stable_level_fraction* \ :sub:`aog`\ -- the
    minimum stable level of the dispatchable-binary-commit generator, defined
    as a fraction its capacity \n

    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`BCG\_OT\subset RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a
    'dispatchable_binary_commit' project can be operational.

    Commit_Binary is the binary commit variable to represent 'on' or 'off'
    state of a generator. It is defined over over
    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    Provide_Power_DispBinaryCommit_MW is the power provision variable for
    the generator. It is defined over is defined over
    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    The main constraints on dispatchable-binary-commit generator power
    provision are as follows:

    For :math:`(bcg, tmp) \in BCG\_OT`: \n
    :math:`Provide\_Power\_DispBinaryCommit\_MW_{bcg, tmp} \geq
    Commit\_MW_{bcg, tmp} \\times disp\_binary\_commit\_min\_stable\_level
    \_fraction \\times Capacity\_MW_{bcg,p}` \n
    :math:`Provide\_Power\_DispBinaryCommit\_MW_{bcg, tmp} \leq
    Commit\_MW_{bcg, tmp} \\times Capacity\_MW_{bcg,p}`

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

    m.dispbincommit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction)
    # Assume this is the start up ramp rate as defined in Knueven 2018
    # Units are MW/hour
    m.dispbincommit_startup_plus_ramp_up_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=9999)
    m.dispbincommit_shutdown_plus_ramp_down_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=9999)
    m.dispbincommit_ramp_up_when_on_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=9999)
    m.dispbincommit_ramp_down_when_on_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=9999)
    # TODO: should't this default to zero since 1 can still be binding
    #   when doing subhourly modeling (15 min timepoints)
    m.dispbincommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=Integers, default=1)
    m.dispbincommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=Integers, default=1)

    # Variables - Binary
    m.Commit_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    m.Start_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    m.Stop_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    # Variables - Continuous
    m.Provide_Power_Above_Pmin_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    m.Available_Power_Above_Pmin_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Expressions
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.DispBinCommit_Upwards_Reserves_MW = Expression(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.DispBinCommit_Downwards_Reserves_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)

    def pmax_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]]
    m.DispBinCommit_Pmax_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmax_rule)

    def pmin_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.dispbincommit_min_stable_level_fraction[g]
    m.DispBinCommit_Pmin_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmin_rule)

    def provide_power_rule(mod, g, tmp):
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] \
            + mod.DispBinCommit_Pmin_MW[g, tmp] \
            * mod.Commit_Binary[g, tmp]
    m.Provide_Power_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=provide_power_rule)

    # Constraints
    def binary_logic_rule(mod, g, tmp):
        """
        If commit status changes, unit is starting or stopping.
        The *Start_Binary* variable is 1 for the first timepoint the unit is
        committed after being offline; it will be able to provide power in that
        timepoint. The *Stop_Binary* variable is 1 for the first timepoint the
        unit is not committed after being online; it will not be able to
        provide power in that timepoint.
        Constraint (2) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: input commit from previous horizon last tmp if linear boundary?
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return (mod.Commit_Binary[g, tmp] -
                    mod.Commit_Binary[g, mod.previous_timepoint[tmp]]) \
                == mod.Start_Binary[g, tmp] - mod.Stop_Binary[g, tmp]
    m.DispBinCommit_Binary_Logic_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=binary_logic_rule
        )

    def min_up_time_rule(mod, g, tmp):
        """
        When units are started, they have to stay on for a minimum number
        of hours described by the dispbincommit_min_up_time_hours parameter
        Constraint (4) from Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: this constraint assumes that hours per timepoint stays
        #   constant, but timepoints.py does not state this
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # TODO: enforce subhourly?
        elif mod.dispbincommit_min_up_time_hours[g] <= 1:
            return Constraint.Skip
        else:
            relevant_tmps = list()
            relevant_tmp = tmp
            n_timepoints_in_min_up_time = \
                int(mod.dispbincommit_min_up_time_hours[g]
                    / mod.number_of_hours_in_timepoint[tmp])

            # build list of relevant tmps: start at relevant tmp and go down to
            # min_up_time_hours before the relevant tmp.
            for n in range(1, n_timepoints_in_min_up_time + 1):
                relevant_tmps.append(relevant_tmp)
                # If horizon is 'linear' and we reach the first timepoint,
                # skip the constraint; this means we are skipping the
                # the constraint for all timepoints less than min_up_time
                # from the start of the horizon, which is consistent with
                # Knueven et al. (2018)
                if relevant_tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp]] \
                        and mod.boundary[mod.horizon[tmp]] == "linear":
                    return Constraint.Skip
                else:
                    relevant_tmp = mod.previous_timepoint[relevant_tmp]

            # units_started is 1 if there were any starts
            # min_up_time_or_less_hours_ago; otherwise it is 0.
            units_started_min_up_time_or_less_hours_ago = \
                sum(mod.Start_Binary[g, tp] for tp in relevant_tmps)

            # If there was a start min_up_time_or_less_hours_ago,
            # Commit_Binary has to be one (i.e. you have to stay offline)
            return mod.Commit_Binary[g, tmp] \
                >= units_started_min_up_time_or_less_hours_ago
    m.DispBinCommit_Min_Up_Time_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_up_time_rule
        )

    def min_down_time_rule(mod, g, tmp):
        """
        When units are stopped, they have to stay off for a minimum number
        of hours described by the dispbincommit_min_down_time_hours parameter
        If using linear horizons, this constraint is skipped for the timepoints
        within min_down_time hours from the start of the horizon (each constraint
        looks back min_down_time hours so the first timepoints are covered by
        the constraint of the first timepoint after min_down_time hours).
        Constraint (5) from Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # TODO: this constraint assumes that hours per timepoint stays
        #   constant, but timepoints.py does not state this
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # TODO: enforce subhourly?
        elif mod.dispbincommit_min_down_time_hours[g] <= 1:
            return Constraint.Skip
        else:
            relevant_tmps = list()
            relevant_tmp = tmp
            n_timepoints_in_min_down_time = \
                int(mod.dispbincommit_min_down_time_hours[g]
                    / mod.number_of_hours_in_timepoint[tmp])

            # build list of relevant tmps: start at relevant tmp and go down to
            # min_down_time_hours before the relevant tmp.
            for n in range(1, n_timepoints_in_min_down_time + 1):
                relevant_tmps.append(relevant_tmp)
                # If horizon is 'linear' and we reach the first timepoint,
                # skip the constraint; this means we are skipping the
                # the constraint for all timepoints less than min_down_time
                # from the start of the horizon, which is consistent with
                # Knueven et al. (2018)
                if relevant_tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp]] \
                        and mod.boundary[mod.horizon[tmp]] == "linear":
                    return Constraint.Skip
                else:
                    relevant_tmp = mod.previous_timepoint[relevant_tmp]

            # unit_stopped is 1 if there were any stops
            # min_down_time_or_less_hours_ago; otherwise it is 0.
            units_stopped_min_down_time_or_less_hours_ago = \
                sum(mod.Stop_Binary[g, tp] for tp in relevant_tmps)

            # If there was a stop min_down_time_or_less_hours_ago,
            # Commit_Binary has to be zero (i.e. you have to stay offline)
            return 1 - mod.Commit_Binary[g, tmp] \
                >= units_stopped_min_down_time_or_less_hours_ago
    m.DispBinCommit_Min_Down_Time_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_down_time_rule
        )

    def max_power_rule(mod, g, tmp):
        """
        Total power provision can't be above generator's maximum power output
        Also ensure total capacity is not above startup or shutdown ramp rate
        if unit is starting in this timepoint or stopping the next timepoint.
        Constraint only applies when min_up_time is larger than the
        number_of_hour_in_timepoint, i.e. when you can't start in one
        timepoint and shutdown on the next timepoint (there are 2 other
        constraints to cover that situation)
        Constraint (20) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if mod.dispbincommit_min_up_time_hours[g] \
                <= mod.number_of_hours_in_timepoint[tmp]:
            return Constraint.Skip
        elif tmp == mod.last_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                    + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
                <= \
                (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.DispBinCommit_Pmin_MW[g, tmp]) \
                * mod.Commit_Binary[g, tmp] \
                - (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.dispbincommit_startup_plus_ramp_up_rate[g]
                    * mod.number_of_hours_in_timepoint[tmp]) \
                * mod.Start_Binary[g, tmp] \
                - (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.dispbincommit_shutdown_plus_ramp_down_rate[g]
                    * mod.number_of_hours_in_timepoint[tmp]
                    * mod.availability_derate[g, mod.horizon[tmp]]) \
                * mod.Stop_Binary[g, mod.next_timepoint[tmp]]
    m.Max_Power_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_rule
    )

    def max_power_startup_rule(mod, g, tmp):
        """
        Total power provision can't be above generator's maximum power output
        Also ensure total capacity is not above startup ramp rate if unit
        is starting in this timepoint.
        Constraint (21a) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if mod.dispbincommit_min_up_time_hours[g] \
                > mod.number_of_hours_in_timepoint[tmp]:
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                    + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
                <= \
                (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.DispBinCommit_Pmin_MW[g, tmp]) \
                * mod.Commit_Binary[g, tmp] \
                - (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.dispbincommit_startup_plus_ramp_up_rate[g]
                    * mod.number_of_hours_in_timepoint[tmp]
                    * mod.availability_derate[g, mod.horizon[tmp]]) \
                * mod.Start_Binary[g, tmp]
    m.Max_Power_Startup_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_startup_rule
    )

    def max_power_shutdown_rule(mod, g, tmp):
        """
        Total power provision can't be above generator's maximum power output
        Also ensure total capacity is not above shutdown ramp rate if unit
        is shutting down the next timepoint.
        Constraint (21b) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if mod.dispbincommit_min_up_time_hours[g] \
                > mod.number_of_hours_in_timepoint[tmp]:
            return Constraint.Skip
        elif tmp == mod.last_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                    + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
                <= \
                (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.DispBinCommit_Pmin_MW[g, tmp]) \
                * mod.Commit_Binary[g, tmp] \
                - (mod.DispBinCommit_Pmax_MW[g, tmp]
                    - mod.dispbincommit_shutdown_plus_ramp_down_rate[g]
                    * mod.number_of_hours_in_timepoint[tmp]
                    * mod.availability_derate[g, mod.horizon[tmp]]) \
                * mod.Stop_Binary[g, mod.next_timepoint[tmp]]
    m.Max_Power_Shutdown_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_shutdown_rule
    )

    def ramp_up_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints has to
        obey ramp up rates.
        Constraint (26) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                    + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
                - (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[
                       g, mod.previous_timepoint[tmp]]
                   - mod.DispBinCommit_Downwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp]]) \
                <= mod.dispbincommit_ramp_up_when_on_rate[g] \
                * mod.number_of_hours_in_timepoint[tmp] \
                * mod.availability_derate[g, mod.horizon[tmp]]
    m.Ramp_Up_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_rule
    )

    def ramp_down_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints has to
        obey ramp down rates.
        Constraint (27) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[
                       g, mod.previous_timepoint[tmp]]
                    + mod.DispBinCommit_Upwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp]]) \
                - (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                   - mod.DispBinCommit_Downwards_Reserves_MW[g, tmp]) \
                <= mod.dispbincommit_ramp_up_when_on_rate[g] \
                * mod.number_of_hours_in_timepoint[tmp] \
                * mod.availability_derate[g, mod.horizon[tmp]]
    m.Ramp_Down_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_rule
    )

    def min_power_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below minimum stable level.
        This constraint is not in Knueven et al. (2018) because they don't
        look at downward reserves. In that case, enforcing
        provide_power_above_pmin to be within NonNegativeReals is sufficient.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] - \
            mod.DispBinCommit_Downwards_Reserves_MW[g, tmp] \
            >= 0
    m.DispBinCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by dispatchable-binary-commit
     generators

    Power provision for dispatchable-binary-commit generators is a
    variable constrained to be between the generator's minimum stable level
    and its capacity if the generator is committed and 0 otherwise.
    """
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


# RPS
def rec_provision_rule(mod, g, tmp):
    """
    REC provision of dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    # TODO: shouldn't we return MW here to make this general?
    return mod.Commit_Binary[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    return mod.DispBinCommit_Pmax_MW[g, tmp] \
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
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.minimum_input_mmbtu_per_hr[g] \
            + mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] \
            * mod.inc_heat_rate_mmbtu_per_mwh[g]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    Returns the number of MWs that are started up or shut down.
    Will be positive when there are more generators committed in the current
    timepoint than there were in the previous timepoint.
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
        # TODO: split out pmax into pmax of current timepoint and pmax
        #   of previous timepoint? (in case the availability derate changes)
        return (mod.Commit_Binary[g, tmp]
                - mod.Commit_Binary[g, mod.previous_timepoint[tmp]]) * \
               mod.DispBinCommit_Pmax_MW[g, tmp]


def ramp_rule(mod, g, tmp):
    """
    Ramp between this timepoint and the previous timepoint
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] - \
               mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[
                    g, mod.previous_timepoint[tmp]]


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
    startup_plus_ramp_up_rate = dict()
    shutdown_plus_ramp_down_rate = dict()
    ramp_up_when_on_rate = dict()
    ramp_down_when_on_rate = dict()
    min_up_time = dict()
    min_down_time = dict()

    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["startup_plus_ramp_up_rate",
                        "shutdown_plus_ramp_down_rate",
                        "ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours",
                        "min_down_time_hours"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "operational_type",
                     "min_stable_level_fraction"] + used_columns
            )

    # todo: remove this since not used?
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "dispatchable_binary_commit":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass

    data_portal.data()["dispbincommit_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional, will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_plus_ramp_up_rate"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_up_time_hours"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                min_up_time[row[0]] = int(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_min_up_time_hours"] = \
            min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_down_time_hours"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                min_down_time[row[0]] = int(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_min_down_time_hours"] = \
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
                value(mod.DispBinCommit_Pmax_MW[p, tmp])
                * value(mod.Commit_Binary[p, tmp]),
                value(mod.Commit_Binary[p, tmp])
            ])
# TODO: also output unit starts and stops? (and MW start/stop?)
#  might be output somewhere else already
