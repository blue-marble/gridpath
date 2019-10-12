#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Projects with timepoint-level, binary availability decision variables.
"""

import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, Binary, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints
from gridpath.project.common_functions import determine_project_subset


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Sets
    m.BINARY_AVAILABILITY_PROJECTS = Set(within=m.PROJECTS)
    m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_PERIODS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_PERIODS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_PERIODS
            if g in mod.BINARY_AVAILABILITY_PROJECTS
            )
    )
    # TODO: factor out this lambda rule, as it is used in all operational type
    #  modules and availability type modules
    m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.BINARY_AVAILABILITY_PROJECTS
            )
    )

    # Params
    m.unavailable_hours_per_period_binary = Param(
        m.BINARY_AVAILABILITY_PROJECTS
    )
    m.unavailable_hours_per_event_min_binary = Param(
        m.BINARY_AVAILABILITY_PROJECTS
    )
    m.unavailable_hours_per_event_max_binary = Param(
        m.BINARY_AVAILABILITY_PROJECTS
    )
    m.available_hours_between_events_min_binary = Param(
        m.BINARY_AVAILABILITY_PROJECTS
    )
    m.available_hours_between_events_max_binary = Param(
        m.BINARY_AVAILABILITY_PROJECTS
    )

    # Variables
    m.Unavailable_Binary = Var(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )
    m.Start_Unavailability_Binary = Var(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )
    m.Stop_Unavailability_Binary = Var(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS, within=Binary
    )

    # Constraints
    def total_scheduled_availability_per_period_rule(mod, g, p):
        """
        :param mod:
        :param g:
        :param p:
        :return:

        The generator must be down for
        unavailable_hours_per_period_binary in each period.
        TODO: it's possible that solve time will be faster if we make this
            constraint >= instead of ==, but then degeneracy could be an issue
        """
        return sum(mod.Unavailable_Binary[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   ) \
            == mod.unavailable_hours_per_period_binary[g]

    m.Total_Scheduled_Availability_Per_Period_Binary_Constraint = Constraint(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_PERIODS,
        rule=total_scheduled_availability_per_period_rule
    )

    def availability_start_and_stop_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        Constrain the start and stop availability variables based on the
        availability status in the current and previous timepoint. If the
        generator is down in the current timepoint and was not down in the
        previous timepoint, then the RHS is 1 and Start_Unavailability_Binary
        must be set to 1. If the generator is not down in the current
        timepoint and was down in the previous timepoint, then the RHS is -1
        and Stop_Unavailability_Binary must be set to 1.
        """
        # TODO: refactor skipping of constraint in first timepoint of linear
        #  horizons, as we do it a lot
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp,
                                             mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Start_Unavailability_Binary[g, tmp] \
                - mod.Stop_Unavailability_Binary[g, tmp] \
                == mod.Unavailable_Binary[g, tmp] \
                - mod.Unavailable_Binary[
                       g, mod.previous_timepoint[tmp,
                                                 mod.balancing_type_project[g]]
                   ]

    m.Availability_Start_and_Stop_Binary_Constraint = Constraint(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=availability_start_and_stop_rule
    )

    def availability_event_min_duration_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        If a generator became unavailable within
        unavailable_hours_per_event_min_binary from the current timepoint,
        it must still be unavailable in the current timepoint.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.unavailable_hours_per_event_min_binary[g]
        )
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        return sum(mod.Start_Unavailability_Binary[g, tp]
                   for tp in relevant_tmps) \
            <= mod.Unavailable_Binary[g, tmp]

    m.Availability_Event_Min_Duration_Binary_Constraint = Constraint(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=availability_event_min_duration_rule
    )

    def availability_event_max_duration_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        If a generator became unavailable within
        max_unavailable_hours_per_event_min_binary from the current timepoint,
        it must have also been brought back to availability during that time.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.unavailable_hours_per_event_max_binary[g]
        )
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        return sum(
            (mod.Start_Unavailability_Binary[g, tp] -
             mod.Stop_Unavailability_Binary[g, tp])
            for tp in relevant_tmps
        ) <= 0

    m.Availability_Event_Max_Duration_Binary_Constraint = Constraint(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=availability_event_max_duration_rule
    )

    def min_time_between_availability_events_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        If a generator became available within
        unavailable_hours_per_event_min_binary from the current timepoint, 
        it must still be available in the current timepoint.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.available_hours_between_events_min_binary[g]
        )
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        return sum(mod.Stop_Unavailability_Binary[g, tp]
                   for tp in relevant_tmps) \
            <= 1 - mod.Unavailable_Binary[g, tmp]

    m.Min_Time_Between_Availability_Events_Binary_Constraint = Constraint(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=min_time_between_availability_events_rule
    )

    def max_time_between_availability_events_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:

        If a generator became available within
        available_hours_between_events_min_binary from the current timepoint,
        it must have also been brought back to down during that time.
        """
        relevant_tmps = determine_relevant_timepoints(
            mod, g, tmp, mod.available_hours_between_events_min_binary[g]
        )
        if relevant_tmps == [tmp]:
            return Constraint.Skip
        return sum(
            (mod.Stop_Unavailability_Binary[g, tp] -
             mod.Start_Unavailability_Binary[g, tp])
            for tp in relevant_tmps
        ) <= 0

    m.Max_Time_Between_Availability_Events_Binary_Constraint = Constraint(
        m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS,
        rule=max_time_between_availability_events_rule
    )


def availability_derate_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 1 - mod.Unavailable_Binary[g, tmp]


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
    # Figure out which projects have this availability type
    project_subset = determine_project_subset(
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage, column="availability_type",
        type="binary"
    )

    data_portal.data()["BINARY_AVAILABILITY_PROJECTS"] = \
        {None: project_subset}

    unavailable_hours_per_period_binary_dict = {}
    unavailable_hours_per_event_min_binary_dict = {}
    unavailable_hours_per_event_max_binary_dict = {}
    available_hours_between_events_min_binary_dict = {}
    available_hours_between_events_max_binary_dict = {}

    with open(os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "project_availability_endogenous.tab"),
              "r") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)

        for row in reader:
            if row[0] in project_subset:
                unavailable_hours_per_period_binary_dict[row[0]] = \
                    float(row[1])
                unavailable_hours_per_event_min_binary_dict[row[0]] = \
                    float(row[2])
                unavailable_hours_per_event_max_binary_dict[row[0]] = \
                    float(row[3])
                available_hours_between_events_min_binary_dict[row[0]] = \
                    float(row[4])
                available_hours_between_events_max_binary_dict[row[0]] = \
                    float(row[5])

    data_portal.data()["unavailable_hours_per_period_binary"] = \
        unavailable_hours_per_period_binary_dict
    data_portal.data()["unavailable_hours_per_event_min_binary"] = \
        unavailable_hours_per_event_min_binary_dict
    data_portal.data()["unavailable_hours_per_event_max_binary"] = \
        unavailable_hours_per_event_max_binary_dict
    data_portal.data()["available_hours_between_events_min_binary"] = \
        available_hours_between_events_min_binary_dict
    data_portal.data()["available_hours_between_events_max_binary"] = \
        available_hours_between_events_max_binary_dict


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
    availability_params = c.execute("""
            SELECT project, unavailable_hours_per_period, 
            unavailable_hours_per_event_min, unavailable_hours_per_event_max,
            available_hours_between_events_min, 
            available_hours_between_events_max
            FROM (
            SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
            ) as portfolio_tbl
            INNER JOIN (
                SELECT project, endogenous_availability_scenario_id
                FROM inputs_project_availability_types
                WHERE project_availability_scenario_id = {}
                AND availability_type = 'binary'
                AND endogenous_availability_scenario_id IS NOT NULL
                ) AS avail_char
             USING (project)
            LEFT OUTER JOIN
            inputs_project_availability_endogenous
            USING (endogenous_availability_scenario_id, project);
            """.format(
        subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID
        )
    )

    return availability_params


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn):
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

    # Check if project_availability_endogenous.tab exists; only write header
    # if the file wasn't already created
    availability_file = os.path.join(
        inputs_directory, subproblem, stage, "inputs",
        "project_availability_endogenous.tab"
    )

    if not os.path.exists(availability_file):
        with open(availability_file, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            # Write header
            writer.writerow(
                ["project", "unavailable_hours_per_period",
                 "unavailable_hours_per_event"]
            )

    with open(availability_file, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        # Write rows
        for row in endogenous_availability_params:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def export_module_specific_results(
        scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """

    # First power
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "project_availability_endogenous.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "timepoint_weight", "number_of_hours_in_timepoint",
                         "load_zone", "technology",
                         "unavailability_decision", "start_unavailability",
                         "stop_unavailability", "availability_derate"])
        for (p, tmp) in m.BINARY_AVAILABILITY_PROJECTS_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Unavailable_Binary[p, tmp]),
                value(m.Start_Unavailability_Binary[p, tmp]),
                value(m.Stop_Unavailability_Binary[p, tmp]),
                1-value(m.Unavailable_Binary[p, tmp])
            ])


def import_module_specific_results_into_database(
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
    print("project availability")
    # dispatch_all.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_availability_endogenous",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, 
                           "project_availability_endogenous.csv"), "r") as \
            dispatch_file:
        reader = csv.reader(dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            technology = row[7]
            unavailability_decision = row[8]
            start_unavailability = row[9]
            stop_unavailability = row[10]
            availability_derate = row[11]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 load_zone, technology, unavailability_decision,
                 start_unavailability, stop_unavailability,
                 availability_derate)
            )
    insert_temp_sql = """
        INSERT INTO temp_results_project_availability_endogenous{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight,
        number_of_hours_in_timepoint,
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_availability_endogenous
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw
        FROM temp_results_project_availability_endogenous{}
        ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
