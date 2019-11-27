#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'binary-commit' generators,
i.e. generators with on/off commitment decisions.
The formulation is based on "Tight and compact MILP formulation for the
thermal unit commitment problem" (Morales-Espana et al. 2013), available
online at https://ieeexplore.ieee.org/abstract/document/6485014
"""

# TODO: deal with issue of very high startup ramp which means you don't have
#  a startup trajectory. Current approach still requires unit to sit at Pmin
#  for one timepoint. Ideally should revert to old constraint that lets you
#  jump to whatever that fraction is within one timepoint
#  Because we include the first timepoint of a startup and the last of a
#  shutdown when calculating ramp trajectories. Can we simply not include
#  that last timepoint (the 0 MW)

# TODO: ramp assumptions about setpoints are clashing with Morales-Espana
#  assumptions. Ramp assumptions assume you reach setpoint at START of timepoint
#  whereas Morales-Espana assume you reach it end of timepoint.

# TODO: set min down time equal to expression of min offline time +
#   shortest startup duration + shutdown duration (see Morales Espana 2013b p4))
#   (or just assume in down time includes shut down and startup duration
#    and simply check this in validation)

# TODO validations:
#  disallow binary commit with availability decsisions since non-linear?
#  don't allow min down time < shutdown + startup (note: default is 0 min_down!)
#   okay if startup ramp up rate is big enough for you to go straight to pmin
#  make sure first point in startup ramp rate is equal to min down time
#  make sure ID for startup type is unique and auto-increment! (we use +1)
#  make sure down time for different startup types is different and increasing
#  with increasing ID
#  if startup ramp is defined, cost needs to be defined - ACTUALY NOT?
#  can't allow both startup fuel and startup ramp because that will double count
#  the fuel
#  down time has to be always defined and equal to TD at first down time

# TODO: cleanup
#  REMOVE "sorted" in results and hard-coded 4h min up and down time
#  add explanations to new functions
#  add testing to new functions (?)
#  change naming of ramp up rates -> first see how we deal with this formulation
#  vs. the previous one with startup_plus_rampup_rates, which are used in
#  capacity commit as well. Seems weird to me that you can ramp higher than
#  normal ramp rate when starting up.
#  REMOVE debug print statements

# Untested: if availability changes during a startup process, things could
# get weird

from __future__ import division

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Binary, PercentFraction, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    setup_results_import
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, determine_relevant_timepoints_forward, \
    determine_relevant_timepoints_startup


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from
    First, we determine the project subset with 'gen_commit_bin'
    as operational type. This is the *DISPATCHABLE_BINARY_COMMIT_GENERATORS*
    set, which we also designate with :math:`BCG\subset R` and index
    :math:`bcg`.
    We define several operational parameters over :math:`BCG`: \n
    *dispbincommit_min_stable_level_fraction* \ :sub:`bcg`\ -- the
    minimum stable level of the dispatchable-binary-commit generator, defined
    as a fraction its capacity \n
    *dispbincommit_ramp_up_when_on_rate* \ :sub:`bcg`\ -- the project's
    upward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n
    *dispbincommit_ramp_down_when_on_rate* \ :sub:`bcg`\ -- the project's
    downward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n
    *dispbincommit_shutdown_plus_ramp_down_rate* \ :sub:`bcg`\ -- the project's
    downward ramp rate limit during shutdown, defined as a fraction of its
    capacity per minute. This param, adjusted for timepoint duration, has to be
    equal or larger than *dispbincommit_min_stable_level_fraction* for the
    unit to be able to shut down between timepoints. \n

    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`BCG\_OT\subset RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a
    'gen_commit_bin' project can be operational.

    There are three binary decision variables, and one continuous decision
    variable, all defined over
    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.
    Commit_Binary is the binary commit variable to represent 'on' or 'off'
    state of a generator.
    Start_Binary is the binary variable to represent the state when a generator
    is turning on.
    Stop_Binary is the binary variable to represent the state when a generator
    is shutting down.
    Provide_Power_Above_Pmin_DispBinaryCommit_MW is the power provision variable
    for the generator.

    The main constraints on dispatchable-binary-commit generator power
    provision are as follows:
    For :math:`(bcg, tmp) \in BCG\_OT`: \n
    :math:`Provide\_Power\_DispBinaryCommit\_MW_{bcg, tmp} \geq
    Commit\_MW_{bcg, tmp} \\times disp\_binary\_commit\_min\_stable\_level
    \_fraction \\times Capacity\_MW_{bcg,p}` \n
    :math:`Provide\_Power\_DispBinaryCommit\_MW_{bcg, tmp} \leq
    Commit\_MW_{bcg, tmp} \\times Capacity\_MW_{bcg,p}`

    TODO: add documentation on all constraints

    """
    # ------------------------ Sets ------------------------ #
    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "gen_commit_bin")
    )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS))

    m.DISPATCHABLE_BINARY_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=3,
            within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS)
            )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS_STARTUP_TYPES = Set(
            within=m.STARTUP_PROJECTS_TYPES,
        rule=lambda mod:
            set((g, l) for (g, l) in mod.STARTUP_PROJECTS_TYPES
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS)
    )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS_STARTUP_RAMP_TYPES = Set(
            within=m.STARTUP_RAMP_PROJECTS_TYPES,
        rule=lambda mod:
            set((g, l) for (g, l) in mod.STARTUP_RAMP_PROJECTS_TYPES
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS)
    )

    m.DISPATCHABLE_BINARY_COMMIT_STARTUP_TYPES_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=3,
        rule=lambda mod:
        set((g, tmp, l) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            for _g, l in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS_STARTUP_TYPES
            if g == _g)
    )

    # --------------- Params - Required -------------------- #
    m.disp_binary_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction)

    # --------------- Params - Optional -------------------- #

    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    # Startup and shutdown ramp rate are defined as ramp rate limit during
    # startup or shutdown, usually lower than the operational ramp rate.
    m.dispbincommit_ramp_up_when_on_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispbincommit_ramp_down_when_on_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)

    m.dispbincommit_shutdown_plus_ramp_down_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)

    m.dispbincommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=0)
    m.dispbincommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=0)

    # ------------------ Derived Params ------------------------ #
    def startup_length_hours_rule(mod, g, l):
        return mod.disp_binary_commit_min_stable_level_fraction[g] \
            / mod.startup_ramp[g, l] / 60
    m.DispBinCommit_Startup_Length_Hours = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS_STARTUP_RAMP_TYPES,
        rule=startup_length_hours_rule
    )

    def shutdown_length_hours_rule(mod, g):
        return mod.disp_binary_commit_min_stable_level_fraction[g] \
            / mod.dispbincommit_shutdown_plus_ramp_down_rate[g] / 60
    m.DispBinCommit_Shutdown_Length_Hours = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        rule=shutdown_length_hours_rule
    )

    # -------------------- Variables - Binary -------------------- #
    m.Commit_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    # ------------------ Variables - Continuous ------------------ #

    # Start_Binary is 1 for the first timepoint the unit is committed after
    # being offline; it will be able to provide power and reserves in that
    # timepoint. The timepoint before that, the unit will have to have reached
    # Pmin at the end of that timepoint as part of the startup process.
    # Due to the binary logic constraint, this variable will be forced to take
    # on binary values, even though it is a continuous variable.
    m.Start_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)
    # Stop_Binary is 1 for the first timepoint the unit is offline after
    # being committed; it will not be able to provide power in that timepoint,
    # except for some residual power as part of the shutdown process.
    # Due to the binary logic constraint, this variable will be forced to take
    # on binary values, even though it is a continuous variable.
    m.Stop_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)

    # Continuous variable which takes the value of 1 in the period where the
    # unit starts up for the start-up type l and 0 otherwise.
    # Due to the binary logic constraint, this variable will be forced to take
    # on binary values, even though it is a continuous variable.
    m.Start_Binary_Type = Var(
        m.DISPATCHABLE_BINARY_COMMIT_STARTUP_TYPES_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction)

    # We assume that generator reaches this setpoint at start of timepoint
    m.Provide_Power_Above_Pmin_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    m.Fuel_Burn_DispBinCommit_MMBTU = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    # ---------------------- Expressions --------------------- #
    def pmax_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp]
    m.DispBinCommit_Pmax_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmax_rule)

    def pmin_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp] \
            * mod.disp_binary_commit_min_stable_level_fraction[g]
    m.DispBinCommit_Pmin_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmin_rule)

    # Calculate active startup
    def active_startup_rule(mod, g, tmp):
        return (sum(mod.Start_Binary_Type[g, tmp, l] * l
                    for l in mod.STARTUP_TYPES_BY_STARTUP_PROJECT[g])
                if g in mod.STARTUP_PROJECTS else 0)
    m.DispBinCommit_Active_Startup_Type = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=active_startup_rule)

    def shutdown_power_rule(mod, g, tmp):
        """
        Get the shutdown power (only applicable of timepoint tmp takes place
        during the shutdown trajectory duration).

        We first determine the relevant timepoints, namely the current timepoint
        and the previous timepoints that are within shutdown_duration hours from
        timepoint tmp. If the unit shuts down in any of these timepoints
        (Stop_Binary = 1), timepoint tmp will be part of a shutdown trajectory.

        For each of these relevant timepoints, we then calculate what the
        shutdown power in timepoint tmp would be if the unit was shutting down
        in that relevant timepoint.

        Example:
        tmp = 5, timepoint_duration_hours = 1 hour, shutdown_duration = 4 hours
        Pmin = 4 MW
        --> relevant timepoints = [5, 4, 3, 2], i.e. a shutdown in any of these
            timepoints would have an effect on the shutdown power in timepoint
            10
        --> Let's assume that the unit actually shuts down in timepoint 4
            (Stop_Binary[4] = 0). That means that in tmp 5, the power output
            will be 2 MW, which is what this function would return. (note: in
            tmp 3, the unit will be at PMin at 4 MW, in tmp 4 it will be already
            down to 3 MW).

        Note:  Stop_Binary is 1 first timepoint of shutdown trajectory
        (Pmin at end of timepoint before)

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        relevant_tmps_shutdown = determine_relevant_timepoints(
            mod, g, tmp, mod.DispBinCommit_Shutdown_Length_Hours[g])

        relevant_shutdown_power = 0
        time_from_shutdown = 0
        for t in relevant_tmps_shutdown[:-1]:
            time_from_shutdown += mod.number_of_hours_in_timepoint[t]
            relevant_shutdown_power += mod.Stop_Binary[g, t] \
                * (mod.DispBinCommit_Pmin_MW[g, tmp]
                   - time_from_shutdown * 60
                   * mod.dispbincommit_shutdown_plus_ramp_down_rate[g]
                   * mod.Capacity_MW[g, mod.period[t]]
                   * mod.Availability_Derate[g, t])

        # Alternative with list comprehension
        # durations = [0] + list(accumulate(
        #     [mod.number_of_hours_in_timepoint[t]
        #      for t in relevant_tmps_shutdown][:-1]
        # ))
        # relevant_shutdown_power = sum(
        #     (mod.DispBinCommit_Pmin_MW[g, tmp] -
        #      durations[i]
        #      * mod.dispbincommit_shutdown_plus_ramp_down_rate[g]
        #      * mod.Capacity_MW[g, mod.period[t]]
        #      * mod.Availability_Derate[g, t])
        #     * mod.Stop_Binary[g, t]
        #     for i, t in enumerate(relevant_tmps_shutdown)
        # )

        return relevant_shutdown_power
    m.ShutDownPower_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_power_rule
    )

    def startup_power_rule(mod, g, tmp):
        """
        Get the startup power (only applicable if timepoint tmp takes place
        during the startup trajectory duration).

        We first determine the relevant timepoints, namely the future timepoints
        that are within startup_duration hours from timepoint tmp. If the unit
        starts up in any of these timepoints (Start_Binary = 1), timepoint tmp
        will be part of a startup trajectory.

        For each of these relevant timepoints, we then calculate what the
        startup power in timepoint tmp would be if the unit was starting up
        in that relevant timepoint.

        Example:
        tmp = 5, timepoint_duration_hours = 1 hour, startup_duration = 4 hours
        Pmin = 4 MW
        --> relevant timepoints = [6, 7, 8, 9], i.e. a shutdown in any of these
            timepoints would have an effect on the startup power in timepoint
            5
        --> Let's assume that the unit actually starts up in timepoint 7
            (Start_Binary[7] = 0). That means that in tmp 5, the power output
            will be 3 MW, which is what this function would return. (note: in
            tmp 6, the unit will be at PMin at 4 MW, in tmp 4 it will at 2 MW,
            and in tmp 3 it will be at 1 MW.

        Note: Start_Binary is 1 first timepoint after startup trajectory
        (pmin at start of that timepoint, i.e. end of previous timeoint)

        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        relevant_startup_power = 0
        if g in mod.STARTUP_RAMP_PROJECTS:
            for l in mod.STARTUP_TYPES_BY_STARTUP_RAMP_PROJECT[g]:
                relevant_tmps_startup = determine_relevant_timepoints_forward(
                    mod, g, tmp,
                    mod.DispBinCommit_Startup_Length_Hours[g, l]
                )
                # print(tmp, l, relevant_tmps_startup)
                time_from_startup = 0
                for t in relevant_tmps_startup:
                    relevant_startup_power += mod.Start_Binary_Type[g, t, l] \
                        * (mod.DispBinCommit_Pmin_MW[g, tmp]
                           - time_from_startup * 60
                           * mod.startup_ramp[g, l]
                           * mod.Capacity_MW[g, mod.period[t]]
                           * mod.Availability_Derate[g, t])
                    time_from_startup += mod.number_of_hours_in_timepoint[t]
                # print(tmp, relevant_startup_power)
        return relevant_startup_power
    m.StartUpPower_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_power_rule
    )

    def provide_power_operations_rule(mod, g, tmp):
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] \
            + mod.DispBinCommit_Pmin_MW[g, tmp] \
            * mod.Commit_Binary[g, tmp]
    m.Provide_Power_Operations_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=provide_power_operations_rule)

    def provide_power_all_rule(mod, g, tmp):
        return mod.Provide_Power_Operations_DispBinaryCommit_MW[g, tmp] \
            + mod.StartUpPower_DispBinaryCommit_MW[g, tmp] \
            + mod.ShutDownPower_DispBinaryCommit_MW[g, tmp]
    m.Provide_Power_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=provide_power_all_rule)

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
            * mod.dispbincommit_ramp_up_when_on_rate[g] \
            * mod.number_of_hours_in_timepoint[tmp] \
            * 60  # convert min to hours
    m.DispBinCommit_Ramp_Up_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
            * mod.dispbincommit_ramp_down_when_on_rate[g] \
            * mod.number_of_hours_in_timepoint[tmp] \
            * 60  # convert min to hours
    m.DispBinCommit_Ramp_Down_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_rate_rule)

    # TODO: remove or adjust to be linked to new startup param
    # Note: make sure to limit this to Pmax, otherwise max power rules break
    # def startup_ramp_rate_rule(mod, g, tmp, l):
    #     return mod.Capacity_MW[g, mod.period[tmp]] \
    #         * mod.Availability_Derate[g, tmp] \
    #         * min(mod.startup_ramp[g, l]
    #               * mod.number_of_hours_in_timepoint[tmp]
    #               * 60, 1)
    # m.DispBinCommit_Startup_Ramp_Rate_MW_Per_Timepoint = Expression(
    #     m.DISPATCHABLE_BINARY_COMMIT_STARTUP_TYPES_OPERATIONAL_TIMEPOINTS,
    #     rule=startup_ramp_rate_rule)

    # TODO: remove or link back up to old ramp rate rule for non-quick start
    #  units
    # Note: make sure to limit this to Pmax, otherwise max power rules break
    def shutdown_ramp_rate_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp] \
            * min(mod.dispbincommit_shutdown_plus_ramp_down_rate[g]
                  * mod.number_of_hours_in_timepoint[tmp]
                  * 60, 1)
    m.DispBinCommit_Shutdown_Ramp_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_ramp_rate_rule)

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

    # ------------------ Constraints -------------------- #
    def binary_logic_constraint_rule(mod, g, tmp):
        """
        If commit status changes, unit is turning on or shutting down.
        The *Start_Binary* variable is 1 for the first timepoint the unit is
        committed after being offline; it will be able to provide power in that
        timepoint. The *Stop_Binary* variable is 1 for the first timepoint the
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
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Commit_Binary[g, tmp] \
                - mod.Commit_Binary[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                == mod.Start_Binary[g, tmp] - mod.Stop_Binary[g, tmp]

    m.DispBinCommit_Binary_Logic_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=binary_logic_constraint_rule
    )

    def startup_type_constraint_rule(mod, g, tmp, l):
        """
        Startup_type l can only be activated (startup_type ≤ 1) if the unit has
        previously been down within the appropriate interval. The interval for
        startup type l is defined by the user specified boundary parameters
        mod.down_time_hours[l] and mod.down_time_hours[l+1].

        If we're at the coldest (last) startup type, there is no l+1 and the
        constraint is skipped. This is okay because the model will select a
        hotter, cheaper startup type if it can and there can only be one
        startup_type active at once (see next constraint). This also means the
        constraint will be skipped if there is only one startup type.

        :param mod:
        :param g:
        :param tmp:
        :param l: startup_type
        :return:
        """

        # Coldest startup type is un-constrained
        if l == mod.STARTUP_TYPES_BY_STARTUP_PROJECT[g][-1]:
            return Constraint.Skip

        # Get the timepoints within [TSU,l; TSU,l+1) hours from *tmp*
        relevant_tmps = determine_relevant_timepoints_startup(
            mod, g, tmp,
            mod.down_time_hours[g, l],
            mod.down_time_hours[g, l+1]
        )

        # Skip constraint if we are within TSU,l+1 hours from the start of the
        # horizon (linear horizon boundary) or from the current tmp (circular
        # horizon boundary).
        if len(relevant_tmps) == 0:
            return Constraint.Skip

        # Equal to 1 if unit has been down within interval [TSU,l; TSU,l+1)
        # before hour t. This "activates" this particular startup type
        shutdown_within_interval = \
            sum(mod.Stop_Binary[g, tp] for tp in relevant_tmps)

        return mod.Start_Binary_Type[g, tmp, l] <= shutdown_within_interval

    m.DispBinCommit_Start_Binary_Type_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_STARTUP_TYPES_OPERATIONAL_TIMEPOINTS,
        rule=startup_type_constraint_rule
    )

    def only_one_startup_type_constraint_rule(mod, g, tmp):
        """
        Ensure that just one startup type is selected when the unit starts up.

        From Morales-Espana 2013b:
        "In the event that more than one SU type variable can be activated
        (delta-t,l ≤ 1) then (2) together with the objective function ensure
        that the hottest, which is the cheapest, possible option is always
        selected. Therefore, just one of the variables is activated (equal to
        one). That is, these variables take binary values even though they
        are modeled as continuous variables. This is due to the convex
        (monotonically increasing) characteristic of the exponential SU costs
        of thermal units"

        Equation (2) in Morales-Espana 2013b
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        if g not in mod.STARTUP_PROJECTS:
            return Constraint.Skip
        else:
            sum_startup_types = sum(
                mod.Start_Binary_Type[g, tmp, l]
                for l in mod.STARTUP_TYPES_BY_STARTUP_PROJECT[g]
            )

            return sum_startup_types == mod.Start_Binary[g, tmp]

    m.DispBinCommit_Only_One_Startup_Type_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=only_one_startup_type_constraint_rule
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
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] - \
            mod.DispBinCommit_Downwards_Reserves_MW[g, tmp] \
            >= 0

    m.DispBinCommit_Min_Power_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_power_constraint_rule
    )

    def max_power_constraint_rule(mod, g, tmp):
        """
        Power provision adjusted for upward reserves can't exceed generator's
        maximum power output.

        This also sets the power output to Pmin at the last timepoint of an
        up-period (last committed timeoint).

        Constraint (6) in Morales-Espana et al. (2013b)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: replace with constraint (31) Morales-Espana 2017 and see
        #  whether this gets rid of
        #  Note: will also have to take out startup/rampup trajectories if
        #  the unit is quick-starting (might be okay cause it's zero?)

        # *stop_next_tmp* equals the value of the binary stop variable for the
        # next timepoint. If the horizon boundary is linear and we're at the
        # last timepoint in the horizon, there is no next timepoint, so we'll
        # assume that the value equals zero. This equivalent to "skipping" the
        # tightening of the constraint.
        if tmp == mod.last_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            stop_next_tmp = 0
        else:
            stop_next_tmp = mod.Stop_Binary[
                g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]]

        # Power provision plus upward reserves shall not exceed maximum power.
        return \
            (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
             + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispBinCommit_Pmax_MW[g, tmp]
             - mod.DispBinCommit_Pmin_MW[g, tmp]) \
            * (mod.Commit_Binary[g, tmp] - stop_next_tmp)

    m.DispBinCommit_Max_Power_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_constraint_rule
    )

    def min_up_time_constraint_rule(mod, g, tmp):
        """
        When units are started, they have to stay on for a minimum number
        of hours described by the dispbincommit_min_up_time_hours parameter.
        The constraint is enforced by ensuring that the binary commitment
        is at least as large as the number of unit starts within min up time
        hours.

        We ensure a unit turned on less than the minimum up time ago is
        still on in the current timepoint *tmp* by checking how much units
        were turned on in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to dispbincommit_min_up_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        starts.

        If using linear horizon boundaries, the constraint is skipped for all
        timepoints less than min up time hours from the start of the timepoint's
        horizon because the constraint for the first included timepoint
        will sufficiently constrain the binary start variables of all the
        timepoints before it.

        Constraint (6) in Morales-Espana et al. (2013a)

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
            mod, g, tmp, mod.dispbincommit_min_up_time_hours[g]
        )

        number_of_starts_min_up_time_or_less_hours_ago = \
            sum(mod.Start_Binary[g, tp] for tp in relevant_tmps)

        # If we've reached the first timepoint in linear boundary mode and
        # the total duration of the relevant timepoints (which includes *tmp*)
        # is less than the minimum up time, skip the constraint since the next
        # timepoint's constraint will already cover these same timepoints.
        # Don't skip if this timepoint is the last timepoint of the horizon
        # (since there will be no next timepoint).
        if (mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear"
                and
                relevant_tmps[-1]
                == mod.first_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]
                and
                sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
                < mod.dispbincommit_min_up_time_hours[g]
                and
                tmp != mod.last_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]):
            return Constraint.Skip
        # Otherwise, if there was a start min_up_time or less ago, the unit has
        # to remain committed.
        else:
            return mod.Commit_Binary[g, tmp] \
                >= number_of_starts_min_up_time_or_less_hours_ago

    m.DispBinCommit_Min_Up_Time_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_up_time_constraint_rule
    )

    def min_down_time_constraint_rule(mod, g, tmp):
        """
        When units are shut down, they have to stay off for a minimum number
        of hours described by the dispbincommit_min_down_time_hours parameter.
        The constraint is enforced by ensuring that (1-binary commitment)
        is at least as large as the number of unit shutdowns within min down
        time hours.

        We ensure a unit shut down less than the minimum up time ago is
        still off in the current timepoint *tmp* by checking how much units
        were shut down in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to dispbincommit_min_down_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        shutdowns.

        If using linear horizon boundaries, the constraint is skipped for all
        timepoints less than min down time hours from the start of the
        timepoint's horizon because the constraint for the first included
        timepoint will sufficiently constrain the binary stop variables of all
        the timepoints before it.

        Constraint (7) in Morales-Espana et al. (2013)
        """

        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.dispbincommit_min_down_time_hours[g]
        )

        number_of_stops_min_down_time_or_less_hours_ago = \
            sum(mod.Stop_Binary[g, tp] for tp in relevant_tmps)

        # If we've reached the first timepoint in linear boundary mode and
        # the total duration of the relevant timepoints (which includes *tmp*)
        # is less than the minimum down time, skip the constraint since the
        # next timepoint's constraint will already cover these same timepoints.
        # Don't skip if this timepoint is the last timepoint of the horizon
        # (since there will be no next timepoint).
        if (mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear"
                and
                relevant_tmps[-1]
                == mod.first_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]
                and
                sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
                < mod.dispbincommit_min_down_time_hours[g]
                and
                tmp != mod.last_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]):
            return Constraint.Skip
        # Otherwise, if there was a shutdown min_down_time or less ago, the unit
        # has to remain shut down.
        else:
            return 1 - mod.Commit_Binary[g, tmp] \
                >= number_of_stops_min_down_time_or_less_hours_ago

    m.DispBinCommit_Min_Down_Time_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp up the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.dispbincommit_ramp_up_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= (1 - mod.disp_binary_commit_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                 + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
                - \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[
                     g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                 - mod.DispBinCommit_Downwards_Reserves_MW[
                     g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
                <= \
                mod.DispBinCommit_Ramp_Up_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]

    m.Ramp_Up_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp down the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.dispbincommit_ramp_down_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= (1 - mod.disp_binary_commit_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[
                     g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                 + mod.DispBinCommit_Upwards_Reserves_MW[
                     g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
                - \
                (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
                 - mod.DispBinCommit_Downwards_Reserves_MW[g, tmp]) \
                <= mod.DispBinCommit_Ramp_Down_Rate_MW_Per_Timepoint[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]

    m.Ramp_Down_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_constraint_rule
    )

    def fuel_burn_constraint_rule(mod, g, tmp, s):
        """
        Fuel burn is set by piecewise linear representation of input/output
        curve. This does not include fuel burn during startup/shutdown,
        which is calculated and reported separately.

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
            mod.Fuel_Burn_DispBinCommit_MMBTU[g, tmp] \
            >= \
            mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
            * mod.Provide_Power_Operations_DispBinaryCommit_MW[g, tmp] \
            + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
            * mod.Availability_Derate[g, tmp] \
            * mod.Commit_Binary[g, tmp]
    m.Fuel_Burn_DispBinCommit_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
        rule=fuel_burn_constraint_rule
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
    and its capacity if the generator is committed and 0 otherwise. The one
    exception is during startup and shutdown, when the unit can follow a
    trajectory from zero to the generator's minimum stable level, defined by the
    startup/shutdown ramp rate.
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
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.Fuel_Burn_DispBinCommit_MMBTU[g, tmp]
    else:
        raise ValueError(error_message)


def startup_rule(mod, g, tmp, l):
    """
    Returns the number of MWs that are started up for startup type *l*
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
        return mod.Start_Binary_Type[g, tmp, l] \
               * mod.DispBinCommit_Pmax_MW[g, tmp]
        # TODO: should we multiply by availability here?


def shutdown_rule(mod, g, tmp):
    """
    Returns the number of MWs that are shut down.
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
        return mod.Stop_Binary[g, tmp] * mod.DispBinCommit_Pmax_MW[g, tmp]
    # TODO: should we multiply by availability here?


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
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] - \
            mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def fix_commitment(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Binary[g, tmp] = \
        mod.fixed_commitment[g, mod.previous_stage_timepoint_map[tmp]]
    mod.Commit_Binary[g, tmp].fixed = True


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
    ramp_up_when_on_rate = dict()
    ramp_down_when_on_rate = dict()
    min_up_time = dict()
    min_down_time = dict()
    shutdown_plus_ramp_down_rate = dict()

    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours",
                        "min_down_time_hours",
                        "shutdown_plus_ramp_down_rate"]
    used_columns = [c for c in optional_columns if c in header]

    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type",
                 "min_stable_level_fraction"] + used_columns

    )
    for row in zip(df["project"],
                   df["operational_type"],
                   df["min_stable_level_fraction"]):
        if row[1] == "gen_commit_bin":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass
    data_portal.data()["disp_binary_commit_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional, will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["startup_plus_ramp_up_rate"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["shutdown_plus_ramp_down_rate"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispbincommit_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    # Ramp rates are optional, will default to 1 if not specified
    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["ramp_up_when_on_rate"]):
            if row[1] == "gen_commmit_bin" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["ramp_down_when_on_rate"]):
            if row[1] == "gen_commmit_bin" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["min_up_time_hours"]):
            if row[1] == "gen_commmit_bin" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_min_up_time_hours"] = \
            min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["min_down_time_hours"]):
            if row[1] == "gen_commmit_bin" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_min_down_time_hours"] = \
            min_down_time

    # Shut down ramp is optional, will default to 1 if not specified
    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["shutdown_plus_ramp_down_rate"]):
            if row[1] == "dispatchable_binary_commit" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate


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
                           "dispatch_binary_commit.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_operations_mw", "power_startup_mw",
                         "power_shutdown_mw", "power_total_mw",
                         "committed_mw",
                         "committed_units", "started_units", "stopped_units",
                         "startup_type_id"
                         ])

        for (p, tmp) in sorted(mod.\
                DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS):
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
                value(mod.Provide_Power_Operations_DispBinaryCommit_MW[p, tmp]),
                value(mod.StartUpPower_DispBinaryCommit_MW[p, tmp]),
                value(mod.ShutDownPower_DispBinaryCommit_MW[p, tmp]),
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp]),
                value(mod.DispBinCommit_Pmax_MW[p, tmp])
                * value(mod.Commit_Binary[p, tmp]),
                value(mod.Commit_Binary[p, tmp]),
                value(mod.Start_Binary[p, tmp]),
                value(mod.Stop_Binary[p, tmp]),
                value(mod.DispBinCommit_Active_Startup_Type[p, tmp])
                if p in mod.STARTUP_PROJECTS
                else None,
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
    print("project dispatch binary commit")
    # dispatch_binary_commit.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_dispatch_binary_commit",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(
            results_directory, "dispatch_binary_commit.csv"), "r") \
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
            power_operations_mw = row[9]
            power_startup_mw = row[10]
            power_shutdown_mw = row[11]
            power_total_mw = row[12]
            committed_mw = row[13]
            committed_units = row[14]
            started_units = row[15]
            stopped_units = row[16]
            startup_type_id = row[17]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                    balancing_type_project, horizon, timepoint,
                    timepoint_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_operations_mw,
                    power_startup_mw, power_shutdown_mw, power_total_mw,
                    committed_mw, committed_units, started_units, stopped_units,
                    startup_type_id)
            )
    insert_temp_sql ="""
        INSERT INTO temp_results_project_dispatch_binary_commit{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint,
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_operations_mw, power_startup_mw, 
        power_shutdown_mw, power_total_mw,
        committed_mw, committed_units, started_units, stopped_units,
        startup_type_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch_binary_commit
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_operations_mw, power_startup_mw, 
        power_shutdown_mw, power_total_mw,
        committed_mw, committed_units, started_units, stopped_units,
        startup_type_id)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_operations_mw, power_startup_mw, 
        power_shutdown_mw, power_total_mw,
        committed_mw, committed_units, started_units, stopped_units,
        startup_type_id
        FROM temp_results_project_dispatch_binary_commit{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

