#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'continuous-commit' generators,
i.e. generators with on/off commitment decisions, but with the binary
commitment decision relaxed. The relaxation replaces the binary variables
(commit, start, stop) with continuous variables within the range [0,1].

Except for this relaxation, the formulation is exactly the same as
*dispatchable_binary_commit*, which is based on
"Tight and compact MILP formulation for the thermal unit commitment problem"
(Morales-Espana et al. 2013), available online at
https://ieeexplore.ieee.org/abstract/document/6485014
"""

from __future__ import division

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    PercentFraction, Expression, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints

def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from
    First, we determine the project subset with 'dispatchable_continuous_commit'
    as operational type. This is the *DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS*
    set, which we also designate with :math:`CCG\subset R` and index
    :math:`ccg`.

    We define several operational parameters over :math:`CCG`: \n
    *dispcontcommit_min_stable_level_fraction* \ :sub:`ccg`\ -- the
    minimum stable level of the dispatchable-continuous-commit generator,
    defined as a fraction its capacity \n
    *dispcontcommit_startup_plus_ramp_up_rate* \ :sub:`ccg`\ -- the project's
    upward ramp rate limit during startup, defined as a fraction of its capacity
    per minute. This param, adjusted for timepoint duration, has to be equal or
    larger than *dispcontcommit_min_stable_level_fraction* for the unit to be
    able to start up between timepoints. \n
    *dispcontcommit_shutdown_plus_ramp_down_rate* \ :sub:`ccg`\ -- the project's
    downward ramp rate limit during shutdown, defined as a fraction of its
    capacity per minute. This param, adjusted for timepoint duration, has to be
    equal or larger than *dispcontcommit_min_stable_level_fraction* for the
    unit to be able to shut down between timepoints. \n
    *dispcontcommit_ramp_up_when_on_rate* \ :sub:`ccg`\ -- the project's
    upward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n
    *dispcontcommit_ramp_down_when_on_rate* \ :sub:`ccg`\ -- the project's
    downward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n

    *DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`CCG\_OT\subset RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a
    'dispatchable_continuous_commit' project can be operational.


    There are three relaxed binary decision variables, and one continuous
    decision variable, all defined over
    *DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.
    Commit_Continuous is the relaxed binary commit variable to represent 'on' or
    'off' state of a generator.
    Start_Continuous is the relaxed binary variable to represent the state when a
    generator is turning on.
    Stop_Continuous is the relaxed binary variable to represent the state when a
    generator is shutting down.
    Provide_Power_Above_Pmin_DispContinuousCommit_MW is the power provision
    variable for the generator.

    The main constraints on dispatchable-continuous-commit generator power
    provision are as follows:
    For :math:`(ccg, tmp) \in CCG\_OT`: \n
    :math:`Provide\_Power\_DispContinuousCommit\_MW_{ccg, tmp} \geq
    Commit\_MW_{ccg, tmp} \\times disp\_continuous\_commit\_min\_stable\_level
    \_fraction \\times Capacity\_MW_{ccg,p}` \n
    :math:`Provide\_Power\_DispContinuousCommit\_MW_{ccg, tmp} \leq
    Commit\_MW_{ccg, tmp} \\times Capacity\_MW_{ccg,p}`

    TODO: add documentation on all constraints

    """
    # Sets
    m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "dispatchable_continuous_commit")
    )

    m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS))

    # Params - Required
    m.disp_cont_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=PercentFraction)

    # Params - Optional

    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    # Startup and shutdown ramp rate are defined as the amount you can
    # ramp when starting up or shutting down. When adjusted for the timepoint
    # duration, it should be at least equal to the min_stable_level_fraction
    m.dispcontcommit_startup_plus_ramp_up_rate = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcontcommit_shutdown_plus_ramp_down_rate = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcontcommit_ramp_up_when_on_rate = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcontcommit_ramp_down_when_on_rate = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=PercentFraction, default=1)

    m.dispcontcommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=NonNegativeReals, default=0)
    m.dispcontcommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS,
              within=NonNegativeReals, default=0)

    # Variables - Binary, relaxed
    m.Commit_Continuous = Var(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)
    # Start_Continuous is 1 for the first timepoint the unit is committed after
    # being offline; it will be able to provide power in that timepoint.
    m.Start_Continuous = Var(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)
    # Stop_Binary is 1 for the first timepoint the unit is offline after
    # being committed; it will not be able to provide power in that timepoint.
    m.Stop_Continuous = Var(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)

    # Variables - Continuous
    m.Provide_Power_Above_Pmin_DispContinuousCommit_MW = \
        Var(m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Expressions
    def pmax_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]]
    m.DispContCommit_Pmax_MW = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmax_rule)

    def pmin_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.disp_cont_commit_min_stable_level_fraction[g]
    m.DispContCommit_Pmin_MW = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmin_rule)

    def provide_power_rule(mod, g, tmp):
        return mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp] \
            + mod.DispContCommit_Pmin_MW[g, tmp] \
            * mod.Commit_Continuous[g, tmp]
    m.Provide_Power_DispContinuousCommit_MW = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=provide_power_rule)

    def ramp_up_rate_rule(mod, g, tmp):
        """
        Ramp up rate limit in MW per timepoint, derived from input ramp rate
        which is given in fraction of installed capacity per minute. Longer
        timepoints will lead to a larger ramp up rate limit, since ramping
        can take place over a longer duration.
        Unit check:
            capacity [MW]
            * availability [unit-less]
            * ramp up rate [1/min]
            * hours in timepoint [hours/timepoint]
            * minutes per hour [min/hour]
            = ramp up rate [MW/timepoint]
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.dispcontcommit_ramp_up_when_on_rate[g] \
            * mod.number_of_hours_in_timepoint[tmp] \
            * 60  # convert min to hours
    m.DispContCommit_Ramp_Up_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_rate_rule)

    def ramp_down_rate_rule(mod, g, tmp):
        """
        Ramp down rate limit in MW per timepoint, derived from input ramp rate
        which is given in fraction of installed capacity per minute. Longer
        timepoints will lead to a larger ramp down rate limit, since ramping
        can take place over a longer duration.
        Unit check:
            capacity [MW]
            * availability [unit-less]
            * ramp down rate [1/min]
            * hours in timepoint [hours/timepoint]
            * minutes per hour [min/hour]
            = ramp down rate [MW/timepoint]
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.dispcontcommit_ramp_down_when_on_rate[g] \
            * mod.number_of_hours_in_timepoint[tmp] \
            * 60  # convert min to hours
    m.DispContCommit_Ramp_Down_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_rate_rule)

    # Note: make sure to limit this to Pmax, otherwise max power rules break
    def startup_ramp_rate_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * min(mod.dispcontcommit_startup_plus_ramp_up_rate[g]
                  * mod.number_of_hours_in_timepoint[tmp]
                  * 60, 1)
    m.DispContCommit_Startup_Ramp_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_ramp_rate_rule)

    # Note: make sure to limit this to Pmax, otherwise max power rules break
    def shutdown_ramp_rate_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * min(mod.dispcontcommit_shutdown_plus_ramp_down_rate[g]
                  * mod.number_of_hours_in_timepoint[tmp]
                  * 60, 1)
    m.DispContCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_ramp_rate_rule)

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.DispContCommit_Upwards_Reserves_MW = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.DispContCommit_Downwards_Reserves_MW = Expression(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)

    # Constraints
    def binary_logic_constraint_rule(mod, g, tmp):
        """
        If commit status changes, unit is turning on or shutting down.
        The *Start_Continuous* variable is 1 for the first timepoint the unit is
        committed after being offline; it will be able to provide power in that
        timepoint. The *Stop_Continuous* variable is 1 for the first timepoint
        the unit is not committed after being online; it will not be able to
        provide power in that timepoint.
        Constraint (8) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: if we can link horizons, input commit from previous horizon's
        #  last timepoint rather than skipping the constraint
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
           return mod.Commit_Continuous[g, tmp] \
                  - mod.Commit_Continuous[g, mod.previous_timepoint[tmp]] \
                  == mod.Start_Continuous[g, tmp] - mod.Stop_Continuous[g, tmp]

    m.DispContCommit_Binary_Logic_Constraint = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=binary_logic_constraint_rule
    )

    def min_power_constraint_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below minimum stable level.
        This constraint is not in Morales-Espana et al. (2013) because they
        don't look at downward reserves. In that case, enforcing
        provide_power_above_pmin to be within NonNegativeReals is sufficient.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp] - \
            mod.DispContCommit_Downwards_Reserves_MW[g, tmp] \
            >= 0

    m.DispContCommit_Min_Power_Constraint = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_power_constraint_rule
    )

    def max_power_tightened_for_startup_constraint_rule(mod, g, tmp):
        """
        Power provision adjusted for upward reserves can't exceed generator's
        maximum power output. If the unit is starting up this timepoint,
        tighten the constraint to account for startup ramp limits.

        This constraint is part of a set of two maximum power constraints;
        one that tightens maximum power for startup ramp limits (this one), and
        one that tightens maximum power for shutdown ramp limits (next one).
        If the minimum up-time is larger than the timepoint duration, the unit
        can't start and immediately shut down the next timepoint, and a tighter,
        more compact formulation exists that tightens the maximum power for both
        startup ramps and shutdown ramps at the same time. In that case this
        constraint (and the next one) can be skipped and the tighter constraint
        can be applied instead.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; Therefore, if a unit is starting up in the current timepoint
        (binary start variable equal to 1), the ramping is assumed to take place
        during the previous timepoint, and we use the startup ramp rate that is
        adjusted for the previous timepoint duration.

        Constraint (9) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # If the minimum up-time is larger than the timepoint duration,a tighter
        # formulation is possible. Therefore, skip this constraint and apply
        # the tighter formulation instead.
        if mod.dispcontcommit_min_up_time_hours[g] \
                > mod.number_of_hours_in_timepoint[tmp]:
            return Constraint.Skip
        # *startup_ramp* equals the ramp rate limit during the previous
        # timepoint. If the horizon boundary is linear and we're at the first
        # timepoint in the horizon, there is no previous timepoint, so we'll
        # skip tightening the constraint for startup ramp rate limits by setting
        # startup_ramp equal to Pmax.
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            startup_ramp = mod.DispContCommit_Pmax_MW[g, tmp]
        else:
            startup_ramp = mod. \
                DispContCommit_Startup_Ramp_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp]]

        # Power provision plus upward reserves shall not exceed maximum power.
        # Constraint is further tightened if the unit is turning on, ensuring
        # that the unit does not exceed the startup ramp rate limits.
        return \
            (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp]
             + mod.DispContCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispContCommit_Pmax_MW[g, tmp]
             - mod.DispContCommit_Pmin_MW[g, tmp]) \
            * mod.Commit_Continuous[g, tmp] \
            - (mod.DispContCommit_Pmax_MW[g, tmp] - startup_ramp) \
            * mod.Start_Continuous[g, tmp]

    m.DispContCommit_Max_Power_Tightened_For_Startup_Constraint = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_tightened_for_startup_constraint_rule
    )

    def max_power_tightened_for_shutdown_constraint_rule(mod, g, tmp):
        """
        Power provision adjusted for upward reserves can't exceed generator's
        maximum power output. If the unit is shutting down the next timepoint,
        tighten the constraint to account for shutdown ramp limits.

        This constraint is part of a set of two maximum power constraints;
        one that tightens maximum power for startup ramp limits (previous one),
        and one that tightens maximum power for shutdown ramp limits (this one).
        If the minimum up-time is larger than the timepoint duration, the unit
        can't start and immediately shut down the next timepoint, and a tighter,
        more compact formulation exists that tightens the maximum power for both
        startup ramps and shutdown ramps at the same time. In that case this
        constraint (and the previous one) can be skipped and the tighter
        constraint can be applied instead.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; Therefore, if a unit is shutting down in the next timepoint
        (binary stop variable equal to 1), the ramping is assumed to take place
        during the current timepoint, and we use the shut down ramp rate that
        is adjusted for the current timepoint duration.

        Constraint (10) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # If the minimum up-time is larger than the timepoint duration,a tighter
        # formulation is possible. Therefore, skip this constraint and apply
        # the tighter formulation instead.
        if mod.dispcontcommit_min_up_time_hours[g] \
                > mod.number_of_hours_in_timepoint[tmp]:
            return Constraint.Skip
        # *stop_next_tmp* equals the value of the binary stop variable for the
        # next timepoint. If the horizon boundary is linear and we're at the
        # last timepoint in the horizon, there is no next timepoint, so we'll
        # assume that the value equals zero. This equivalent to "skipping" the
        # tightening of the constraint.
        if tmp == mod.last_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            stop_next_tmp = 0
        else:
            stop_next_tmp = mod.Stop_Continuous[g, mod.next_timepoint[tmp]]

        # Power provision plus upward reserves shall not exceed maximum power.
        # Constraint is further tightened if the unit is shutting down, ensuring
        # that the unit does not exceed the shutdown ramp rate limits.
        return \
            (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp]
             + mod.DispContCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispContCommit_Pmax_MW[g, tmp]
             - mod.DispContCommit_Pmin_MW[g, tmp]) \
            * mod.Commit_Continuous[g, tmp] \
            - (mod.DispContCommit_Pmax_MW[g, tmp]
               - mod.DispContCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint[g, tmp]
               ) \
            * stop_next_tmp

    m.DispContCommit_Max_Power_Tightened_For_Shutdown_Constraint = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_tightened_for_shutdown_constraint_rule
    )

    def max_power_tightened_for_startup_and_shutdown_constraint_rule(
            mod, g, tmp
    ):
        """
        Power provision adjusted for upward reserves can't exceed generator's
        maximum power output. If the unit is starting up this timepoint or
        shutting down the next timepoint, tighten the constraint to account for
        startup or shutdown ramp limits

        This constraint is a tighter, more compact formulation of the previous
        two maximum power constraints, combining the tightening for startup
        and shutdown ramping into one constraint. Combining the tightening for
        startup and shutdown ramp is only valid if only one tightening can be
        active at a time (if they are both active, you can get a negative
        RHS which would make the constraint infeasible).
        This is only the case if the mininum up-time disallows a unit from
        starting in one timepoint (which would activate the startup ramp
        tightening) and shutting down the next timepoint (which would activate
        the shutdown ramp tightening). Therefore, this constraint only applies
        when *min_up_time* is larger than the *number_of_hours_in_timepoint*.
        Conversely, if the minimum up-time is small enough that units can run
        for only one timepoint (start up one timepoint, shut down the next),
        this constraint should be skipped and the two other maximum power
        constraints that break out the tightening into two different constraints
        should be applied instead.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; Therefore, if a unit is shutting down in the next timepoint
        (binary stop variable equal to 1), the ramping is assumed to take place
        during the current timepoint, and we use the shut down ramp rate that
        is adjusted for the current timepoint duration. Similarly, if a unit is
        starting up in the current timepoint (binary start variable equal to 1),
        the ramping is assumed to take place during the previous timepoint, and
        we use the start up ramp rate that is adjusted for the previous
        timepoint duration.

        Constraint (11) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # If the minimum up time is smaller than or equal to the timepoint
        # duration, this compact version of the maximum power constraints is
        # too tight and can lead to a negative RHS, making it infeasible. In
        # that case, skip this constraint and apply two less tight maximum
        # power constraints that tighten for startup and shutdown separately.
        # (see above)
        if mod.dispcontcommit_min_up_time_hours[g] \
                <= mod.number_of_hours_in_timepoint[tmp]:
            return Constraint.Skip
        # *stop_next_tmp* equals the value of the binary stop variable for the
        # next timepoint. If the horizon boundary is linear and we're at the
        # last timepoint in the horizon, there is no next timepoint, so we'll
        # assume that the value equals zero. This equivalent to "skipping" the
        # tightening of the constraint.
        if tmp == mod.last_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            stop_next_tmp = 0
        else:
            stop_next_tmp = mod.Stop_Continuous[g, mod.next_timepoint[tmp]]
        # *startup_ramp* equals the ramp rate limit during the previous
        # timepoint. If the horizon boundary is linear and we're at the first
        # timepoint in the horizon, there is no previous timepoint, so we'll
        # skip tightening the constraint for startup ramp rate limits by setting
        # startup_ramp equal to Pmax.
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            startup_ramp = mod.DispContCommit_Pmax_MW[g, tmp]
        else:
            startup_ramp = mod. \
                DispContCommit_Startup_Ramp_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp]]

        # Power provision plus upward reserves shall not exceed maximum power.
        # Constraint is further tightened if the unit is turning on or shutting
        # down, ensuring that the unit does not exceed the startup/shutdown
        # ramp rate limits.
        return \
            (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp]
             + mod.DispContCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispContCommit_Pmax_MW[g, tmp]
             - mod.DispContCommit_Pmin_MW[g, tmp]) \
            * mod.Commit_Continuous[g, tmp] \
            - (mod.DispContCommit_Pmax_MW[g, tmp] - startup_ramp) \
            * mod.Start_Continuous[g, tmp] \
            - (mod.DispContCommit_Pmax_MW[g, tmp]
               - mod.DispContCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint[g, tmp]
               ) \
            * stop_next_tmp

    m.DispContCommit_Max_Power_Tightened_For_Startup_And_Shutdown_Constraint = \
        Constraint(
            m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=max_power_tightened_for_startup_and_shutdown_constraint_rule
        )

    def min_up_time_constraint_rule(mod, g, tmp):
        """
        When units are started, they have to stay on for a minimum number
        of hours described by the dispcontcommit_min_up_time_hours parameter.
        The constraint is enforced by ensuring that the continuous commitment
        is at least as large as the number of unit starts within min up time
        hours.

        We ensure a unit turned on less than the minimum up time ago is
        still on in the current timepoint *tmp* by checking how much units
        were turned on in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to dispcontcommit_min_up_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        starts.

        If using linear horizon boundaries, the constraint is skipped for all
        timepoints less than min up time hours from the start of the timepoint's
        horizon because the constraint for the first included timepoint
        will sufficiently constrain the continuous start variables of all the
        timepoints before it.

        Constraint (6) in Morales-Espana et al. (2013)

        Example 1:
          min_up_time = 4; tmps = [0,1,2,3];
          hours_in_tmps = [1,3,1,1];
          tmp = 2; relevant_tmps = [1,2]
          --> if there is a start in tmp 1, you have to be committed in tmp 2
          --> starts in all other tmps (incl. tmp 0) don't affect tmp 2
        Example 2:
          min_up_time = 4; tmps = [0,1,2,3];
          hours_in_tmps = [1,4,1,1];
          tmp = 2; relevant_tmps = [2]
          --> start in t1 does not affect state of t2; tmp 1 is 4 hrs long
          --> so even if you start in tmp 1 you can stop again in tmp 2
          --> The constraint simply ensures that the unit is committed if
          --> it is turned on.
        Example 3:
          min_up_time = 4; tmps = [0,1,2,3];
          hours_in_tmps = [1,1,1,1];
          tmp = 2; relevant_tmps = [0,1,2,3]
          --> if there is a start in tmp 0, 1, 2, or 3, you have to be committed
          --> in tmp 2. The unit either has to be on for all timepoints, or off
          --> for all timepoints
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        relevant_tmps = determine_relevant_timepoints(
            mod, tmp, mod.dispcontcommit_min_up_time_hours[g]
        )

        number_of_starts_min_up_time_or_less_hours_ago = \
            sum(mod.Start_Continuous[g, tp] for tp in relevant_tmps)

        # If we've reached the first timepoint in linear boundary mode and
        # the total duration of the relevant timepoints (which includes *tmp*)
        # is less than the minimum up time, skip the constraint since the next
        # timepoint's constraint will already cover these same timepoints.
        # Don't skip if this timepoint is the last timepoint of the horizon
        # (since there will be no next timepoint).
        if (mod.boundary[mod.horizon[tmp]] == "linear"
                and
                relevant_tmps[-1]
                == mod.first_horizon_timepoint[mod.horizon[tmp]]
                and
                sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
                < mod.dispcontcommit_min_up_time_hours[g]
                and
                tmp != mod.last_horizon_timepoint[mod.horizon[tmp]]):
            return Constraint.Skip
        # Otherwise, if there was a start min_up_time or less ago, the unit has
        # to remain committed.
        else:
            return mod.Commit_Continuous[g, tmp] \
                >= number_of_starts_min_up_time_or_less_hours_ago

    m.DispContCommit_Min_Up_Time_Constraint = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_up_time_constraint_rule
    )

    def min_down_time_constraint_rule(mod, g, tmp):
        """
        When units are shut down, they have to stay off for a minimum number
        of hours described by the dispcontcommit_min_down_time_hours parameter.
        The constraint is enforced by ensuring that (1-continuous commitment)
        is at least as large as the number of unit shutdowns within min down
        time hours.

        We ensure a unit shut down less than the minimum up time ago is
        still off in the current timepoint *tmp* by checking how much units
        were shut down in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to dispcontcommit_min_down_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        shutdowns.

        If using linear horizon boundaries, the constraint is skipped for all
        timepoints less than min down time hours from the start of the
        timepoint's horizon because the constraint for the first included
        timepoint will sufficiently constrain the continuous stop variables of all
        the timepoints before it.

        Constraint (7) in Morales-Espana et al. (2013)
        """

        relevant_tmps = determine_relevant_timepoints(
            mod, tmp, mod.dispcontcommit_min_down_time_hours[g]
        )

        number_of_stops_min_down_time_or_less_hours_ago = \
            sum(mod.Stop_Continuous[g, tp] for tp in relevant_tmps)

        # If we've reached the first timepoint in linear boundary mode and
        # the total duration of the relevant timepoints (which includes *tmp*)
        # is less than the minimum down time, skip the constraint since the
        # next timepoint's constraint will already cover these same timepoints.
        # Don't skip if this timepoint is the last timepoint of the horizon
        # (since there will be no next timepoint).
        if (mod.boundary[mod.horizon[tmp]] == "linear"
                and
                relevant_tmps[-1]
                == mod.first_horizon_timepoint[mod.horizon[tmp]]
                and
                sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
                < mod.dispcontcommit_min_down_time_hours[g]
                and
                tmp != mod.last_horizon_timepoint[mod.horizon[tmp]]):
            return Constraint.Skip
        # Otherwise, if there was a shutdown min_down_time or less ago, the unit
        # has to remain shut down.
        else:
            return 1 - mod.Commit_Continuous[g, tmp] \
                >= number_of_stops_min_down_time_or_less_hours_ago

    m.DispContCommit_Min_Down_Time_Constraint = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_down_time_constraint_rule
    )

    def ramp_up_constraint_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints has to
        obey ramp up rates.
        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate is adjusted for the duration of the first timepoint.
        Constraint (12) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp up the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.dispcontcommit_ramp_up_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[mod.previous_timepoint[tmp]]
              >= (1 - mod.disp_cont_commit_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp]
                 + mod.DispContCommit_Upwards_Reserves_MW[g, tmp]) \
                - \
                (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[
                     g, mod.previous_timepoint[tmp]]
                 - mod.DispContCommit_Downwards_Reserves_MW[
                     g, mod.previous_timepoint[tmp]]) \
                <= \
                mod.DispContCommit_Ramp_Up_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp]]

    m.Ramp_Up_Constraint_DispContinuousCommit = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_constraint_rule
    )

    def ramp_down_constraint_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints has to
        obey ramp down rates.
        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate is adjusted for the duration of the first timepoint.
        Constraint (13) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp down the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.dispcontcommit_ramp_down_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[mod.previous_timepoint[tmp]]
              >= (1 - mod.disp_cont_commit_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[
                     g, mod.previous_timepoint[tmp]]
                 + mod.DispContCommit_Upwards_Reserves_MW[
                     g, mod.previous_timepoint[tmp]]) \
                - \
                (mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp]
                 - mod.DispContCommit_Downwards_Reserves_MW[g, tmp]) \
                <= mod.DispContCommit_Ramp_Down_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp]]

    m.Ramp_Down_Constraint_DispContinuousCommit = Constraint(
        m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_constraint_rule
    )


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by dispatchable-continuous-commit
     generators
    Power provision for dispatchable-continuous-commit generators is a
    variable constrained to be between the generator's minimum stable level
    and its capacity if the generator is committed and 0 otherwise.
    """
    return mod.Provide_Power_DispContinuousCommit_MW[g, tmp]


# RPS
def rec_provision_rule(mod, g, tmp):
    """
    REC provision of dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispContinuousCommit_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    # TODO: shouldn't we return MW here to make this general?
    return mod.Commit_Continuous[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.DispContCommit_Pmax_MW[g, tmp] \
        * mod.Commit_Continuous[g, tmp]


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
        return mod.Commit_Continuous[g, tmp] \
               * mod.availability_derate[g, mod.horizon[tmp]] \
               * mod.minimum_input_mmbtu_per_hr[g] \
               + mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp] \
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
        return (mod.Commit_Continuous[g, tmp]
                - mod.Commit_Continuous[g, mod.previous_timepoint[tmp]]) \
            * mod.DispContCommit_Pmax_MW[g, tmp]


def power_delta_rule(mod, g, tmp):
    """
    Ramp between this timepoint and the previous timepoint
    Actual ramp rate in MW/hr depends on the duration of the timepoints.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[g, tmp] - \
            mod.Provide_Power_Above_Pmin_DispContinuousCommit_MW[
                g, mod.previous_timepoint[tmp]]


def fix_commitment(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Continuous[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Continuous[g, tmp].fixed = True


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

    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "dispatchable_continuous_commit":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass
    data_portal.data()["disp_cont_commit_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional, will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_plus_ramp_up_rate"]):
            if row[1] == "dispatchable_continuous_commit" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcontcommit_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]):
            if row[1] == "dispatchable_continuous_commit" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcontcommit_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]):
            if row[1] == "dispatchable_continuous_commit" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcontcommit_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]):
            if row[1] == "dispatchable_continuous_commit" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcontcommit_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_up_time_hours"]):
            if row[1] == "dispatchable_continuous_commit" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcontcommit_min_up_time_hours"] = \
            min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_down_time_hours"]):
            if row[1] == "dispatchable_continuous_commit" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcontcommit_min_down_time_hours"] = \
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
                           "dispatch_continuous_commit.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "committed_mw", "committed_units",
                         "started_units", "stopped_units"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Power_DispContinuousCommit_MW[p, tmp]),
                value(mod.DispContCommit_Pmax_MW[p, tmp])
                * value(mod.Commit_Continuous[p, tmp]),
                value(mod.Commit_Continuous[p, tmp]),
                value(mod.Start_Continuous[p, tmp]),
                value(mod.Stop_Continuous[p, tmp])
            ])


def import_module_specific_results_to_database(scenario_id, c, db,
                                               results_directory):
    """
    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("project dispatch continuous commit")
    # dispatch_continuous_commit.csv
    c.execute(
        """DELETE FROM results_project_dispatch_continuous_commit
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_dispatch_continuous_commit"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_dispatch_continuous_commit"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            horizon_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            technology VARCHAR(32),
            power_mw FLOAT,
            committed_mw FLOAT,
            committed_units INTEGER,
            started_units INTEGER,
            stopped_units INTEGER,
            PRIMARY KEY (scenario_id, project, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(
            results_directory, "dispatch_continuous_commit.csv"), "r") \
            as cc_dispatch_file:
        reader = csv.reader(cc_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[7]
            technology = row[6]
            power_mw = row[8]
            committed_mw = row[9]
            committed_units = row[10]
            started_units = row[11]
            stopped_units = row[12]
            c.execute(
                """
                INSERT INTO temp_results_project_dispatch_continuous_commit
                """
                + str(scenario_id) + """
                    (scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw, committed_mw,
                    committed_units, started_units, stopped_units)
                    VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                    {}, {}, {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw, committed_mw,
                    committed_units, started_units, stopped_units
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_continuous_commit
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, committed_mw,
        committed_units, started_units, stopped_units)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, committed_mw, committed_units,
        started_units, stopped_units
        FROM temp_results_project_dispatch_continuous_commit""" + str(
            scenario_id) + """
            ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_dispatch_continuous_commit""" + str(
            scenario_id) +
        """;"""
    )
    db.commit()
