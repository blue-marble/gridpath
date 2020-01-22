#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'continuous/linear-commit' generators,
i.e. generators with on/off commitment decisions, but with the binary
commitment decision relaxed. The relaxation replaces the binary variables
(commit, start, stop, synced_units) with continuous variables within the range
[0,1]. Except for this relaxation, the formulation is exactly the same as
*gen_commit_bin*. Please refer to the *gen_commit_bin* module for more
information on the formulation.

.. Note:: Some of the more complex constraints in this module such as the
startup trajectories might show weird behavior in the linearized version, e.g.
different fractions of the unit might be starting up and shutting down in the
same timepoint. We don't recommend using this linearized version in combination
with these complex constraints.
"""

from __future__ import division

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    PercentFraction, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    setup_results_import, check_req_prj_columns, write_validation_to_database,\
    validate_startup_shutdown_rate_inputs
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    First, we determine the project subset with 'gen_commit_lin'
    as operational type. This is the *DISPATCHABLE_LINEAR_COMMIT_GENERATORS*
    set, which we also designate with :math:`BCG\subset R` and index
    :math:`bcg`.
    We define several operational parameters over :math:`BCG`: \n
    *displincommit_min_stable_level_fraction* \ :sub:`bcg`\ -- the
    minimum stable level of the dispatchable-linear-commit generator, defined
    as a fraction its capacity \n
    *displincommit_startup_plus_ramp_up_rate* \ :sub:`bcg`\ -- the project's
    upward ramp rate limit during startup, defined as a fraction of its capacity
    per minute. This param, adjusted for timepoint duration, has to be equal or
    larger than *displincommit_min_stable_level_fraction* for the unit to be
    able to start up between timepoints. \n
    *displincommit_shutdown_plus_ramp_down_rate* \ :sub:`bcg`\ -- the project's
    downward ramp rate limit during shutdown, defined as a fraction of its
    capacity per minute. This param, adjusted for timepoint duration, has to be
    equal or larger than *displincommit_min_stable_level_fraction* for the
    unit to be able to shut down between timepoints. \n
    *displincommit_ramp_up_when_on_rate* \ :sub:`bcg`\ -- the project's
    upward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n
    *displincommit_ramp_down_when_on_rate* \ :sub:`bcg`\ -- the project's
    downward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n

    *DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`BCG\_OT\subset RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a
    'gen_commit_lin' project can be operational.

    There are four linear (continuous) decision variables, all defined over
    *DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.
    Commit_Linear is the linear commit variable to represent 'on' or 'off'
    state of a generator.
    Start_Linear is the linear variable to represent the state when a generator
    is turning on.
    Stop_Linear is the linear variable to represent the state when a generator
    is shutting down.
    Provide_Power_Above_Pmin_DispLinearCommit_MW is the power provision variable
    for the generator.

    The main constraints on dispatchable-linear-commit generator power
    provision are as follows:
    For :math:`(bcg, tmp) \in BCG\_OT`: \n
    :math:`Provide\_Power\_DispLinearCommit\_MW_{bcg, tmp} \geq
    Commit\_MW_{bcg, tmp} \\times disp\_linear\_commit\_min\_stable\_level
    \_fraction \\times Capacity\_MW_{bcg,p}` \n
    :math:`Provide\_Power\_DispLinearCommit\_MW_{bcg, tmp} \leq
    Commit\_MW_{bcg, tmp} \\times Capacity\_MW_{bcg,p}`

    TODO: clean up or remove? --> wait for gen_commit_cap template
    """
    # Sets
    m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "gen_commit_lin")
    )

    m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_LINEAR_COMMIT_GENERATORS))

    m.DISPATCHABLE_LINEAR_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=3,
            within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_LINEAR_COMMIT_GENERATORS))

    # Params - Required
    m.disp_linear_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=PercentFraction)

    # Params - Optional

    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    # Startup and shutdown ramp rate are defined as the amount you can
    # ramp when starting up or shutting down. When adjusted for the timepoint
    # duration, it should be at least equal to the min_stable_level_fraction
    m.displincommit_startup_plus_ramp_up_rate = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.displincommit_shutdown_plus_ramp_down_rate = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.displincommit_ramp_up_when_on_rate = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.displincommit_ramp_down_when_on_rate = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=PercentFraction, default=1)

    m.displincommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=NonNegativeReals, default=0)
    m.displincommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_LINEAR_COMMIT_GENERATORS,
              within=NonNegativeReals, default=0)

    # Variables - Linear (relaxed from binary)
    m.Commit_Linear = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)
    # Start_Linear is 1 for the first timepoint the unit is committed after
    # being offline; it will be able to provide power in that timepoint.
    m.Start_Linear = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)
    # Stop_Linear is 1 for the first timepoint the unit is offline after
    # being committed; it will not be able to provide power in that timepoint.
    m.Stop_Linear = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)
    # This auxiliary variable is 1 if the unit is committed or in a startup or
    # shutdown trajectory and zero otherwise.
    m.DispLinCommit_Synced_Units = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)

    # Variables - Continuous
    m.Provide_Power_Above_Pmin_DispLinearCommit_MW = \
        Var(m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    m.Fuel_Burn_DispLinCommit_MMBTU = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    m.DispLinCommit_Pstarting_MW = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    m.DispLinCommit_Pstopping_MW = Var(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    # Expressions
    def pmax_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.Availability_Derate[g, tmp]

    m.DispLinCommit_Pmax_MW = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmax_rule)

    def pmin_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.Availability_Derate[g, tmp] \
               * mod.disp_linear_commit_min_stable_level_fraction[g]

    m.DispLinCommit_Pmin_MW = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmin_rule)

    def provide_power_rule(mod, g, tmp):
        return mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp] \
               + mod.DispLinCommit_Pmin_MW[g, tmp] \
               * mod.Commit_Linear[g, tmp] \
               + mod.DispLinCommit_Pstarting_MW[g, tmp] \
               + mod.DispLinCommit_Pstopping_MW[g, tmp]

    m.Provide_Power_DispLinearCommit_MW = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
               * mod.Availability_Derate[g, tmp] \
               * mod.displincommit_ramp_up_when_on_rate[g] \
               * mod.number_of_hours_in_timepoint[tmp] \
               * 60  # convert min to hours

    m.DispLinCommit_Ramp_Up_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
               * mod.Availability_Derate[g, tmp] \
               * mod.displincommit_ramp_down_when_on_rate[g] \
               * mod.number_of_hours_in_timepoint[tmp] \
               * 60  # convert min to hours

    m.DispLinCommit_Ramp_Down_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_rate_rule)

    def startup_ramp_rate_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.Availability_Derate[g, tmp] \
               * min(mod.displincommit_startup_plus_ramp_up_rate[g]
                     * mod.number_of_hours_in_timepoint[tmp]
                     * 60, 1)

    m.DispLinCommit_Startup_Ramp_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_ramp_rate_rule)

    def shutdown_ramp_rate_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.Availability_Derate[g, tmp] \
               * min(mod.displincommit_shutdown_plus_ramp_down_rate[g]
                     * mod.number_of_hours_in_timepoint[tmp]
                     * 60, 1)

    m.DispLinCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_ramp_rate_rule)

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])

    m.DispLinCommit_Upwards_Reserves_MW = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])

    m.DispLinCommit_Downwards_Reserves_MW = Expression(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)

    # Constraints
    def linear_logic_constraint_rule(mod, g, tmp):
        """
        If commit status changes, unit is turning on or shutting down.
        The *Start_Linear* variable is 1 for the first timepoint the unit is
        committed after being offline; it will be able to provide power in that
        timepoint. The *Stop_Linear* variable is 1 for the first timepoint the
        unit is not committed after being online; it will not be able to
        provide power in that timepoint.

        Constraint (8) in Morales-Espana et al. (2013)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: if we can link horizons, input commit from previous horizon's
        #  last timepoint rather than skipping the constraint
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Commit_Linear[g, tmp] \
                   - mod.Commit_Linear[
                       g, mod.previous_timepoint[
                           tmp, mod.balancing_type_project[g]]] \
                   == mod.Start_Linear[g, tmp] - mod.Stop_Linear[g, tmp]

    m.DispLinCommit_Linear_Logic_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=linear_logic_constraint_rule
    )

    def synced_units_constraint_rule(mod, g, tmp):
        """
        Synced Units is 1 if the unit is committed, starting, or stopping and
        zero otherwise.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.DispLinCommit_Synced_Units[g, tmp] \
               >= mod.Commit_Linear[g, tmp] \
               + (mod.DispLinCommit_Pstarting_MW[g, tmp]
                  + mod.DispLinCommit_Pstopping_MW[g, tmp]) \
               / mod.DispLinCommit_Pmin_MW[g, tmp]

    m.DispLinCommit_Synced_Units_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=synced_units_constraint_rule
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
        return mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp] - \
               mod.DispLinCommit_Downwards_Reserves_MW[g, tmp] \
               >= 0

    m.DispLinCommit_Min_Power_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_power_constraint_rule
    )

    def max_power_constraint_rule(mod, g, tmp):
        """
        Power provision plus upward reserves shall not exceed maximum power.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return \
            (mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp]
             + mod.DispLinCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispLinCommit_Pmax_MW[g, tmp]
             - mod.DispLinCommit_Pmin_MW[g, tmp]) \
            * mod.Commit_Linear[g, tmp]

    m.DispLinCommit_Max_Power_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_constraint_rule
    )

    def min_up_time_constraint_rule(mod, g, tmp):
        """
        When units are started, they have to stay on for a minimum number
        of hours described by the displincommit_min_up_time_hours parameter.
        The constraint is enforced by ensuring that the linear commitment
        is at least as large as the number of unit starts within min up time
        hours.

        We ensure a unit turned on less than the minimum up time ago is
        still on in the current timepoint *tmp* by checking how much units
        were turned on in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to displincommit_min_up_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        starts.

        If using linear horizon boundaries, the constraint is skipped for all
        timepoints less than min up time hours from the start of the timepoint's
        horizon because the constraint for the first included timepoint
        will sufficiently constrain the linear start variables of all the
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
            mod, g, tmp, mod.displincommit_min_up_time_hours[g]
        )

        number_of_starts_min_up_time_or_less_hours_ago = \
            sum(mod.Start_Linear[g, tp] for tp in relevant_tmps)

        # If we've reached the first timepoint in linear boundary mode and
        # the total duration of the relevant timepoints (which includes *tmp*)
        # is less than the minimum up time, skip the constraint since the next
        # timepoint's constraint will already cover these same timepoints.
        # Don't skip if this timepoint is the last timepoint of the horizon
        # (since there will be no next timepoint).
        if (mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear"
                and
                relevant_tmps[-1]
                == mod.first_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]
                and
                sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
                < mod.displincommit_min_up_time_hours[g]
                and
                tmp != mod.last_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]):
            return Constraint.Skip
        # Otherwise, if there was a start min_up_time or less ago, the unit has
        # to remain committed.
        else:
            return mod.Commit_Linear[g, tmp] \
                   >= number_of_starts_min_up_time_or_less_hours_ago

    m.DispLinCommit_Min_Up_Time_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_up_time_constraint_rule
    )

    def min_down_time_constraint_rule(mod, g, tmp):
        """
        When units are shut down, they have to stay off for a minimum number
        of hours described by the displincommit_min_down_time_hours parameter.
        The constraint is enforced by ensuring that (1-linear commitment)
        is at least as large as the number of unit shutdowns within min down
        time hours.

        We ensure a unit shut down less than the minimum up time ago is
        still off in the current timepoint *tmp* by checking how much units
        were shut down in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to displincommit_min_down_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        shutdowns.

        If using linear horizon boundaries, the constraint is skipped for all
        timepoints less than min down time hours from the start of the
        timepoint's horizon because the constraint for the first included
        timepoint will sufficiently constrain the linear stop variables of all
        the timepoints before it.

        Constraint (7) in Morales-Espana et al. (2013)
        """

        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.displincommit_min_down_time_hours[g]
        )

        number_of_stops_min_down_time_or_less_hours_ago = \
            sum(mod.Stop_Linear[g, tp] for tp in relevant_tmps)

        # If we've reached the first timepoint in linear boundary mode and
        # the total duration of the relevant timepoints (which includes *tmp*)
        # is less than the minimum down time, skip the constraint since the
        # next timepoint's constraint will already cover these same timepoints.
        # Don't skip if this timepoint is the last timepoint of the horizon
        # (since there will be no next timepoint).
        if (mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear"
                and
                relevant_tmps[-1]
                == mod.first_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]
                and
                sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
                < mod.displincommit_min_down_time_hours[g]
                and
                tmp != mod.last_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]):
            return Constraint.Skip
        # Otherwise, if there was a shutdown min_down_time or less ago, the unit
        # has to remain shut down.
        else:
            return 1 - mod.Commit_Linear[g, tmp] \
                   >= number_of_stops_min_down_time_or_less_hours_ago

    m.DispLinCommit_Min_Down_Time_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp up the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.displincommit_ramp_up_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= (1 - mod.disp_linear_commit_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp]
                 + mod.DispLinCommit_Upwards_Reserves_MW[g, tmp]) \
                - \
                (mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[
                     g, mod.previous_timepoint[
                         tmp, mod.balancing_type_project[g]]]
                 - mod.DispLinCommit_Downwards_Reserves_MW[
                     g, mod.previous_timepoint[
                         tmp, mod.balancing_type_project[g]]]) \
                <= \
                mod.DispLinCommit_Ramp_Up_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[
                        tmp, mod.balancing_type_project[g]]]

    m.Ramp_Up_Constraint_DispLinearCommit = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp down the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.displincommit_ramp_down_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= (1 - mod.disp_linear_commit_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[
                     g, mod.previous_timepoint[
                         tmp, mod.balancing_type_project[g]]]
                 + mod.DispLinCommit_Upwards_Reserves_MW[
                     g, mod.previous_timepoint[
                         tmp, mod.balancing_type_project[g]]]) \
                - \
                (mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp]
                 - mod.DispLinCommit_Downwards_Reserves_MW[g, tmp]) \
                <= mod.DispLinCommit_Ramp_Down_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[
                        tmp, mod.balancing_type_project[g]]]

    m.Ramp_Down_Constraint_DispLinearCommit = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_constraint_rule
    )

    # Startup power
    def max_startup_power_constraint_rule(mod, g, tmp):
        """
        Startup power is 0 when the unit is committed and must be less than or
        equal to the minimum stable level when not committed.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        return mod.DispLinCommit_Pstarting_MW[g, tmp] \
               <= (1 - mod.Commit_Linear[g, tmp]) \
               * mod.DispLinCommit_Pmin_MW[g, tmp]

    m.DispLinCommit_Max_Startup_Power_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_startup_power_constraint_rule
    )

    def ramp_during_startup_constraint_rule(mod, g, tmp):
        """
        The difference between startup power of consecutive timepoints has to
        obey startup ramp up rates.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return \
                mod.DispLinCommit_Pstarting_MW[g, tmp] - \
                mod.DispLinCommit_Pstarting_MW[g,
                                               mod.previous_timepoint[tmp,
                                                                      mod
                                                                          .balancing_type_project[
                                                                          g]
                                               ]
                ] \
                <= mod.DispLinCommit_Startup_Ramp_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp,
                                              mod.balancing_type_project[g]]
                ]

    m.DispLinCommit_Ramp_During_Startup_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_during_startup_constraint_rule
    )

    def increasing_startup_power_constraint_rule(mod, g, tmp):
        """
        DispLinCommit_Pstarting_MW[t] can only be less than
        DispLinCommit_Pstarting_MW[t-1] in the starting timepoint (when it is
        is back at 0). In other words, DispLinCommit_Pstarting_MW can only
        decrease in the starting timepoint; in all other timepoints it should
        increase or stay constant. This prevents situations in which the model
        can abuse this by providing starting power in some timepoints and then
        reducing power back to 0 without ever committing the unit.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return \
                mod.DispLinCommit_Pstarting_MW[g, tmp] - \
                mod.DispLinCommit_Pstarting_MW[g,
                                               mod.previous_timepoint[tmp,
                                                                      mod
                                                                          .balancing_type_project[
                                                                          g]
                                               ]
                ] \
                >= - mod.Start_Linear[g, tmp] \
                * mod.DispLinCommit_Pmin_MW[g, tmp]

    m.DispLinCommit_Increasing_Startup_Power_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=increasing_startup_power_constraint_rule
    )

    def power_during_startup_constraint_rule(mod, g, tmp):
        """
        Power provision in the start timepoint (i.e. the timepoint when the unit
        is first committed) is constrained by the startup ramp rate (adjusted
        for timepoint duration).

        In other words, to provide 'committed' power in the start timepoint, we
        need to have provided startup power in the previous timepoint, which
        will in turn set the whole startup trajectory based on the previous
        constraints.

        When we are not in the start timepoint, simply constrain power provision
        by the capacity, which may not bind. To elaborate, when we are not in a
        start timepoint, t-1 could have had:
        1) the unit committed, meaning Pstarting[t-1]=0, resulting in
        power provision <= capacity, or
        2) the unit not committed, meaning that we are also not committed in t,
        i.e. power provision[t]=0, resulting in -Pstarting[t-1] <= capacity

        (Commit[t] x Pmin + P_above_Pmin[t]) - Pstarting[t-1]
        <=
        (1 - Start[t]) x Pmax + Start[t] x Startup_Ramp_Rate x Pmax
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return (mod.Commit_Linear[g, tmp]
                    * mod.DispLinCommit_Pmin_MW[g, tmp]
                    + mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp]
                    ) \
                   + mod.DispLinCommit_Upwards_Reserves_MW[g, tmp] \
                   - mod.DispLinCommit_Pstarting_MW[g, mod.previous_timepoint[
                tmp, mod.balancing_type_project[g]]] \
                   <= \
                   (1 - mod.Start_Linear[g, tmp]) \
                   * mod.DispLinCommit_Pmax_MW[g, tmp] \
                   + mod.Start_Linear[g, tmp] \
                   * mod.DispLinCommit_Startup_Ramp_Rate_MW_Per_Timepoint[
                       g, mod.previous_timepoint[tmp,
                                                 mod.balancing_type_project[g]]
                   ]

    m.DispLinCommit_Power_During_Startup_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=power_during_startup_constraint_rule
    )

    # Shutdown power
    def max_shutdown_power_constraint_rule(mod, g, tmp):
        """
        Shutdown power is 0 when the unit is committed and must be less than or
        equal to the minimum stable level when not committed
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        return mod.DispLinCommit_Pstopping_MW[g, tmp] \
               <= (1 - mod.Commit_Linear[g, tmp]) \
               * mod.DispLinCommit_Pmin_MW[g, tmp]

    m.DispLinCommit_Max_Shutdown_Power_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_shutdown_power_constraint_rule
    )

    def ramp_during_shutdown_constraint_rule(mod, g, tmp):
        """
        The difference between shutdown power of consecutive timepoints has to
        obey shutdown ramp up rates.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.DispLinCommit_Pstopping_MW[g, mod.previous_timepoint[
                tmp, mod.balancing_type_project[g]]] \
                   - mod.DispLinCommit_Pstopping_MW[g, tmp] \
                   <= mod.DispLinCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint[
                       g, mod.previous_timepoint[tmp,
                                                 mod.balancing_type_project[g]]
                   ]

    m.DispLinCommit_Ramp_During_Shutdown_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_during_shutdown_constraint_rule
    )

    def decreasing_shutdown_power_constraint_rule(mod, g, tmp):
        """
        DispLinCommit_Pstopping_MW[t] can only be less than
        DispLinCommit_Pstopping_MW[t+1] if the unit stops in t+1 (when it is
        back above 0). In other words, DispLinCommit_Pstopping_MW can only
        increase in the stopping timepoint; in all other timepoints it should
        decrease or stay constant. This prevents situations in which the model
        can abuse this by providing stopping power in some timepoints without
        previously having committed the unit.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.last_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return \
                mod.DispLinCommit_Pstopping_MW[g, tmp] - \
                mod.DispLinCommit_Pstopping_MW[g,
                                               mod.next_timepoint[tmp,
                                                                  mod
                                                                      .balancing_type_project[
                                                                      g]
                                               ]
                ] \
                >= \
                - mod.Stop_Linear[g,
                                  mod.next_timepoint[tmp,
                                                     mod
                                                         .balancing_type_project[
                                                         g]
                                  ]
                ] * \
                mod.DispLinCommit_Pmin_MW[g, tmp]

    m.DispLinCommit_Decreasing_Shutdown_Power_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=decreasing_shutdown_power_constraint_rule
    )

    def power_during_shutdown_constraint_rule(mod, g, tmp):
        """
        Power provision in the stop timepoint (i.e. the first timepoint the unit
        is not committed after having been committed) is constrained by the
        shutdown ramp rate (adjusted for timepoint duration).

        In other words, to provide 'committed' power in the stop timepoint, we
        need to provide shutdown power in the next timepoint, which will in turn
        set the whole shutdown trajectory based on the previous constraints.

        When we are not in the stop timepoint, simply constrain power provision
        by the capacity, which may not bind. To elaborate, when we are not in a
        stop timepoint, t+1 could have:
        1) the unit committed, meaning Pstopping[t+1]=0, resulting in
        power provision <= capacity, or
        2) the unit not committed, meaning that we are also not committed in t
        i.e. power provision[t]=0, resulting in -Pstopping[t+1] <= capacity

        (Commit[t] x Pmin + P_above_Pmin[t]) - Pstopping[t+1]
        <=
        (1 - Stop[t+1]) x Pmax + Stop[t+1] x Shutdown_Ramp_Rate x Pmax
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        if tmp == mod.last_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return (mod.Commit_Linear[g, tmp]
                    * mod.DispLinCommit_Pmin_MW[g, tmp]
                    + mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g,
                                                                       tmp]) \
                   + mod.DispLinCommit_Upwards_Reserves_MW[g, tmp] \
                   - mod.DispLinCommit_Pstopping_MW[g, mod.next_timepoint[
                tmp, mod.balancing_type_project[g]]] \
                   <= \
                   (1 - mod.Stop_Linear[g, mod.next_timepoint[
                       tmp, mod.balancing_type_project[g]]]) \
                   * mod.DispLinCommit_Pmax_MW[
                       g, mod.next_timepoint[
                           tmp, mod.balancing_type_project[g]]] \
                   + mod.Stop_Linear[
                       g, mod.next_timepoint[
                           tmp, mod.balancing_type_project[g]]] \
                   * mod.DispLinCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint[
                       g, tmp]

    m.DispLinCommit_Power_During_Shutdown_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=power_during_shutdown_constraint_rule
    )

    def fuel_burn_constraint_rule(mod, g, tmp, s):
        """
        Fuel burn is set by piecewise linear representation of input/output
        curve.

        Note: we assume that when projects are derated for availability, the
        input/output curve is derated by the same amount. The implicit
        assumption is that when a generator is de-rated, some of its units
        are out rather than it being forced to run below minimum stable level
        at very inefficient operating points.
        :param mod:
        :param g:
        :param tmp:
        :param s:
        :return:
        """
        return \
            mod.Fuel_Burn_DispLinCommit_MMBTU[g, tmp] \
            >= \
            mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
            * mod.Provide_Power_DispLinearCommit_MW[g, tmp] \
            + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
            * mod.Availability_Derate[g, tmp] \
            * mod.DispLinCommit_Synced_Units[g, tmp]

    m.Fuel_Burn_DispLinCommit_Constraint = Constraint(
        m.DISPATCHABLE_LINEAR_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
        rule=fuel_burn_constraint_rule
    )


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by dispatchable-linear-commit
     generators

    Power provision for dispatchable-linear-commit generators is a
    variable constrained to be between the generator's minimum stable level
    and its capacity if the generator is committed and 0 otherwise.

    """
    return mod.Provide_Power_DispLinearCommit_MW[g, tmp]


# RPS
def rec_provision_rule(mod, g, tmp):
    """
    REC provision of dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispLinearCommit_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    # TODO: shouldn't we return MW here to make this general?
    return mod.Commit_Linear[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.DispLinCommit_Pmax_MW[g, tmp] \
           * mod.Commit_Linear[g, tmp]


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
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.Fuel_Burn_DispLinCommit_MMBTU[g, tmp]
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
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return None
    else:
        return (mod.Commit_Linear[g, tmp]
                - mod.Commit_Linear[
                    g, mod.previous_timepoint[
                        tmp, mod.balancing_type_project[g]]]) \
               * mod.DispLinCommit_Pmax_MW[g, tmp]


def power_delta_rule(mod, g, tmp):
    """
    Ramp between this timepoint and the previous timepoint
    Actual ramp rate in MW/hr depends on the duration of the timepoints.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        pass
    else:
        return mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[g, tmp] - \
               mod.Provide_Power_Above_Pmin_DispLinearCommit_MW[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]]


def fix_commitment(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Linear[g, tmp] = \
        mod.fixed_commitment[g, mod.previous_stage_timepoint_map[tmp]]
    mod.Commit_Linear[g, tmp].fixed = True


def load_module_specific_data(mod, data_portal,
                              scenario_directory, subproblem, stage):
    """
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
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

    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["startup_plus_ramp_up_rate",
                        "shutdown_plus_ramp_down_rate",
                        "ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours",
                        "min_down_time_hours"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type",
                 "min_stable_level_fraction"] + used_columns

    )
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "gen_commit_lin":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass
    data_portal.data()["disp_linear_commit_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional, will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_plus_ramp_up_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "displincommit_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "displincommit_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "displincommit_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "displincommit_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_up_time_hours"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "displincommit_min_up_time_hours"] = \
            min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_down_time_hours"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "displincommit_min_down_time_hours"] = \
            min_down_time


def export_module_specific_results(mod, d,
                                   scenario_directory, subproblem, stage):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "dispatch_linear_commit.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint", "technology",
                         "load_zone", "power_mw", "committed_mw",
                         "committed_units", "started_units", "stopped_units",
                         "synced_units"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_LINEAR_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.balancing_type_project[p],
                mod.horizon[tmp, mod.balancing_type_project[p]],
                tmp,
                mod.timepoint_weight[tmp],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Power_DispLinearCommit_MW[p, tmp]),
                value(mod.DispLinCommit_Pmax_MW[p, tmp])
                * value(mod.Commit_Linear[p, tmp]),
                value(mod.Commit_Linear[p, tmp]),
                value(mod.Start_Linear[p, tmp]),
                value(mod.Stop_Linear[p, tmp]),
                value(mod.DispLinCommit_Synced_Units[p, tmp])
            ])


def import_module_specific_results_to_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """
    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("project dispatch linear commit")
    # dispatch_linear_commit.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_dispatch_continuous_commit",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(
            results_directory, "dispatch_linear_commit.csv"), "r") \
            as cc_dispatch_file:
        reader = csv.reader(cc_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type_project = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            load_zone = row[8]
            technology = row[7]
            power_mw = row[9]
            committed_mw = row[10]
            committed_units = row[11]
            started_units = row[12]
            stopped_units = row[13]
            synced_units = row[14]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 balancing_type_project, horizon, timepoint,
                 timepoint_weight, number_of_hours_in_timepoint,
                 load_zone, technology, power_mw, committed_mw,
                 committed_units, started_units, stopped_units,
                 synced_units)
            )
    insert_temp_sql = """
        INSERT INTO temp_results_project_dispatch_continuous_commit{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint,
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_mw, committed_mw, 
        committed_units, started_units, stopped_units, synced_units)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch_continuous_commit
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        committed_mw, committed_units, started_units, stopped_units,
        synced_units)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        committed_mw, committed_units, started_units, stopped_units,
        synced_units
        FROM temp_results_project_dispatch_continuous_commit{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs

    TODO: could add data type checking here
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    validation_results = []

    # Get project inputs
    c1 = conn.cursor()
    projects = c1.execute(
        """SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND operational_type = '{}'""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "gen_commit_lin"
        )
    )

    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Get the number of hours in the timepoint (take min if it varies)
    c2 = conn.cursor()
    tmp_durations = c2.execute(
        """SELECT number_of_hours_in_timepoint
           FROM inputs_temporal_timepoints
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {}
           AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    ).fetchall()
    hrs_in_tmp = min(tmp_durations)

    # Check that min stable level is specified
    # (not all operational types require this input)
    req_columns = [
        "min_stable_level",
    ]
    validation_errors = check_req_prj_columns(df, req_columns, True,
                                              "gen_commit_lin")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Missing inputs",
             error
             )
        )

    # Check that there are no unexpected operational inputs
    expected_na_columns = [
        "unit_size_mw",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                              "gen_commit_lin")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Unexpected inputs",
             error
             )
        )

    # Check startup shutdown rate inputs
    validation_errors = validate_startup_shutdown_rate_inputs(df, hrs_in_tmp)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Invalid startup/shutdown ramp inputs",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)

