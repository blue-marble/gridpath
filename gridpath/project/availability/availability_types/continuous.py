#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
This *availability type* is formulated like the *binary* type except that
all binary decision variables are relaxed to be continuous with bounds
between 0 and 1. This can be useful to address computational difficulties
when modeling endogenous *project* availabilities.

"""

import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, PercentFraction, \
    value, NonNegativeReals

from gridpath.project.availability.availability_types.common_functions import \
    insert_availability_results
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints
from gridpath.project.common_functions import determine_project_subset, \
    check_if_boundary_type_and_first_timepoint


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`AVL_CONT`                                                      |
    |                                                                         |
    | The set of projects of the :code:`continuous` availability type.        |
    +-------------------------------------------------------------------------+
    | | :code:`AVL_CONT_OPR_PRDS`                                             |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`continuous` availability|
    | type and their operational periods.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`AVL_CONT_OPR_TMPS`                                             |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`continuous` availability|
    | type and their operational timepoints.                                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`avl_cont_unavl_hrs_per_prd`                                    |
    | | *Defined over*: :code:`AVL_CONT`                                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The number of hours the project must be unavailable per period.         |
    +-------------------------------------------------------------------------+
    | | :code:`avl_cont_min_unavl_hrs_per_event`                              |
    | | *Defined over*: :code:`AVL_CONT`                                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum number of hours an unavailability event should last for.    |
    +-------------------------------------------------------------------------+
    | | :code:`avl_cont_min_avl_hrs_between_events`                           |
    | | *Defined over*: :code:`AVL_CONT`                                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum number of hours a project should be available between       |
    | unavailability events.                                                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`AvlCont_Unavailable`                                           |
    | | *Defined over*: :code:`AVL_CONT_OPR_TMPS`                             |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | Continuous decision variable that specifies whteher the project is      |
    | unavailable or not in each operational timepoint (1=unavailable).       |
    +-------------------------------------------------------------------------+
    | | :code:`AvlCont_Start_Unavailability`                                  |
    | | *Defined over*: :code:`AVL_CONT_OPR_TMPS`                             |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | Continuous decision variable that designates the start of an            |
    | unavailability event (when the project goes from available to           |
    | unavailable.                                                            |
    +-------------------------------------------------------------------------+
    | | :code:`AvlCont_Stop_Unavailability`                                   |
    | | *Defined over*: :code:`AVL_CONT_OPR_TMPS`                             |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | Continuous decision variable that designates the end of an              |
    | unavailability event (when the project goes from unavailable to         |
    | available.                                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`AvlCont_Tot_Sched_Unavl_per_Prd_Constraint`                    |
    | | *Defined over*: :code:`AVL_CONT_OPR_PRDS`                             |
    |                                                                         |
    | The project must be unavailable for :code:`avl_cont_unavl_hrs_per_prd`  |
    | hours in each period.                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`AvlCont_Unavl_Start_and_Stop_Constraint`                       |
    | | *Defined over*: :code:`AVL_CONT_OPR_TMPS`                             |
    |                                                                         |
    | Link the three continuous variables in each timepoint such that         |
    | :code:`AvlCont_Start_Unavailability` is 1 if the project goes from      |
    | available to unavailable, and :code:`AvlCont_Stop_Unavailability` is 1  |
    | if the project goes from unavailable to available.                      |
    +-------------------------------------------------------------------------+
    | | :code:`AvlCont_Min_Event_Duration_Constraint`                         |
    | | *Defined over*: :code:`AVL_CONT_OPR_TMPS`                             |
    |                                                                         |
    | The duration of each unavailability event should be larger than or      |
    | equal to :code:`avl_cont_min_unavl_hrs_per_event` hours.                |
    +-------------------------------------------------------------------------+
    | | :code:`AvlCont_Min_Time_Between_Events_Constraint`                    |
    | | *Defined over*: :code:`AVL_CONT_OPR_TMPS`                             |
    |                                                                         |
    | The time between unavailability events should be larger than or equal   |
    | to :code:`avl_cont_min_avl_hrs_between_events` hours.                   |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.AVL_CONT = Set(within=m.PROJECTS)

    m.AVL_CONT_OPR_PRDS = Set(
        dimen=2, within=m.PRJ_OPR_PRDS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_PRDS
            if g in mod.AVL_CONT)
    )

    # TODO: factor out this lambda rule, as it is used in all operational type
    #  modules and availability type modules
    m.AVL_CONT_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.AVL_CONT)
    )

    # Required Input Params
    ###########################################################################

    m.avl_cont_unavl_hrs_per_prd = Param(
        m.AVL_CONT, within=NonNegativeReals
    )

    m.avl_cont_min_unavl_hrs_per_event = Param(
        m.AVL_CONT, within=NonNegativeReals
    )

    m.avl_cont_min_avl_hrs_between_events = Param(
        m.AVL_CONT, within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.AvlCont_Unavailable = Var(
        m.AVL_CONT_OPR_TMPS,
        within=PercentFraction
    )

    m.AvlCont_Start_Unavailability = Var(
        m.AVL_CONT_OPR_TMPS,
        within=PercentFraction
    )

    m.AvlCont_Stop_Unavailability = Var(
        m.AVL_CONT_OPR_TMPS,
        within=PercentFraction
    )

    # Constraints
    ###########################################################################

    m.AvlCont_Tot_Sched_Unavl_per_Prd_Constraint = Constraint(
        m.AVL_CONT_OPR_PRDS,
        rule=total_scheduled_availability_per_period_rule
    )

    m.AvlCont_Unavl_Start_and_Stop_Constraint = Constraint(
        m.AVL_CONT_OPR_TMPS,
        rule=unavailability_start_and_stop_rule
    )

    m.AvlCont_Min_Event_Duration_Constraint = Constraint(
        m.AVL_CONT_OPR_TMPS,
        rule=event_min_duration_rule
    )

    m.AvlCont_Min_Time_Between_Events_Constraint = Constraint(
        m.AVL_CONT_OPR_TMPS,
        rule=min_time_between_events_rule
    )


# Constraint Formulation Rules
###############################################################################

def total_scheduled_availability_per_period_rule(mod, g, p):
    """
    **Constraint Name**: AvlCont_Tot_Sched_Unavl_per_Prd_Constraint
    **Enforced Over**: AVL_CONT_OPR_PRDS

    The project must be down for avl_cont_unavl_hrs_per_prd in each period.
    TODO: it's possible that solve time will be faster if we make this
        constraint >= instead of ==, but then degeneracy could be an issue
    """
    return sum(
        mod.AvlCont_Unavailable[g, tmp]
        * mod.hrs_in_tmp[tmp]
        for tmp in mod.TMPS_IN_PRD[p]
    ) == mod.avl_cont_unavl_hrs_per_prd[g]


def unavailability_start_and_stop_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlCont_Unavl_Start_and_Stop_Constraint
    **Enforced Over**: AVL_CONT_OPR_TMPS

    Constrain the start and stop availability variables based on the
    availability status in the current and previous timepoint. If the
    project is down in the current timepoint and was not down in the
    previous timepoint, then the RHS is 1 and AvlCont_Start_Unavailability
    must be set to 1. If the project is not down in the current
    timepoint and was down in the previous timepoint, then the RHS is -1
    and AvlCont_Stop_Unavailability must be set to 1.
    """
    if check_if_boundary_type_and_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        return Constraint.Skip
    else:
        return mod.AvlCont_Start_Unavailability[g, tmp] \
            - mod.AvlCont_Stop_Unavailability[g, tmp] \
            == mod.AvlCont_Unavailable[g, tmp] \
            - mod.AvlCont_Unavailable[g, mod.prev_tmp[
                tmp, mod.balancing_type_project[g]]]


def event_min_duration_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlCont_Min_Event_Duration_Constraint
    **Enforced Over**: AVL_CONT_OPR_TMPS

    If a project became unavailable within avl_cont_min_unavl_hrs_per_event
    from the current timepoint, it must still be unavailable in the current
    timepoint.
    """
    relevant_tmps, _ = determine_relevant_timepoints(
        mod, g, tmp, mod.avl_cont_min_unavl_hrs_per_event[g]
    )
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    return sum(
        mod.AvlCont_Start_Unavailability[g, tp]
        for tp in relevant_tmps
    ) <= mod.AvlCont_Unavailable[g, tmp]


def min_time_between_events_rule(mod, g, tmp):
    """
    **Constraint Name**: AvlCont_Min_Time_Between_Events_Constraint
    **Enforced Over**: AVL_CONT_OPR_TMPS

    If a project became available within avl_cont_min_avl_hrs_between_events
    from the current timepoint, it must still be available in the current
    timepoint.
    """
    relevant_tmps, _ = determine_relevant_timepoints(
        mod, g, tmp, mod.avl_cont_min_avl_hrs_between_events[g]
    )
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    return sum(
        mod.AvlCont_Stop_Unavailability[g, tp]
        for tp in relevant_tmps
    ) <= 1 - mod.AvlCont_Unavailable[g, tmp]


# Availability Type Methods
###############################################################################

def availability_derate_rule(mod, g, tmp):
    """
    """
    return 1 - mod.AvlCont_Unavailable[g, tmp]


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
        type="continuous"
    )

    data_portal.data()["AVL_CONT"] = {None: project_subset}

    avl_cont_unavl_hrs_per_prd_dict = {}
    avl_cont_min_unavl_hrs_per_event_dict = {}
    avl_cont_min_avl_hrs_between_events_dict = {}

    with open(os.path.join(scenario_directory, str(subproblem), str(stage),
                           "inputs", "project_availability_endogenous.tab"),
              "r") as f:
        reader = csv.reader(f, delimiter="\t", lineterminator="\n")
        next(reader)

        for row in reader:
            if row[0] in project_subset:
                avl_cont_unavl_hrs_per_prd_dict[row[0]] = float(row[1])
                avl_cont_min_unavl_hrs_per_event_dict[row[0]] = float(row[2])
                avl_cont_min_avl_hrs_between_events_dict[row[0]] = float(
                    row[3])

    data_portal.data()["avl_cont_unavl_hrs_per_prd"] = \
        avl_cont_unavl_hrs_per_prd_dict
    data_portal.data()["avl_cont_min_unavl_hrs_per_event"] = \
        avl_cont_min_unavl_hrs_per_event_dict
    data_portal.data()["avl_cont_min_avl_hrs_between_events"] = \
        avl_cont_min_avl_hrs_between_events_dict


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

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "project_availability_endogenous_continuous.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "subproblem_id", "stage_id",
                         "availability_type", "timepoint",
                         "timepoint_weight", "number_of_hours_in_timepoint",
                         "load_zone", "technology",
                         "unavailability_decision", "start_unavailability",
                         "stop_unavailability", "availability_derate"])
        for (p, tmp) in m.AVL_CONT_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                1 if subproblem == "" else subproblem,
                1 if stage == "" else stage,
                m.availability_type[p],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.AvlCont_Unavailable[p, tmp]),
                value(m.AvlCont_Start_Unavailability[p, tmp]),
                value(m.AvlCont_Stop_Unavailability[p, tmp]),
                1-value(m.AvlCont_Unavailable[p, tmp])
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
            unavailable_hours_per_event_min,
            available_hours_between_events_min
            FROM (
            SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
            ) as portfolio_tbl
            INNER JOIN (
                SELECT project, endogenous_availability_scenario_id
                FROM inputs_project_availability
                WHERE project_availability_scenario_id = {}
                AND availability_type = 'continuous'
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
        scenario_directory, subscenarios, subproblem, stage, conn
):
    """

    :param scenario_directory:
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
        scenario_directory, subproblem, stage,
        "project_availability_endogenous.tab"
    )

    if not os.path.exists(availability_file):
        with open(availability_file, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            # Write header
            writer.writerow(
                ["project",
                 "unavailable_hours_per_period",
                 "unavailable_hours_per_event_min",
                 "available_hours_between_events_min"]
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
        print("project availability continuous")

    insert_availability_results(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id,
        results_file="project_availability_endogenous_continuous.csv"
    )

# TODO: add validation
