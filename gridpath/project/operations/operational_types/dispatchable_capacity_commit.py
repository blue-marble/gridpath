#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of dispatchable generators with 'capacity
commitment,' i.e. commit some level of capacity below the total capacity.
This approach can be good for modeling 'fleets' of generators, e.g. a total
2000 MW of 500-MW units, so if 2000 MW are committed 4 generators (x 500 MW)
are committed. Integer commitment is not enforced; capacity commitment with
this approach is continuous.
"""

from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Constraint, Param, NonNegativeReals, \
    NonPositiveReals, PercentFraction, Reals, value, Expression

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    write_validation_to_database, check_req_prj_columns
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we define the set of dispatchable-capacity-commit generators:
    *DISPATCHABLE_CAPACITY_COMMIT_GENERATORS*
    (:math:`CCG`, index :math:`ccg`) and use this set to get the subset of
    *PROJECT_OPERATIONAL_TIMEPOINTS* with :math:`g \in CCG` -- the
    *DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`CCG\_OT`).

    We define several operational parameters over :math:`CCG`: \n
    *disp_cap_commit_min_stable_level_fraction* \ :sub:`ccg`\ -- the minimum
    stable level of the project, defined as a fraction of its
    capacity \n
    *unit_size_mw* \ :sub:`ccg`\ -- the unit size for the
    project, which is needed to calculate fuel burn if the project
    represents a fleet \n
    *dispcapcommit_startup_plus_ramp_up_rate* \ :sub:`ccg`\ -- the project's
    upward ramp rate limit during startup, defined as a fraction of its capacity
    per minute. This param, adjusted for timepoint duration, has to be equal or
    larger than *disp_cap_commit_min_stable_level_fraction* for the unit to be
    able to start up between timepoints. \n
    *dispcapcommit_shutdown_plus_ramp_down_rate* \ :sub:`ccg`\ -- the project's
    downward ramp rate limit during shutdown, defined as a fraction of its
    capacity per minute. This param, adjusted for timepoint duration, has to be
    equal or larger than *disp_cap_commit_min_stable_level_fraction* for the
    unit to be able to shut down between timepoints. \n
    *dispcapcommit_ramp_up_when_on_rate* \ :sub:`ccg`\ -- the project's
    upward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n
    *dispcapcommit_ramp_down_when_on_rate* \ :sub:`ccg`\ -- the project's
    downward ramp rate limit during operations, defined as a fraction of its
    capacity per minute. \n

    *min up time*, *min down time* -- formulation not
    documented yet

    The power provision variable for dispatchable-capacity-commit generators,
    *Provide_Power_DispCapacityCommit_MW*, is defined over
    *DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    Commit_Capacity_MW is the continuous variable to represent commitment
    state of a project. It is also defined over over
    *DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    The main constraints on dispatchable-capacity-commit project power
    provision are as follows:

    For :math:`(ccg, tmp) \in CCG\_OT`: \n
    :math:`Commit\_Capacity\_MW_{ccg, tmp} \leq Capacity\_MW_{ccg,p^{tmp}}`
    :math:`Provide\_Power\_DispCapacityCommit\_MW_{ccg, tmp} \geq
    disp\_cap\_commit\_min\_stable\_level\_fraction_{ccg} \\times
    Commit\_Capacity\_MW_{ccg,tmp}`
    :math:`Provide\_Power\_DispCapacityCommit\_MW_{ccg, tmp} \leq
    Commit\_Capacity\_MW_{ccg,tmp}`
    """

    # Sets and params
    m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "dispatchable_capacity_commit")
    )

    m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS))

    m.DISPATCHABLE_CAPACITY_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=3,
            within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS))

    m.unit_size_mw = Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
                           within=NonNegativeReals)
    m.disp_cap_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction)
    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    m.dispcapcommit_startup_plus_ramp_up_rate = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcapcommit_shutdown_plus_ramp_down_rate = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcapcommit_ramp_up_when_on_rate = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcapcommit_ramp_down_when_on_rate = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispcapcommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=1)
    m.dispcapcommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=NonNegativeReals, default=1)

    # Variables
    m.Provide_Power_DispCapacityCommit_MW = \
        Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    m.Commit_Capacity_MW = \
        Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals
            )
    m.Fuel_Burn_DispCapCommit_MMBTU = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    # Expressions
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.DispCapCommit_Upwards_Reserves_MW = Expression(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.DispCapCommit_Downwards_Reserves_MW = Expression(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)

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
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, tmp]
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
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] \
            + mod.DispCapCommit_Upwards_Reserves_MW[g, tmp] \
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
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] \
            - mod.DispCapCommit_Downwards_Reserves_MW[g, tmp] \
            >= mod.Commit_Capacity_MW[g, tmp] \
            * mod.disp_cap_commit_min_stable_level_fraction[g]
    m.DispCapCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )

    # Optional
    # Constrain ramps

    # We'll have separate treatment of ramps of:
    # generation that is online in both the current and the previous timepoint
    # and of
    # generation that is either started up or shut down since the previous
    # timepoint

    # Ramp_Up_Startup_MW and Ramp_Down_Shutdown_MW must be able to take
    # either positive  or negative values, as they are both constrained by
    # a product of a positive number and the difference committed capacity
    # between the current and previous timepoints (which needs to be able to
    # take on both positive values when turning units on and negative values
    # when turning units off)
    # They also need to be separate variables, as if they were combined,
    # the only solution would be for there to be no startups/shutdowns
    m.Ramp_Up_Startup_MW = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Reals
    )
    m.Ramp_Down_Shutdown_MW = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Reals
    )

    m.Ramp_Up_When_On_MW = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )
    m.Ramp_Down_When_On_MW = Var(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonPositiveReals
    )

    # Startups and shutdowns
    def ramp_up_off_to_on_constraint_rule(mod, g, tmp):
        """
        When turning on, generators can ramp up to a certain fraction of
        started up capacity. This fraction must be greater than or equal to
        the minimum stable level for the generator to be able to turn on.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Ramp_Up_Startup_MW[g, tmp] \
                <= \
                (mod.Commit_Capacity_MW[g, tmp]
                 - mod.Commit_Capacity_MW[
                     g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]) \
                * mod.dispcapcommit_startup_plus_ramp_up_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp, mod.balancing_type[g]]]
    m.Ramp_Up_Off_to_On_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_off_to_on_constraint_rule
    )

    def ramp_up_on_to_on_constraint_rule(mod, g, tmp):
        """
        Generators online in the last timepoint, if still online, could have
        ramped up at a rate at or below the online capacity times a
        pre-specified ramp rate fraction. The max on to on ramp up
        allowed is if they all stayed online. Startups are treated separately.
        There are limitations to this approach. For example, if online
        capacity was producing at full power at t-2 and t-1, some additional
        capacity was turned on at t-1 and ramped to some level above its
        Pmin but not full output, this constraint would allow for the total
        committed capacity in t-1 to be ramped up, even though in reality
        only the started up capacity can be ramped as the capacity from t-2
        is already producing at full power. In reality, this situation is
        unlikely to be an issue, as most generators can ramp from Pmin to
        Pmax fully in an hour, so the fact that this constraint is too lax
        in this situation does not matter when modeling fleets at an hourly
        or coarser resolution.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Ramp_Up_When_On_MW[g, tmp] \
                <= \
                mod.Commit_Capacity_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type[g]]] \
                * mod.dispcapcommit_ramp_up_when_on_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp, mod.balancing_type[g]]]
    m.Ramp_Up_When_On_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_on_to_on_constraint_rule
    )

    def ramp_up_on_to_on_headroom_constraint_rule(mod, g, tmp):
        """
        Generators online in the previous timepoint that are still online
        could not have ramped up above their total online capacity, i.e. not
        more than their available headroom in the previous timepoint.
        The maximum possible headroom in the previous timepoint is equal to
        the difference between committed capacity and (power provided minus
        downward reserves).
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # TODO: check behavior more carefully (same for ramp down)
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Ramp_Up_When_On_MW[g, tmp] \
                <= \
                mod.Commit_Capacity_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type[g]]] \
                - (mod.Provide_Power_DispCapacityCommit_MW[
                    g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]
                   - mod.DispCapCommit_Downwards_Reserves_MW[
                    g, mod.previous_timepoint[tmp, mod.balancing_type[g]]])
    m.Ramp_Up_When_On_Headroom_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_on_to_on_headroom_constraint_rule
    )

    def ramp_up_constraint_rule(mod, g, tmp):
        """
        The ramp up (power provided in the current timepoint minus power
        provided in the previous timepoint), adjusted for any reserve provision
        in the current and previous timepoint, cannot exceed a prespecified
        ramp rate (expressed as fraction of capacity)
        Two components:
        1) Ramp_Up_Startup_MW (see Ramp_Up_Off_to_On_Constraint above):
        If we are turning generators on since the previous timepoint, we will
        allow the ramp of going from 0 to minimum stable level + some
        additional ramping : the dispcapcommit_startup_plus_ramp_up_rate
        parameter
        2) Ramp_Up_When_On_MW (see Ramp_Up_When_On_Constraint and
        Ramp_Up_When_On_Headroom_Constraint above):
        Units committed in both the current timepoint and the previous
        timepoint could have ramped up at a certain rate since the previous
        timepoint
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # start up the full capacity and ramp up the full operable range
        # between timepoints, constraint won't bind, so skip
        elif (mod.dispcapcommit_startup_plus_ramp_up_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type[g]]]
              >= 1
              and
              mod.dispcapcommit_ramp_up_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type[g]]]
              >= (1 - mod.disp_cap_commit_min_stable_level_fraction[g])
              ):
            return Constraint.Skip
        else:
            return (mod.Provide_Power_DispCapacityCommit_MW[g, tmp]
                    + mod.DispCapCommit_Upwards_Reserves_MW[g, tmp]) \
                - (mod.Provide_Power_DispCapacityCommit_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]
                   - mod.DispCapCommit_Downwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]
                   ) \
                <= \
                mod.Ramp_Up_Startup_MW[g, tmp] \
                + mod.Ramp_Up_When_On_MW[g, tmp]

    m.DispCapCommit_Ramp_Up_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_up_constraint_rule
    )

    # Ramp down
    def ramp_down_on_to_off_constraint_rule(mod, g, tmp):
        """
        When turning off, generators can ramp down from a certain
        fraction of the capacity to be shut down to 0. This fraction must be
        greater than or equal to the minimum stable level for the generator
        to be able to turn off.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Ramp_Down_Shutdown_MW[g, tmp] \
                >= \
                (mod.Commit_Capacity_MW[g, tmp]
                 - mod.Commit_Capacity_MW[
                     g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]) \
                * mod.dispcapcommit_shutdown_plus_ramp_down_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp, mod.balancing_type[g]]]
    m.Ramp_Down_On_to_Off_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_on_to_off_constraint_rule
    )

    def ramp_down_on_to_on_constraint_rule(mod, g, tmp):
        """
        Generators still online in the current timepoint could have ramped
        down at a rate at or below the online capacity times a pre-specified
        ramp rate fraction. Shutdowns are treated separately.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Ramp_Down_When_On_MW[g, tmp] \
                >= \
                mod.Commit_Capacity_MW[g, tmp] \
                * (-mod.dispcapcommit_ramp_down_when_on_rate[g]) * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp, mod.balancing_type[g]]]
    m.Ramp_Down_When_On_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_on_to_on_constraint_rule
    )

    def ramp_down_on_to_on_headroom_constraint_rule(mod, g, tmp):
        """
        Generators still online in the current timepoint could not have ramped
        down more than their current headroom. The maximum possible headroom is
        equal to the difference between committed capacity and (power provided
        minus downward reserves).
        Note: Ramp_Down_When_On_MW is negative when a unit is ramping down, so
        we add a negative sign before it the constraint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return -mod.Ramp_Down_When_On_MW[g, tmp] \
                <= \
                mod.Commit_Capacity_MW[g, tmp] \
                - (mod.Provide_Power_DispCapacityCommit_MW[g, tmp]
                   - mod.DispCapCommit_Downwards_Reserves_MW[g, tmp])
    m.Ramp_Down_When_On_Headroom_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_down_on_to_on_headroom_constraint_rule
    )

    def ramp_down_constraint_rule(mod, g, tmp):
        """
        The ramp down (power provided in the current timepoint minus power
        provided in the previous timepoint), adjusted for any reserve provision
        in the current and previous timepoint, cannot exceed a prespecified
        ramp rate (expressed as fraction of capacity)
        Two components:
        1) Ramp_Down_Shutdown_MW (see Ramp_Down_On_to_Off_Constraint above):
        If we are turning generators off, we will allow the ramp of
        going from minimum stable level to 0 + some additional ramping from
        above minimum stable level
        2) Ramp_Down_When_On_MW (see Ramp_Down_When_On_Constraint and
        Ramp_Down_When_On_Headroom_Constraint above):
        Units still committed in the current timepoint could have ramped down
        at a certain rate since the previous timepoint
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # shut down the full capacity and ramp down the full operable range
        # between timepoints, constraint won't bind, so skip
        elif (mod.dispcapcommit_shutdown_plus_ramp_down_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type[g]]]
              >= 1
              and
              mod.dispcapcommit_ramp_down_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type[g]]]
              >= (1-mod.disp_cap_commit_min_stable_level_fraction[g])
              ):
            return Constraint.Skip
        else:
            return (mod.Provide_Power_DispCapacityCommit_MW[g, tmp]
                    - mod.DispCapCommit_Downwards_Reserves_MW[g, tmp]) \
                - (mod.Provide_Power_DispCapacityCommit_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]
                   + mod.DispCapCommit_Upwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]
                   ) \
                >= \
                mod.Ramp_Down_Shutdown_MW[g, tmp] \
                + mod.Ramp_Down_When_On_MW[g, tmp]
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
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.DispCapCommit_Startup_MW[g, tmp] \
                >= mod.Commit_Capacity_MW[g, tmp] \
                - mod.Commit_Capacity_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]

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
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.DispCapCommit_Shutdown_MW[g, tmp] \
                   >= mod.Commit_Capacity_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type[g]]] \
                   - mod.Commit_Capacity_MW[g, tmp]

    m.DispCapCommit_Shutdown_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_constraint_rule
    )

    def min_up_time_constraint_rule(mod, g, tmp):
        """
        :param mod: the Pyomo AbstractModel object
        :param g: a project
        :param tmp: a timepoint
        :return: rule for constraint DispCapCommit_Min_Up_Time_Constraint

        When units are started, they have to stay on for a minimum number
        of hours described by the dispcapcommit_min_up_time_hours parameter.
        The constraint is enforced by ensuring that the online capacity
        (committed capacity) is at least as large as the amount of capacity
        that was started within min down time hours.

        We ensure capacity turned on less than the minimum up time ago is
        still on in the current timepoint *tmp* by checking how much capacity
        was turned on in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to dispcapcommit_min_up_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        capacities.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.dispcapcommit_min_up_time_hours[g]
        )

        # If only the current timepoint is determined to be relevant,
        # this constraint is redundant (it will simplify to
        # Commit_Capacity_MW[g, previous_timepoint[tmp]} >= 0)
        # This also takes care of the first timepoint in a linear horizon
        # setting, which has only *tmp* in the list of relevant timepoints
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        # Otherwise, we must have at least as much capacity committed as was
        # started up in the relevant timepoints
        else:
            capacity_turned_on_min_up_time_or_less_hours_ago = \
                sum(mod.DispCapCommit_Startup_MW[g, tp]
                    for tp in relevant_tmps)

            return mod.Commit_Capacity_MW[g, tmp] \
                >= capacity_turned_on_min_up_time_or_less_hours_ago

    m.DispCapCommit_Min_Up_Time_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_up_time_constraint_rule
    )

    def min_down_time_constraint_rule(mod, g, tmp):
        """
        :param mod: the Pyomo AbstractModel object
        :param g: a project
        :param tmp: a timepoint
        :return: rule for constraint DispCapCommit_Min_Down_Time_Constraint

        When units are stopped, they have to stay off for a minimum number
        of hours described by the dispcapcommit_min_down_time_hours parameter.
        The constraint is enforced by ensuring that the offline capacity
        (available capacity minus committed capacity) is at least as large
        as the amount of capacity that was stopped within min down time hours.

        We ensure capacity turned off less than the minimum down time ago is
        still off in the current timepoint *tmp* by checking how much capacity
        was turned off in each 'relevant' timepoint (i.e. a timepoint that
        begins more than or equal to dispcapcommit_min_down_time_hours ago
        relative to the start of timepoint *tmp*) and then summing those
        capacities.
        """

        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.dispcapcommit_min_down_time_hours[g]
        )

        capacity_turned_off_min_down_time_or_less_hours_ago = \
            sum(mod.DispCapCommit_Shutdown_MW[g, tp]
                for tp in relevant_tmps)

        # If only the current timepoint is determined to be relevant,
        # this constraint is redundant (it will simplify to
        # Commit_Capacity_MW[g, previous_timepoint[tmp]} >= 0)
        # This also takes care of the first timepoint in a linear horizon
        # setting, which has only *tmp* in the list of relevant timepoints
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        # Otherwise, we must have at least as much capacity off as was shut
        # down in the relevant timepoints
        else:
            return mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.availability_derate[g, tmp] \
                - mod.Commit_Capacity_MW[g, tmp] \
                >= capacity_turned_off_min_down_time_or_less_hours_ago

    m.DispCapCommit_Min_Down_Time_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=min_down_time_constraint_rule
    )

    def fuel_burn_constraint_rule(mod, g, tmp, s):
        """
        Fuel burn is set by piecewise linear representation of input/output
        curve.

        Note: The availability de-rate is already accounted for in
        Commit_Capacity_MW so we don't need to multiply the intercept
        by the availability_derate like we do for always_on generators.
        :param mod:
        :param g:
        :param tmp:
        :param s:
        :return:
        """
        return \
            mod.Fuel_Burn_DispCapCommit_MMBTU[g, tmp] \
            >= \
            mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
            * mod.Provide_Power_DispCapacityCommit_MW[g, tmp] \
            + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
            * (mod.Commit_Capacity_MW[g, tmp] / mod.unit_size_mw[g])
    m.Fuel_Burn_DispCapCommit_Constraint = Constraint(
        m.DISPATCHABLE_CAPACITY_COMMIT_FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
        rule=fuel_burn_constraint_rule
    )


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by dispatchable-capacity-commit
     generators

    Power provision for dispatchable-capacity-commit generators is a
    variable constrained to be between the minimum stable level (defined as
    a fraction of committed capacity) and the committed capacity.
    """
    return mod.Provide_Power_DispCapacityCommit_MW[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from dispatchable generators is an endogenous variable.
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


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
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
        return mod.Fuel_Burn_DispCapCommit_MMBTU[g, tmp]
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
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
            == "linear":
        return None
    else:
        return mod.Commit_Capacity_MW[g, tmp] \
         - mod.Commit_Capacity_MW[
                   g, mod.previous_timepoint[tmp, mod.balancing_type[g]]]


def power_delta_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] \
            == "linear":
        pass
    else:
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] - \
               mod.Provide_Power_DispCapacityCommit_MW[
                   g, mod.previous_timepoint[tmp, mod.balancing_type[g]]
               ]


def fix_commitment(mod, g, tmp):
    """
    Fix committed capacity based on number of committed units and unit size
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Capacity_MW[g, tmp] = \
        mod.fixed_commitment[g, mod.previous_stage_timepoint_map[tmp]]
    mod.Commit_Capacity_MW[g, tmp].fixed = True


def load_module_specific_data(mod, data_portal, scenario_directory,
                              subproblem, stage):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    unit_size_mw = dict()
    min_stable_fraction = dict()
    startup_plus_ramp_up_rate = dict()
    shutdown_plus_ramp_down_rate = dict()
    ramp_up_when_on_rate = dict()
    ramp_down_when_on_rate = dict()
    min_up_time = dict()
    min_down_time = dict()

    header = pd.read_csv(os.path.join(scenario_directory, subproblem, stage,
                                      "inputs", "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["startup_plus_ramp_up_rate",
                        "shutdown_plus_ramp_down_rate",
                        "ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours", "min_down_time_hours"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs", "projects.tab"),
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

    # Ramp rate limits are optional; will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_plus_ramp_up_rate"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "min_up_time_hours"]
                       ):
            if row[1] == "dispatchable_capacity_commit" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
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
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispcapcommit_min_down_time_hours"] = \
            min_down_time


def export_module_specific_results(mod, d, scenario_directory, subproblem, stage):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "dispatch_capacity_commit.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type, "
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "committed_mw", "committed_units"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.balancing_type[p],
                mod.horizon[tmp, mod.balancing_type[p]],
                tmp,
                mod.timepoint_weight[tmp],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Power_DispCapacityCommit_MW[p, tmp]),
                value(mod.Commit_Capacity_MW[p, tmp]),
                value(mod.Commit_Capacity_MW[p, tmp]) / mod.unit_size_mw[p]
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
    print("project dispatch capacity commit")
    # dispatch_capacity_commit.csv
    c.execute(
        """DELETE FROM results_project_dispatch_capacity_commit
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_dispatch_capacity_commit"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_dispatch_capacity_commit"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            subproblem_id INTEGER,
            stage_id INTEGER,
            balancing_type VARCHAR(64),
            horizon INTEGER,
            timepoint INTEGER,
            timepoint_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            technology VARCHAR(32),
            power_mw FLOAT,
            committed_mw FLOAT,
            committed_units FLOAT,
            PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(
            results_directory, "dispatch_capacity_commit.csv"), "r") \
            as cc_dispatch_file:
        reader = csv.reader(cc_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            load_zone = row[8]
            technology = row[7]
            power_mw = row[9]
            committed_mw = row[10]
            committed_units = row[11]
            c.execute(
                """INSERT INTO temp_results_project_dispatch_capacity_commit"""
                + str(scenario_id) + """
                    (scenario_id, project, period, subproblem_id, stage_id, 
                    balancing_type, horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, 
                    power_mw, committed_mw, committed_units)
                    VALUES ({}, '{}', {}, {}, {}, '{}', {}, {}, {}, {}, 
                    '{}', '{}', {}, {}, {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    balancing_type, horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology,
                    power_mw, committed_mw, committed_units
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_capacity_commit
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, balancing_type, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        committed_mw, committed_units)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, balancing_type,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, committed_mw, committed_units
        FROM temp_results_project_dispatch_capacity_commit"""
        + str(scenario_id) +
        """
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_dispatch_capacity_commit""" + str(
            scenario_id) +
        """;"""
    )
    db.commit()


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

    c = conn.cursor()
    projects = c.execute(
        """SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND operational_type = '{}'""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "dispatchable_capacity_commit"
        )
    )

    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Check that unit size and min stable level are specified
    # (not all operational types require this input)
    req_columns = [
        "min_stable_level",
        "unit_size_mw"
    ]
    validation_errors = check_req_prj_columns(df, req_columns, True,
                                          "Dispatchable_capacity_commit")
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
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                          "Dispatchable_capacity_commit")
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

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
