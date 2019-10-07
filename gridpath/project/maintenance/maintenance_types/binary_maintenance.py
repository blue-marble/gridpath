#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

from pyomo.environ import Param, Set, Var, Constraint, Binary

from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Sets
    m.BINARY_MAINTENANCE_PROJECTS = Set(within=m.PROJECTS)
    m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_PERIODS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_PERIODS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_PERIODS
            if g in mod.BINARY_MAINTENANCE_PROJECTS
            )
    )
    # TODO: factor out this lambda rule, as it is used in all operational type
    #  modules and maintenance type modules
    m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.BINARY_MAINTENANCE_PROJECTS
            )
    )

    # Params
    m.maintenance_hours_per_period = Param(
        m.BINARY_MAINTENANCE_PROJECTS, m.PERIODS
    )
    m.hours_per_maintenance_event = Param(
        m.BINARY_MAINTENANCE_PROJECTS, m.PROJECTS
    )

    # Variables
    m.Down_for_Maintenance = Var(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )
    m.Start_Maintenance = Var(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )
    m.Stop_Maintenance = Var(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )

    # Constraints
    def total_scheduled_maintenance_per_period_rule(mod, g, p):
        """
        :param mod:
        :param g:
        :param p:
        :return:

        The generator must be down for maintenance for
        maintenance_hours_per_period in each period.
        TODO: it's possible that solve time will be faster if we make this
            constraint >= instead of ==, but then degeneracy could be an issue
        """
        return sum(mod.Down_for_Maintenance[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   ) \
            == mod.maintenance_hours_per_period[g, p]

    m.Total_Scheduled_Maintenance_Per_Period_Constraint = Constraint(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_PERIODS,
        rule=total_scheduled_maintenance_per_period_rule
    )

    def maintenance_start_and_stop_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        Constrain the start and stop maintenance variables based on the
        maintenance status in the current and previous timepoint. If the
        generator is down for maintenance in the current timepoint and was
        not down for maintenance in the previous timepoint, then the RHS is 1
        and Start_Maintenance must be set to 1. If the generator is not
        down for maintenance in the current timepoint and was down for
        maintenance in the previous timepoint, then the RHS is -1 and
        Stop_Maintenance must be set to 1.
        """
        return mod.Start_Maintenance[g, tmp] - mod.Stop_Maintenance[g, tmp] \
            == mod.Down_for_Maintenance[g, tmp] \
            - mod.Down_for_Maintenance[
                   g, mod.previous_timepoint[tmp, mod.balancing_type[g]]
               ]

    m.Maintenance_Event_Duration_Constraint = Constraint(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=maintenance_start_and_stop_rule
    )

    def maintenance_event_duration_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        If maintenance was started within hours_per_maintenance_event from the
        current timepoint, it could not have also been stopped during that
        time, i.e. the generator could not have changed its down for
        maintenance status and must still be down for maintenance in the
        current timepoint.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.hours_per_maintenance_event[g]
        )
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        return sum(
            mod.Start_Maintenance[g, tp] + mod.Stop_Maintenance[g, tp]
            for tp in relevant_tmps
        ) <= 1

    m.Maintenance_Event_Duration_Constraint = Constraint(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=maintenance_event_duration_rule
    )


def maintenance_derate_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 1 - mod.Down_for_Maintenance[g, tmp]
