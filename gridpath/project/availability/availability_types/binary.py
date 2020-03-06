#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
*Projects* assigned this availability type have binary decision variables
for their availability in each timepoint. This type can be useful in
optimizing planned outage schedules. A *project* of this type is constrained
to be unavailable for at least a pre-specified number of hours in each
*period*. In addition, each unavailability event can be constrained to be
within a minimum and maximum number of hours, and constraints can also be
implemented on the minimum and maximum duration between unavailability events.

"""

import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, Binary, value, \
    NonNegativeReals

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints
from gridpath.project.common_functions import determine_project_subset,\
    check_if_linear_horizon_first_timepoint


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`AVL_BIN`                                                       |
    |                                                                         |
    | The set of projects of the :code:`binary` availability type.            |
    +-------------------------------------------------------------------------+
    | | :code:`AVL_BIN_OPR_PRDS`                                              |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`binary` availability    |
    | type and their operational periods.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`AVL_BIN_OPR_TMPS`                                              |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`binary` availability    |
    | type and their operational timepoints.                                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`avl_bin_unavl_hrs_per_prd`                                     |
    | | *Defined over*: :code:`AVL_BIN`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The number of hours the project must be unavailable per period.         |
    +-------------------------------------------------------------------------+
    | | :code:`avl_bin_min_unavl_hrs_per_event`                               |
    | | *Defined over*: :code:`AVL_BIN`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum number of hours an unavailability event should last for.    |
    +-------------------------------------------------------------------------+
    | | :code:`avl_bin_max_unavl_hrs_per_event`                               |
    | | *Defined over*: :code:`AVL_BIN`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The maximum number of hours an unavailability event can last for.       |
    +-------------------------------------------------------------------------+
    | | :code:`avl_bin_min_avl_hrs_between_events`                            |
    | | *Defined over*: :code:`AVL_BIN`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum number of hours a project should be available between       |
    | unavailability events.                                                  |
    +-------------------------------------------------------------------------+
    | | :code:`avl_bin_max_avl_hrs_between_events`                            |
    | | *Defined over*: :code:`AVL_BIN`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The maximum number of hours a project can be available between          |
    | unavailability events.                                                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`AvlBin_Unavailable`                                            |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    | | *Within*: :code:`Binary`                                              |
    |                                                                         |
    | Binary decision variable that specifies whether the project is          |
    | unavailable or not in each operational timepoint (1=unavailable).       |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Start_Unavailability`                                   |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    | | *Within*: :code:`Binary`                                              |
    |                                                                         |
    | Binary decision variable that designates the start of an unavailability |
    | event (when the project goes from available to unavailable.             |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Stop_Unavailability`                                    |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    | | *Within*: :code:`Binary`                                              |
    |                                                                         |
    | Binary decision variable that designates the end of an unavailability   |
    | event (when the project goes from unavailable to available.             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`AvlBin_Tot_Sched_Unavl_per_Prd_Constraint`                     |
    | | *Defined over*: :code:`AVL_BIN_OPR_PRDS`                              |
    |                                                                         |
    | The project must be unavailable for :code:`avl_bin_unavl_hrs_per_prd`   |
    | hours in each period.                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Unavl_Start_and_Stop_Constraint`                        |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    |                                                                         |
    | Link the three binary variables in each timepoint such that             |
    | :code:`AvlBin_Start_Unavailability` is 1 if the project goes from       |
    | available to unavailable, and :code:`AvlBin_Stop_Unavailability` is 1   |
    | if the project goes from unavailable to available.                      |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Min_Event_Duration_Constraint`                          |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    |                                                                         |
    | The duration of each unavailability event should be larger than or      |
    | equal to :code:`avl_bin_min_unavl_hrs_per_event` hours.                 |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Max_Event_Duration_Constraint`                          |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    |                                                                         |
    | The duration of each unavailability event should be smaller than or     |
    | equal to :code:`avl_bin_max_unavl_hrs_per_event` hours.                 |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Min_Time_Between_Events_Constraint`                     |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    |                                                                         |
    | The time between unavailability events should be larger than or equal   |
    | to :code:`avl_bin_min_avl_hrs_between_events` hours.                    |
    +-------------------------------------------------------------------------+
    | | :code:`AvlBin_Max_Time_Between_Events_Constraint`                     |
    | | *Defined over*: :code:`AVL_BIN_OPR_TMPS`                              |
    |                                                                         |
    | The time between unavailability events should be smaller than or equal  |
    | to :code:`avl_bin_max_avl_hrs_between_events` hours.                    |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.AVL_BIN = Set(within=m.PROJECTS)

    m.AVL_BIN_OPR_PRDS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_PERIODS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_PERIODS
            if g in mod.AVL_BIN)
    )

    # TODO: factor out this lambda rule, as it is used in all operational type
    #  modules and availability type modules
    m.AVL_BIN_OPR_TMPS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.AVL_BIN)
    )

    # Required Input Params
    ###########################################################################

    m.avl_bin_unavl_hrs_per_prd = Param(
        m.AVL_BIN, within=NonNegativeReals
    )

    m.avl_bin_min_unavl_hrs_per_event = Param(
        m.AVL_BIN, within=NonNegativeReals
    )

    m.avl_bin_max_unavl_hrs_per_event = Param(
        m.AVL_BIN, within=NonNegativeReals
    )

    m.avl_bin_min_avl_hrs_between_events = Param(
        m.AVL_BIN, within=NonNegativeReals
    )

    m.avl_bin_max_avl_hrs_between_events = Param(
        m.AVL_BIN, within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.AvlBin_Unavailable = Var(
        m.AVL_BIN_OPR_TMPS,
        within=Binary
    )

    m.AvlBin_Start_Unavailability = Var(
        m.AVL_BIN_OPR_TMPS,
        within=Binary
    )

    m.AvlBin_Stop_Unavailability = Var(
        m.AVL_BIN_OPR_TMPS,
        within=Binary
    )

    # Constraints
    ###########################################################################

    m.AvlBin_Tot_Sched_Unavl_per_Prd_Constraint = Constraint(
        m.AVL_BIN_OPR_PRDS,
        rule=total_scheduled_availability_per_period_rule
    )

    m.AvlBin_Unavl_Start_and_Stop_Constraint = Constraint(
        m.AVL_BIN_OPR_TMPS,
        rule=unavailability_start_and_stop_rule
    )

    m.AvlBin_Min_Event_Duration_Constraint = Constraint(
        m.AVL_BIN_OPR_TMPS,
        rule=event_min_duration_rule
    )

    m.AvlBin_Max_Event_Duration_Constraint = Constraint(
        m.AVL_BIN_OPR_TMPS,
        rule=event_max_duration_rule
    )

    m.AvlBin_Min_Time_Between_Events_Constraint = Constraint(
        m.AVL_BIN_OPR_TMPS,
        rule=min_time_between_events_rule
    )

    m.AvlBin_Max_Time_Between_Events_Constraint = Constraint(
        m.AVL_BIN_OPR_TMPS,
        rule=max_time_between_events_rule
    )


# Constraint Formulation Rules
###############################################################################

def total_scheduled_availability_per_period_rule(mod, g, p):
    """
    **Constraint Name**: AvlBin_Tot_Sched_Unavl_per_Prd_Constraint
    **Enforced Over**: AVL_BIN_OPR_PRDS

    The project must be down for avl_bin_unavl_hrs_per_prd in each period.
    TODO: it's possible that solve time will be faster if we make this
        constraint >= instead of ==, but then degeneracy could be an issue
    """
    return sum(
        mod.AvlBin_Unavailable[g, tmp]
        * mod.number_of_hours_in_timepoint[tmp]
        for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
    ) == mod.avl_bin_unavl_hrs_per_prd[g]


def unavailability_start_and_stop_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlBin_Unavl_Start_and_Stop_Constraint
    **Enforced Over**: AVL_BIN_OPR_TMPS

    Constrain the start and stop availability variables based on the
    availability status in the current and previous timepoint. If the
    project is down in the current timepoint and was not down in the
    previous timepoint, then the RHS is 1 and AvlBin_Start_Unavailability
    must be set to 1. If the project is not down in the current
    timepoint and was down in the previous timepoint, then the RHS is -1
    and AvlBin_Stop_Unavailability must be set to 1.
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return mod.AvlBin_Start_Unavailability[g, tmp] \
            - mod.AvlBin_Stop_Unavailability[g, tmp] \
            == mod.AvlBin_Unavailable[g, tmp] \
            - mod.AvlBin_Unavailable[g, mod.previous_timepoint[
                tmp, mod.balancing_type_project[g]]]


def event_min_duration_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlBin_Min_Event_Duration_Constraint
    **Enforced Over**: AVL_BIN_OPR_TMPS

    If a project became unavailable within avl_bin_min_unavl_hrs_per_event
    from the current timepoint, it must still be unavailable in the current
    timepoint.
    """
    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.avl_bin_min_unavl_hrs_per_event[g]
    )
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    return sum(
        mod.AvlBin_Start_Unavailability[g, tp]
        for tp in relevant_tmps
    ) <= mod.AvlBin_Unavailable[g, tmp]


def event_max_duration_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlBin_Max_Event_Duration_Constraint
    **Enforced Over**: AVL_BIN_OPR_TMPS

    If a project became unavailable within avl_bin_max_unavl_hrs_per_event
    from the current timepoint, it must have also been brought back to
    availability during that time.
    """
    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.avl_bin_max_unavl_hrs_per_event[g]
    )
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    return sum(
        (mod.AvlBin_Start_Unavailability[g, tp]
         - mod.AvlBin_Stop_Unavailability[g, tp])
        for tp in relevant_tmps
    ) <= 0


def min_time_between_events_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlBin_Min_Time_Between_Events_Constraint
    **Enforced Over**: AVL_BIN_OPR_TMPS

    If a project became available within avl_bin_min_avl_hrs_between_events
    from the current timepoint, it must still be available in the current
    timepoint.
    """
    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.avl_bin_min_avl_hrs_between_events[g]
    )
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    return sum(
        mod.AvlBin_Stop_Unavailability[g, tp]
        for tp in relevant_tmps
    ) <= 1 - mod.AvlBin_Unavailable[g, tmp]


def max_time_between_events_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlBin_Max_Time_Between_Events_Constraint
    **Enforced Over**: AVL_BIN_OPR_TMPS

    If a project became available within avl_bin_max_avl_hrs_between_events
    from the current timepoint, it must have also been made unavailable
    again during that time.
    """
    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.avl_bin_max_avl_hrs_between_events[g]
    )
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    return sum(
        (mod.AvlBin_Stop_Unavailability[g, tp] -
         mod.AvlBin_Start_Unavailability[g, tp])
        for tp in relevant_tmps
    ) <= 0


# Availability Type Methods
###############################################################################

def availability_derate_rule(mod, g, tmp):
    """
    """
    return 1 - mod.AvlBin_Unavailable[g, tmp]


# Input-Output
###############################################################################

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

    data_portal.data()["AVL_BIN"] = {None: project_subset}

    avl_bin_unavl_hrs_per_prd_dict = {}
    avl_bin_min_unavl_hrs_per_event_dict = {}
    avl_bin_max_unavl_hrs_per_event_dict = {}
    avl_bin_min_avl_hrs_between_events_dict = {}
    avl_bin_max_avl_hrs_between_events_dict = {}

    with open(os.path.join(scenario_directory, subproblem, stage,
                           "inputs", "project_availability_endogenous.tab"),
              "r") as f:
        reader = csv.reader(f, delimiter="\t", lineterminator="\n")
        next(reader)

        for row in reader:
            if row[0] in project_subset:
                avl_bin_unavl_hrs_per_prd_dict[row[0]] = float(row[1])
                avl_bin_min_unavl_hrs_per_event_dict[row[0]] = float(row[2])
                avl_bin_max_unavl_hrs_per_event_dict[row[0]] = float(row[3])
                avl_bin_min_avl_hrs_between_events_dict[row[0]] = float(row[4])
                avl_bin_max_avl_hrs_between_events_dict[row[0]] = float(row[5])

    data_portal.data()["avl_bin_unavl_hrs_per_prd"] = \
        avl_bin_unavl_hrs_per_prd_dict
    data_portal.data()["avl_bin_min_unavl_hrs_per_event"] = \
        avl_bin_min_unavl_hrs_per_event_dict
    data_portal.data()["avl_bin_max_unavl_hrs_per_event"] = \
        avl_bin_max_unavl_hrs_per_event_dict
    data_portal.data()["avl_bin_min_avl_hrs_between_events"] = \
        avl_bin_min_avl_hrs_between_events_dict
    data_portal.data()["avl_bin_max_avl_hrs_between_events"] = \
        avl_bin_max_avl_hrs_between_events_dict


def export_module_specific_results(
        scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m: The Pyomo abstract model
    :param d: Dynamic components
    :return: Nothing
    """

    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "project_availability_endogenous.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "timepoint_weight", "number_of_hours_in_timepoint",
                         "load_zone", "technology",
                         "unavailability_decision", "start_unavailability",
                         "stop_unavailability", "availability_derate"])
        for (p, tmp) in m.AVL_BIN_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.AvlBin_Unavailable[p, tmp]),
                value(m.AvlBin_Start_Unavailability[p, tmp]),
                value(m.AvlBin_Stop_Unavailability[p, tmp]),
                1-value(m.AvlBin_Unavailable[p, tmp])
            ])


# Database
###############################################################################

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
        inputs_directory, subscenarios, subproblem, stage, conn
):
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
        inputs_directory, "project_availability_endogenous.tab"
    )

    if not os.path.exists(availability_file):
        with open(availability_file, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            # Write header
            writer.writerow(
                ["project",
                 "unavailable_hours_per_period",
                 "unavailable_hours_per_event_min",
                 "unavailable_hours_per_event_max",
                 "available_hours_between_events_min",
                 "available_hours_between_events_max"]
            )

    with open(availability_file, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        # Write rows
        for row in endogenous_availability_params:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    if not quiet:
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
                           "project_availability_endogenous.csv"),
              "r") as dispatch_file:
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
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate
        FROM temp_results_project_availability_endogenous{}
        ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

# TODO: add validation
