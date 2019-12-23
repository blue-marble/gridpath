#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'binary-commit' generators,
i.e. generators with on/off commitment decisions.

The formulation is based on "Hidden power system inflexibilities imposed by
traditional unit commitment formulations", Morales-Espana et al. (2017).
A related, interesting paper with more background information is "Tight and
compact MILP formulation for the thermal unit commitment problem",
Morales-Espana et al. (2013).

Disclaimer: changing availabilty and timepoint duration not fully tested!
  - if availability changes during a startup process, things could get weird
  - varying timepoint durations are likely not entirely bug free

"""

from __future__ import division

from builtins import zip
import csv
import os.path
import numpy as np
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Binary, PercentFraction, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    setup_results_import, write_validation_to_database
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, determine_startup_elapsed_time


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
    *dispbincommit_startup_plus_ramp_up_rate* \ :sub:`bcg`\ -- the project's
    upward ramp rate limit during startup, defined as a fraction of its capacity
    per minute. This param, adjusted for timepoint duration, has to be equal or
    larger than *dispbincommit_min_stable_level_fraction* for the unit to be
    able to start up between timepoints. \n
    *dispbincommit_shutdown_plus_ramp_down_rate* \ :sub:`bcg`\ -- the project's
    downward ramp rate limit during shutdown, defined as a fraction of its
    capacity per minute. This param, adjusted for timepoint duration, has to be
    equal or larger than *dispbincommit_min_stable_level_fraction* for the
    unit to be able to shut down between timepoints. \n
    *dispbincommit_ramp_up_when_on_rate* \ :sub:`bcg`\ -- the project's
    upward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n
    *dispbincommit_ramp_down_when_on_rate* \ :sub:`bcg`\ -- the project's
    downward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n

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
        initialize=generator_subset_init("operational_type", "gen_commit_bin")
    )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS))

    m.DISPATCHABLE_BINARY_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS =\
        Set(dimen=3,
            within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS)
            )

    m.GEN_COMMIT_BIN_STR_RMP_PRJS = Set(
        within=m.DISPATCHABLE_BINARY_COMMIT_GENERATORS
    )

    m.GEN_COMMIT_BIN_STR_RMP_PRJS_TPS = Set(
        dimen=2, ordered=True
    )

    def get_startup_types_by_project(mod, g):
        """
        Get indexed set of startup types by project, ordered from hottest to
        coldest.
        :param mod:
        :param g:
        :return:
        """
        types = [s for (_g, s) in mod.GEN_COMMIT_BIN_STR_RMP_PRJS_TPS if g == _g]
        return types

    m.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ = Set(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS,
        initialize=get_startup_types_by_project,
        ordered=True
    )

    m.GEN_COMMIT_BIN_PRJS_OPR_TMPS_STR_TPS = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            for _g, s in mod.GEN_COMMIT_BIN_STR_RMP_PRJS_TPS
            if g == _g)
    )

    # --------------- Params - Required -------------------- #
    m.disp_binary_commit_min_stable_level_fraction = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        within=PercentFraction
    )

    # --------------- Params - Optional -------------------- #

    m.dispbincommit_min_up_time_hours = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        within=NonNegativeReals, default=0
    )
    m.dispbincommit_min_down_time_hours = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        within=NonNegativeReals, default=0
    )

    # TODO: move all comments/explanations to top?
    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    m.dispbincommit_ramp_up_when_on_rate = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        within=PercentFraction, default=1
    )
    m.dispbincommit_ramp_down_when_on_rate = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        within=PercentFraction, default=1
    )

    # Note: startup ramp rates can depend on down time (hot/cold start) so there
    # can be multiple startup types each with a cutoff down time. For shutdowns
    # there is only one type and one ramp rate. If the ramp rate normalized to
    # timepoint duration is longer than the timepoint, the model considers a
    # linear startup/shutdown trajectory.
    # NOTE: no inputs are treated differently. Shutodwn defaults to zero whereas
    # startup becomes param indexed by empty set
    m.dispbincommit_down_time_cutoff_hours = Param(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS_TPS,
        within=NonNegativeReals
    )

    m.dispbincommit_startup_plus_ramp_up_rate = Param(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS_TPS,
        within=PercentFraction, default=1
    )

    m.dispbincommit_shutdown_plus_ramp_down_rate = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        within=PercentFraction, default=1
    )

    # ------------------ Derived Params ------------------------ #
    def startup_duration_hours_rule(mod, g, s):
        """
        The startup duration in hours for each startup type (hot/cold).
        Calculated from the startup ramp rate and the minimum stable level.
        :param mod:
        :param g:
        :param s:
        :return:
        """
        return mod.disp_binary_commit_min_stable_level_fraction[g] \
            / mod.dispbincommit_startup_plus_ramp_up_rate[g, s] / 60
    m.dispbincommit_startup_duration_hours = Param(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS_TPS,
        rule=startup_duration_hours_rule
    )

    def shutdown_duration_hours_rule(mod, g):
        """
        The shutdown duration in hours. Calculated from the startup ramp rate
        and the minimum stable level.
        :param mod:
        :param g:
        :return:
        """
        return mod.disp_binary_commit_min_stable_level_fraction[g] \
            / mod.dispbincommit_shutdown_plus_ramp_down_rate[g] / 60
    m.dispbincommit_shutdown_duration_hours = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
        rule=shutdown_duration_hours_rule
    )

    def shutdown_ramp_fraction_per_timepoint_rule(mod, g, tmp):
        """
        Convert the ramp rate fraction per minute to ramp rate fraction per
        timepoint, and limit it between min_stable_level (pmin) and 1 (pmax).
        This limit is necessary to ensure the unit can't ramp down from above
        Pmax during shutdown, and to provide a seamless transition between
        the up (committed) and down (shutdown trajectory) states.

        Remember that *dispbincommit_shutdown_plus_ramp_down_rate* will default
        to 1 if no inputs are given, which will return 1 for this expression,

        If there are no inputs for *dispbincommit_shutdown_plus_ramp_down_rate*,
        the model will assume a default of 1, and this expression will also
        return 1, meaning it is a quick-start unit and it can ramp down from
        Pmax to zero within one timepoint.

        TODO: what happens if timepoint duration changes and some timepoints
         will be "quick-start" (can start within timepoint) and others aren't?
         What if this happens in the middle of a shutdown?
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        shutdown_fraction = mod.dispbincommit_shutdown_plus_ramp_down_rate[g] \
            * mod.number_of_hours_in_timepoint[tmp] * 60
        clipped = max(mod.disp_binary_commit_min_stable_level_fraction[g],
                      min(shutdown_fraction, 1))
        return clipped
    m.dispbincommit_shutdown_ramp_fraction_per_timepoint = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_ramp_fraction_per_timepoint_rule
    )

    def startup_ramp_fraction_per_timepoint_rule(mod, g, tmp):
        """
        Convert the ramp rate fraction per minute to ramp rate fraction per
        timepoint, and limit it between min_stable_level (pmin) and 1 (pmax).
        This limit is necessary to ensure the unit can't ramp to above Pmax
        during startup, and to provide a seamless transition between the down
        (startup trajectory) and up (committed) states.

        If no inputs are given for the project (not a startup project), assume
        the unit is quick-start and can ramp from zero to Pmax in one timepoint.

        We check the hottest start (highest startup ramp) vs. min_stable_level.
        If even the hottest start has a slower ramp per timepoint than the
        min_stable_level, it is a slow start unit and we set this ramp
        expression equal to the min_stable_level. We don't allow inputs where
        some of the starts are quick-start (within one timepoint) and others
        are not.

        TODO: not fully vetted for varying timepoint durations.
         if you start in timepoint 9, but have longer timepoint duration in tmp
         7, it seems like this longer timepoint duration in 7 is erroneously
         used to determine that we should skip the startup trajectory approach
         for tmp 7, even though it is actually a longer duration in tmp 8
         that might allow us to skip it
         background: timepoint of 1 hour requires you to do multi time point
         trajectory while timepoint of 2 hours requires you to do full startup
         within the tmp

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if g in mod.GEN_COMMIT_BIN_STR_RMP_PRJS:
            pmin = mod.disp_binary_commit_min_stable_level_fraction[g]
            fractions = [mod.dispbincommit_startup_plus_ramp_up_rate[g, s]
                         * mod.number_of_hours_in_timepoint[tmp] * 60
                         for s in mod.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ[g]]
            hottest_startup_fraction = max(fractions)
            if len(fractions) > 1 and hottest_startup_fraction >= pmin:
                raise ValueError(
                    """
                    Quick-start units should not have multiple startup types.
                    Check startup ramp inputs for project '{}'.
                    Make sure that there is either just one (quick) startup
                    ramp input or that all startup ramps are slow starts that 
                    take place over multiple timepoints.
                    """.format(g)
                )

            clipped = max(min(hottest_startup_fraction, 1), pmin)
            return clipped
        else:
            return 1
    m.dispbincommit_startup_ramp_fraction_per_timepoint = Param(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_ramp_fraction_per_timepoint_rule
    )

    def get_tmps_by_project_relevant_tmp_startup_type(mod):
        """
        Get list of the possible startup timepoints indexed by project,
        timepoint, and startup type. The tmp in the index is the "relevant
        timepoint" (which would be part of a trajectory) and the tmps in the
        list are the timepoints in which a start would affect the relevant
        timepoint's output (the "startup timepoints").

        Note: When determining relevant timepoints, the first relevant tmp is
        the tmp itself. However, for that case (relevant tmp = start tmp),
        constraint (31) in Morales-Espana et al. (2017) already sets the
        output for that timepoint (the end of a startup trajectory) to Pmin,
        so we can skip that timepoint here (if not we will end up setting the
        startup power at the end of the startup to Pmin twice).

        """
        result = {}
        for (g, tmp, s) in mod.\
                GEN_COMMIT_BIN_PRJS_OPR_TMPS_STR_TPS:

            # Make sure there is a dict entry for each (g, tmp, s)
            if (g, tmp, s) not in result.keys():
                result[g, tmp, s] = []

            # Skip first relevant timepoint which is *tmp* itself
            for relevant_tmp in determine_relevant_timepoints(mod, g, tmp,
                    mod.dispbincommit_startup_duration_hours[g, s])[1:]:
                # If we haven't run into this timepoint and startup type yet,
                # this is the first possible startup timepoint
                if (g, relevant_tmp, s) not in result.keys():
                    result[g, relevant_tmp, s] = [tmp]
                # If we've seen this relevant timepoint and startup type
                # before, append to our list of possible startup timepoints
                else:
                    result[g, relevant_tmp, s].append(tmp)
        return result
    m.tmps_by_prj_reltmp_stype = Param(
        m.GEN_COMMIT_BIN_PRJS_OPR_TMPS_STR_TPS,
        initialize=get_tmps_by_project_relevant_tmp_startup_type,
    )

    # -------------------- Variables - Binary -------------------- #
    m.Commit_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary
    )

    # ------------------ Variables - Continuous ------------------ #

    # Start_Binary is 1 for the first timepoint the unit is committed after not
    # being committed; it will be able to provide power and reserves in that
    # timepoint. Due to the binary logic constraint, this variable will be
    # forced to take on binary values, even though it is a continuous variable.
    m.Start_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction
    )
    # Stop_Binary is 1 for the first timepoint the unit is no longer committed
    # after being committed; As part of the shutdown process, the unit can still
    # provide power (and possibly reserves) in this timepoint. Due to the binary
    # logic constraint, this variable will be forced to take on binary values,
    # even though it is a continuous variable.
    m.Stop_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=PercentFraction
    )

    # Continuous variable which takes the value of 1 in the period where the
    # unit starts up for the start-up type l and 0 otherwise.
    # Due to the binary logic constraint, this variable will be forced to take
    # on binary values, even though it is a continuous variable.
    m.Start_Binary_Type = Var(
        m.GEN_COMMIT_BIN_PRJS_OPR_TMPS_STR_TPS,
        within=PercentFraction
    )

    # We assume that generator reaches this setpoint at start of timepoint
    m.Provide_Power_Above_Pmin_DispBinaryCommit_MW = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

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
        rule=pmax_rule
    )

    def pmin_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp] \
            * mod.disp_binary_commit_min_stable_level_fraction[g]
    m.DispBinCommit_Pmin_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=pmin_rule
    )

    def active_startup_rule(mod, g, tmp):
        return (sum(mod.Start_Binary_Type[g, tmp, s] * s
                    for s in mod.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ[g])
                if g in mod.GEN_COMMIT_BIN_STR_RMP_PRJS else 0)
    m.DispBinCommit_Active_Startup_Type = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=active_startup_rule
    )

    def synced_units_rule(mod, g, tmp):
        """
        Returns 1 if the unit is synchronized to the system and providing power
        (could be fully committed with controllable output, or during a startup
        or shutdown trajectory), and 0 if not.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        committed = mod.Commit_Binary[g, tmp]
        starting = 0
        stopping = 0

        # Calculate whether unit is starting up
        if g in mod.GEN_COMMIT_BIN_STR_RMP_PRJS:
            for s in mod.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ[g]:
                for stmp in mod.tmps_by_prj_reltmp_stype[g, tmp, s]:
                    starting += mod.Start_Binary_Type[g, stmp, s] \

        # Calculate whether unit is shutting down
        shutdown_duration = mod.dispbincommit_shutdown_duration_hours[g]
        if shutdown_duration <= mod.number_of_hours_in_timepoint[tmp]:
            stopping += mod.Stop_Binary[g, tmp]
        else:
            for t in determine_relevant_timepoints(mod, g, tmp,
                                                   shutdown_duration):
                stopping += mod.Stop_Binary[g, t]

        return committed + starting + stopping
    m.DispBinCommit_Synced_Units = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=synced_units_rule
    )

    def shutdown_power_rule(mod, g, tmp):
        """
        Get the shutdown trajectory power output (if any) for each timepoint.

        Go through the relevant timepoints in which a shutdown would affect
        *tmp* and add the appropriate shutdown power for *tmp* (will only count
        when unit actually shuts down in the relevant timepoint).

        The relevant timepoints are *tmp* itself and  all previous timepoints
        within shutdown_duration hours *tmp*. If the unit shuts down in any of
        these relevant timepoints (Stop_Binary[relevant_tmp] = 1), *tmp* will
        be part of a shutdown trajectory. The shutdown trajectory power depends
        on the shutdown ramp rate and the number of hours we are into the
        shutdown process.

        See constraint (37) in Morales-Espana et al. (2017), namely the
        summation in the shutdown trajectory from i=2 to i=SD+1.

        Example 1:
            tmp = 5,
            timepoint_duration_hours = 1 hour,
            shutdown_duration = 4 hours
            Pmin = 4 MW

            relevant timepoints = [5, 4, 3, 2], i.e. a shutdown in any of these
            timepoints would mean tmp 5 is part of a shutdown trajectory.

            relevant_shutdown_power in tmp 5 if unit stops in timepoint 5: 4 MW
                Note: this will already be set in the max_power_constraint_rule
                      so we skip this relevant timepoint@
            relevant_shutdown_power in tmp 5 if unit stops in timepoint 4: 3 MW
            relevant_shutdown_power in tmp 5 if unit stops in timepoint 3: 2 MW
            relevant_shutdown_power in tmp 5 if unit stops in timepoint 2: 1 MW

        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        shutdown_duration = mod.dispbincommit_shutdown_duration_hours[g]
        relevant_shutdown_power = 0
        time_into_shutdown = 0

        # Quick-start units don't have a shutdown trajectory
        if shutdown_duration <= mod.number_of_hours_in_timepoint[tmp]:
            return relevant_shutdown_power

        relevant_tmps_shutdown = determine_relevant_timepoints(
            mod, g, tmp, shutdown_duration)
        for i, t in enumerate(relevant_tmps_shutdown):
            # Skip the first relevant timepoint (t == tmp) since the unit will
            # be already set to Pmin at the start of the shutdown in the
            # *max_power_constraint_rule*
            if i > 0:
                relevant_shutdown_power += mod.Stop_Binary[g, t] \
                    * (mod.DispBinCommit_Pmin_MW[g, tmp]
                       - time_into_shutdown * 60
                       * mod.dispbincommit_shutdown_plus_ramp_down_rate[g]
                       * mod.DispBinCommit_Pmax_MW[g, t])
            time_into_shutdown += mod.number_of_hours_in_timepoint[t]

        return relevant_shutdown_power
    m.ShutDownPower_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_power_rule
    )

    def startup_power_rule(mod, g, tmp):
        """
        Get the startup trajectory power output (if any) for each timepoint.

        For each startup type, go through stmps in which a start would affect
        *tmp* and add the appropriate startup power for *tmp* (will only count
        when unit actually starts in stmp).

        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        startup_power = 0
        if g in mod.GEN_COMMIT_BIN_STR_RMP_PRJS:
            for s in mod.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ[g]:
                su_duration = mod.dispbincommit_startup_duration_hours[g, s]
                for stmp in mod.tmps_by_prj_reltmp_stype[g, tmp, s]:
                    startup_elapsed_time = determine_startup_elapsed_time(
                        mod, g, tmp, stmp, su_duration)

                    startup_power += mod.Start_Binary_Type[g, stmp, s] \
                        * startup_elapsed_time * 60 \
                        * mod.dispbincommit_startup_plus_ramp_up_rate[g, s] \
                        * mod.DispBinCommit_Pmax_MW[g, tmp]

        return startup_power
    m.StartUpPower_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_power_rule
    )

    def provide_power_rule(mod, g, tmp):
        """
        Equation (37) in Morales-Espana et al. (2017).

        Note: because GridPath assumes you enter the timepoint at your setpoint
        (vs. Morales-Espana who assumes you end the the timepoint at your
        setpoint), we replace y_t+1 with z_t. This means the unit can still
        provide power above Pmin in the shutdown timepoint (when it is
        technically no longer committed). See the *max_power_constraint_rule*
        for how the power above Pmin is constrained.

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp] \
            + mod.DispBinCommit_Pmin_MW[g, tmp] \
            * (mod.Commit_Binary[g, tmp] + mod.Stop_Binary[g, tmp]) \
            + mod.StartUpPower_DispBinaryCommit_MW[g, tmp] \
            + mod.ShutDownPower_DispBinaryCommit_MW[g, tmp]
    m.Provide_Power_DispBinaryCommit_MW = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        return mod.DispBinCommit_Pmax_MW[g, tmp] \
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
        return mod.DispBinCommit_Pmax_MW[g, tmp] \
            * mod.dispbincommit_ramp_down_when_on_rate[g] \
            * mod.number_of_hours_in_timepoint[tmp] \
            * 60  # convert min to hours
    m.DispBinCommit_Ramp_Down_Rate_MW_Per_Timepoint = Expression(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_rate_rule)

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

        See constraint (4) in Morales-Espana et al. (2017).

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

    def startup_type_constraint_rule(mod, g, tmp, s):
        """
        Startup_type s can only be activated (startup_type ≤ 1) if the unit has
        previously been down within the appropriate interval. The interval for
        startup type s is defined by the user specified boundary parameters
        mod.dispbincommit_down_time_cutoff_hours[s] and
        mod.dispbincommit_down_time_cutoff_hours[s+1].

        If we're at the coldest (last) startup type, there is no s+1 and the
        constraint is skipped. This is okay because the model will select a
        hotter, cheaper startup type if it can and there can only be one
        startup_type active at once (see next constraint). This also means the
        constraint will be skipped if there is only one startup type.

        The constraint works by first determining the relevant timepoints, i.e.
        the timepoints within [TSU,s ; TSU,s+1) hours from *tmp*. If the unit
        has been down in any of these timepoints, we can activate the startup
        variable of the associated startup type for timepoint *tmp* (but only if
        the unit is actually starting in timepoint *tmp*)

        Example: we are in timepoint 7 (hourly resolution) and the down time
        interval is 2-4 hours for a hot start and >4 hours for a cold start.
        This means timepoints 4 and 5 will be the relevant timepoints. A
        shutdown in any of those timepoints means that a start in timepoint 7
        would be a hot start.

        See constraint (7) in Morales-Espana et al. (2017).

        :param mod:
        :param g:
        :param tmp:
        :param s: startup_type
        :return:
        """

        # Coldest startup type is un-constrained
        if s == mod.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ[g][-1]:
            return Constraint.Skip

        # Get the timepoints within [TSU,s; TSU,s+1) hours from *tmp*
        relevant_tmps1 = determine_relevant_timepoints(
            mod, g, tmp, mod.dispbincommit_down_time_cutoff_hours[g, s])
        relevant_tmps2 = determine_relevant_timepoints(
            mod, g, tmp, mod.dispbincommit_down_time_cutoff_hours[g, s+1])
        relevant_tmps = set(relevant_tmps2) - set(relevant_tmps1)

        # Skip constraint if we are within TSU,s hours from the start of the
        # horizon (linear horizon boundary) or from the current tmp (circular
        # horizon boundary). We have no way to know whether unit was down
        # [TSU,s; TSU,s+1) hours ago so we can't know if this start type could
        # be active.
        if len(relevant_tmps) == 0:
            return Constraint.Skip

        # Equal to 1 if unit has been down within interval [TSU,s; TSU,s+1)
        # before hour t. This "activates" this particular startup type
        shutdown_within_interval = \
            sum(mod.Stop_Binary[g, tp] for tp in relevant_tmps)

        return mod.Start_Binary_Type[g, tmp, s] <= shutdown_within_interval

    m.DispBinCommit_Start_Binary_Type_Constraint = Constraint(
        m.GEN_COMMIT_BIN_PRJS_OPR_TMPS_STR_TPS,
        rule=startup_type_constraint_rule
    )

    def unique_startup_type_constraint_rule(mod, g, tmp):
        """
        Ensure that just one startup type is selected when the unit starts up.

        From Morales-Espana et al. (2013):
        "In the event that more than one SU type variable can be activated
        (delta-t,l ≤ 1) then (2) together with the objective function ensure
        that the hottest, which is the cheapest, possible option is always
        selected. Therefore, just one of the variables is activated (equal to
        one). That is, these variables take binary values even though they
        are modeled as continuous variables. This is due to the convex
        (monotonically increasing) characteristic of the exponential SU costs
        of thermal units"

        See constraint (8) in Morales-Espana et al. (2017) and constraint (2)
        in Morales-Espana et al. (2013).

        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        if g not in mod.GEN_COMMIT_BIN_STR_RMP_PRJS:
            return Constraint.Skip
        else:
            sum_startup_types = sum(
                mod.Start_Binary_Type[g, tmp, s]
                for s in mod.GEN_COMMIT_BIN_STR_TPS_BY_STR_RMP_PRJ[g]
            )

            return sum_startup_types == mod.Start_Binary[g, tmp]

    m.DispBinCommit_Unique_Startup_Type_Constraint = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=unique_startup_type_constraint_rule
    )

    def min_power_constraint_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below minimum stable level.
        This constraint is not in Morales-Espana et al. (2017) because they
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

        If the startup or shutdown takes longer than one timepoint (i.e. there
        is a trajectory) this constraint, in combination with the
        *provide_power_rule*, will set the total power output to Pmin in the
        startup timepoint (Start_Binary[tmp]=1) and shutdown timepoint
        (Stop_Binary[tmp]=1).

        If the startup or shutdown occurs within one timepoint (quick-start),
        this constraint, in combination with the *provide_power_rule*, will
        limit the total power output in the startup and shutdown timepoint to a
        value between Pmin and Pmax, depending on the startup ramp rate and the
        shutdown ramp rate.

        Constraint (31) in Morales-Espana et al. (2017)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # Power provision plus upward reserves shall not exceed maximum power.
        return \
            (mod.Provide_Power_Above_Pmin_DispBinaryCommit_MW[g, tmp]
             + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispBinCommit_Pmax_MW[g, tmp]
             - mod.DispBinCommit_Pmin_MW[g, tmp]) * mod.Commit_Binary[g, tmp] \
            - (mod.DispBinCommit_Pmax_MW[g, tmp]
               - mod.dispbincommit_startup_ramp_fraction_per_timepoint[g, tmp]
               * mod.DispBinCommit_Pmax_MW[g, tmp]) * mod.Start_Binary[g, tmp] \
            + (mod.dispbincommit_shutdown_ramp_fraction_per_timepoint[g, tmp]
               * mod.DispBinCommit_Pmax_MW[g, tmp]
               - mod.DispBinCommit_Pmin_MW[g, tmp]) * mod.Stop_Binary[g, tmp]

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

        Constraint (5) in Morales-Espana et al. (2017)

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

        Constraint (6) in Morales-Espana et al. (2017)
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

        Constraint (32) in Morales-Espana et al. (2017).

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

        Constraint (32) in Morales-Espana et al. (2017)
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
        curve.

        Note 1: we assume that when projects are derated for availability, the
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
            * mod.Provide_Power_DispBinaryCommit_MW[g, tmp] \
            + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
            * mod.Availability_Derate[g, tmp] \
            * mod.DispBinCommit_Synced_Units[g, tmp]
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
        return (mod.Commit_Binary[g, tmp]
                - mod.Commit_Binary[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
            * mod.DispBinCommit_Pmax_MW[g, tmp]


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

    # Ramp rate limits are optional, will default to 1 if not specified
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
            if row[1] == "gen_commit_bin" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["ramp_down_when_on_rate"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
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
            if row[1] == "gen_commit_bin" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_min_up_time_hours"] = \
            min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["min_down_time_hours"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["dispbincommit_min_down_time_hours"] = \
            min_down_time

    # Startup characteristics
    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "startup_chars.tab"),
        sep="\t"
    )

    startup_ramp_projects = set()
    startup_ramp_projects_types = list()
    down_time_cutoff_hours_dict = dict()
    startup_plus_ramp_up_rate_dict = dict()

    for i, row in df.iterrows():
        project = row["project"]
        startup_type_id = row["startup_type_id"]
        down_time_cutoff_hours = row["down_time_cutoff_hours"]
        startup_plus_ramp_up_rate = row["startup_plus_ramp_up_rate"]

        if down_time_cutoff_hours != "." and startup_plus_ramp_up_rate != ".":
            startup_ramp_projects.add(project)
            startup_ramp_projects_types.append((project, startup_type_id))
            down_time_cutoff_hours_dict[(project, startup_type_id)] = \
                float(down_time_cutoff_hours)
            startup_plus_ramp_up_rate_dict[(project, startup_type_id)] = \
                float(startup_plus_ramp_up_rate)

    if startup_ramp_projects:
        data_portal.data()["GEN_COMMIT_BIN_STR_RMP_PRJS"] = \
            {None: startup_ramp_projects}
        data_portal.data()["GEN_COMMIT_BIN_STR_RMP_PRJS_TPS"] = \
            {None: startup_ramp_projects_types}
        data_portal.data()["dispbincommit_down_time_cutoff_hours"] = \
            down_time_cutoff_hours_dict
        data_portal.data()["dispbincommit_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate_dict


def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    # TODO: might have to add startup_chars_scenario_id back to table for
    #  input validations
    startup_chars = c.execute(
        """
        SELECT project, 
        startup_type_id, down_time_cutoff_hours, startup_plus_ramp_up_rate
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, startup_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}') AS op_char
        USING(project)
        LEFT OUTER JOIN
        inputs_project_startup_chars
        USING(project, startup_chars_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        AND startup_chars_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   "gen_commit_bin",
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return startup_chars


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    validation_results = []

    # Get the project input data
    startup_chars = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Get project operational input data
    c1 = conn.cursor()
    projects = c1.execute(
        """SELECT 
            project, operational_type,
            min_stable_level,
            shutdown_plus_ramp_down_rate,
            min_down_time_hours
        FROM inputs_project_portfolios
        INNER JOIN
            (SELECT 
                project, operational_type,
                min_stable_level,
                shutdown_plus_ramp_down_rate,
                min_down_time_hours
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}
            AND operational_type = '{}'
            ) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        """.format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            "gen_commit_bin",
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    # Convert input data into DataFrame
    su_df = pd.DataFrame(
        data=startup_chars.fetchall(),
        columns=[s[0] for s in startup_chars.description]
    )
    prj_df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Check startup_chars inputs
    validation_errors = validate_startup_type_inputs(su_df, prj_df)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS_SCENARIO_ID",
             "inputs_project_startup_chars",
             "Invalid/Missing startup characteristics inputs",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    startup_chars.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    startup_chars = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If startup_chars.tab file already exists, append rows to it
    if os.path.isfile(os.path.join(inputs_directory, "startup_chars.tab")):
        with open(os.path.join(inputs_directory, "startup_chars.tab"),
                  "a") as startup_chars_file:
            writer = csv.writer(startup_chars_file, delimiter="\t")
            for row in startup_chars:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)
    # If startup_chars.tab does not exist, write header first, then add data
    else:
        with open(os.path.join(inputs_directory, "startup_chars.tab"),
                  "w", newline="") as startup_chars_file:
            writer = csv.writer(startup_chars_file, delimiter="\t")

            # Write header
            writer.writerow(["project", "startup_type_id",
                             "down_time_cutoff_hours",
                             "startup_plus_ramp_up_rate"])

            for row in startup_chars:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)


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
                         "power_mw", "committed_mw",
                         "committed_units", "started_units", "stopped_units",
                         "synced_units", "startup_type_id"
                         ])

        for (p, tmp) in mod.\
                DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
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
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp]),
                value(mod.DispBinCommit_Pmax_MW[p, tmp])
                * value(mod.Commit_Binary[p, tmp]),
                value(mod.Commit_Binary[p, tmp]),
                value(mod.Start_Binary[p, tmp]),
                value(mod.Stop_Binary[p, tmp]),
                value(mod.DispBinCommit_Synced_Units[p, tmp]),
                value(mod.DispBinCommit_Active_Startup_Type[p, tmp])
                if p in mod.GEN_COMMIT_BIN_STR_RMP_PRJS
                else None
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
            power_mw = row[9]
            committed_mw = row[10]
            committed_units = row[11]
            started_units = row[12]
            stopped_units = row[13]
            startup_type_id = row[14]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                    balancing_type_project, horizon, timepoint,
                    timepoint_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw,
                    committed_mw, committed_units, started_units, stopped_units,
                    startup_type_id)
            )
    insert_temp_sql ="""
        INSERT INTO temp_results_project_dispatch_binary_commit{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint,
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_mw,
        committed_mw, committed_units, started_units, stopped_units,
        startup_type_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch_binary_commit
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_mw,
        committed_mw, committed_units, started_units, stopped_units,
        startup_type_id)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_mw,
        committed_mw, committed_units, started_units, stopped_units,
        startup_type_id
        FROM temp_results_project_dispatch_binary_commit{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def validate_startup_type_inputs(startup_df, project_df):
    """

    Note: we assume the startup types are entered in order; could order the
    dataframe first if needed

    TODO: additional checks:
     - check for excessively slow startup ramps which would wrap around the
       horizon and disallow any startups
     - could also add type checking here (resp. int and float?)
     - check for startup fuel and disallow combination of startup
       ramps and startup fuels (double counts it)

    :param startup_df: dataframe with startup_chars (see startup_chars.tab)
    :param project_df: dataframe with project_chars (see projects.tab)
    :return:
    """

    results = []

    projects = startup_df["project"].unique()
    for project in projects:
        startups = startup_df[startup_df['project'] == project]
        prj_chars = project_df[project_df['project'] == project]
        min_stable_level = prj_chars["min_stable_level"].iloc[0]

        if "min_down_time_hours" not in project_df.columns:
            min_down_time = 0  # default is 0 hour down time
        elif pd.isna(prj_chars["min_down_time_hours"].iloc[0]):
            min_down_time = 0
        else:
            min_down_time = prj_chars["min_down_time_hours"].iloc[0]

        if "shutdown_plus_ramp_down_rate" not in project_df.columns:
            shutdown_ramp = 1
        elif pd.isna(prj_chars["shutdown_plus_ramp_down_rate"].iloc[0]):
            shutdown_ramp = 1
        else:
            shutdown_ramp = prj_chars["shutdown_plus_ramp_down_rate"].iloc[0]

        # Note: take the slowest start here
        if pd.isna(startups["startup_plus_ramp_up_rate"].iloc[-1]):
            startup_ramp = 1
        else:
            startup_ramp = startups["startup_plus_ramp_up_rate"].iloc[-1]

        # TODO: hacky fix; should be more elegant way to deal with this,
        #  and something that doesn't break down when modeling subhourly tmps
        if shutdown_ramp == 1:
            shutdown_duration = 0
        else:
            shutdown_duration = min_stable_level / shutdown_ramp / 60

        if startup_ramp == 1:
            startup_duration = 0
        else:
            startup_duration = min_stable_level / startup_ramp / 60

        startup_plus_shutdown_duration = shutdown_duration + startup_duration

        # Check that startup and shutdown fit within min down time (to avoid
        # overlap of startup and shutdown trajectory)
        if startup_plus_shutdown_duration > min_down_time:
            # might be okay if startup ramp up rate is big enough for you to
            # go straight to pmin?
            results.append(
                "Project '{}': Startup ramp duration of coldest start + "
                "shutdown ramp duration should be less than the minimum "
                "down time"
                .format(project)
            )

        if (len(startups) > 1 and prj_chars["operational_type"].iloc[0] not in
                ["gen_commit_bin", "gen_commit_lin"]):
            results.append(
                "Project '{}': Only gen_commit_bin and gen_commit_lin "
                "operational types can have multiple startup types!"
                .format(project)
            )

        startup_id_mask = pd.isna(startups["startup_type_id"])
        down_time_mask = pd.isna(startups["down_time_cutoff_hours"])
        invalids = startup_id_mask | down_time_mask
        if invalids.any():
            results.append(
                "Project '{}': startup_type_id and down_time_cutoff_hours "
                "should be defined for each startup type."
                .format(project)
            )
        else:
            #  make sure ID for startup type is unique and auto-increment
            id_diff = np.diff(startups["startup_type_id"])
            if sum(id_diff) != len(id_diff):
                results.append(
                    "Project '{}': Startup_type_id should be auto-increment "
                    "(unique and incrementing by 1)"
                    .format(project)
                )

            # check that down time is equal to project opchars min down time
            if startups["down_time_cutoff_hours"].iloc[0] != min_down_time:
                results.append(
                    "Project '{}': down_time_cutoff_hours for hottest startup "
                    "type should be equal to project's minimum down time"
                    .format(project)
                )

            # check that down time increases with startup_type_id
            dt_diff = np.diff(startups["down_time_cutoff_hours"])
            if np.any(dt_diff <= 0):
                results.append(
                    "Project '{}': down_time_cutoff_hours should increase with "
                    "startup_type_id"
                    .format(project)
                )

        # Check startup ramp inputs
        column = "startup_plus_ramp_up_rate"

        # TODO: remove since can't be empty now?
        # Either all values are None or none at all
        nas = pd.isna(startups[column])
        if nas.any() and len(startups[column].unique()) > 1:
            results.append(
                "Project '{}': {} has has no inputs for some of the "
                "startup types; should either have inputs for all "
                "startup types, or none at all"
                .format(project, column)
            )
        elif nas.all():
            pass
        # Startup rate should decrease for colder starts
        elif np.any(np.diff(startups[column]) >= 0):
            results.append(
                "Project '{}': {} should decrease with increasing "
                "startup_type_id (colder starts are slower)"
                .format(project, column)
            )

    return results
