#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Projects with timepoint-level, binary maintenance decision variables.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, Constraint, Binary

from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints
from gridpath.project.maintenance.maintenance_types.common_functions import \
    determine_project_subset


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
    m.binary_maintenance_hours_per_period = Param(m.BINARY_MAINTENANCE_PROJECTS)
    m.binary_maintenance_hours_per_event = Param(m.BINARY_MAINTENANCE_PROJECTS)

    # Variables
    m.Down_for_Maintenance_Binary = Var(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )
    m.Start_Maintenance_Binary = Var(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )
    m.Stop_Maintenance_Binary = Var(
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
        binary_maintenance_hours_per_period in each period.
        TODO: it's possible that solve time will be faster if we make this
            constraint >= instead of ==, but then degeneracy could be an issue
        """
        return sum(mod.Down_for_Maintenance_Binary[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   ) \
            == mod.binary_maintenance_hours_per_period[g]

    m.Total_Scheduled_Maintenance_Per_Period_Binary_Constraint = Constraint(
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
        and Start_Maintenance_Binary must be set to 1. If the generator is not
        down for maintenance in the current timepoint and was down for
        maintenance in the previous timepoint, then the RHS is -1 and
        Stop_Maintenance_Binary must be set to 1.
        """
        # TODO: refactor skipping of constraint in first timepoint of linear
        #  horizons
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp,
                                             mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Start_Maintenance_Binary[g, tmp] \
                - mod.Stop_Maintenance_Binary[g, tmp] \
                == mod.Down_for_Maintenance_Binary[g, tmp] \
                - mod.Down_for_Maintenance_Binary[
                       g, mod.previous_timepoint[tmp,
                                                 mod.balancing_type_project[g]]
                   ]

    m.Maintenance_Start_and_Stop_Binary_Constraint = Constraint(
        m.BINARY_MAINTENANCE_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=maintenance_start_and_stop_rule
    )

    def maintenance_event_duration_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        If maintenance was started within binary_maintenance_hours_per_event from the
        current timepoint, it could not have also been stopped during that
        time, i.e. the generator could not have changed its down for
        maintenance status and must still be down for maintenance in the
        current timepoint.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.binary_maintenance_hours_per_event[g]
        )
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        return sum(
            mod.Start_Maintenance_Binary[g, tp] 
            + mod.Stop_Maintenance_Binary[g, tp]
            for tp in relevant_tmps
        ) <= 1

    m.Maintenance_Event_Duration_Binary_Constraint = Constraint(
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
    return 1 - mod.Down_for_Maintenance_Binary[g, tmp]


def load_module_specific_data(
        m, data_portal, scenario_directory, subproblem, stage
):
    """
    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Figure out which projects have this maintenance type
    project_subset = determine_project_subset(
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage, column="maintenance_type",
        type="binary_maintenance"
    )

    data_portal.data()["BINARY_MAINTENANCE_PROJECTS"] = \
        {None: project_subset}

    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "project_availability_endogenous.tab"),
        index=m.BINARY_MAINTENANCE_PROJECTS,
        param=(m.binary_maintenance_hours_per_period,
               m.binary_maintenance_hours_per_event)
    )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """

    # Get project availability if project_availability_scenario_id is not NUL
    c = conn.cursor()
    maintenance_params = c.execute("""
        SELECT project, maintenance_hours_per_period,
        maintenance_hours_per_event
        FROM inputs_project_availability_endogenous
        INNER JOIN inputs_project_portfolios
        USING (project)
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        WHERE project_portfolio_scenario_id = {}
        AND project_availability_scenario_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID,
        )
    )

    return maintenance_params


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage,
                       conn):
    """

    :param inputs_directory:
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """

    endogenous_availability_params = get_inputs_from_database(
        subscenarios=subscenarios, subproblem=subproblem, stage=stage,
        conn=conn
    )
    with open(os.path.join(inputs_directory,
                           "project_availability_endogenous.tab"),
              "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "maintenance_hours_per_period",
             "maintenance_hours_per_event"]
        )

        for row in endogenous_availability_params:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
