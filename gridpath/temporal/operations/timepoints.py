#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
*Timepoints* are the finest resolution over which operational decisions are
made (e.g. an hour). Generator commitment and dispatch decisions are made for
each timepoint, with some constraints applied across timepoints (e.g. ramp
constraints.) Most commonly, a timepoint is an hour, but the resolution is
flexible: a timepoint could also be a 15-minute, 5-minute, 1-minute, or 4-hour
segment. Different timepoint durations can also be mixed, e.g. some can be
5-minute segments and some can be hours.

Timepoints can also be assigned weights in order to represent other
timepoints that are not modeled explicitly (e.g. use a 24-hour period per month
to represent the whole month using the number of days in that month for the
weight of each of the 24 timepoints).

To support multi-stage production simulation timepoints can also be assigned a
mapping to the previous stage (e.g. timepoints 1-12 in the 5-minute real-time
stage map to timepoint 1 in the hour-ahead stage) and a flag whether the
timepoint is part of a spinup or lookahead segment.
Timepoints that are part of a spinup or lookahead segment are included in the
optimization but are generally discarded when calculating result metrics such
as annual emissions, energy, or cost.
"""

import csv
import os.path

from pyomo.environ import Param, Set, NonNegativeReals, NonNegativeIntegers,\
    PositiveIntegers, NonPositiveIntegers, Boolean


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TMPS`                                                          |
    | | *Within*: :code:`PositiveIntegers`                                    |
    |                                                                         |
    | The list of timepoints being modeled; timepoints are ordered and must   |
    | be non-negative integers.                                               |
    +-------------------------------------------------------------------------+
    | | :code:`MONTHS`                                                        |
    | | *Within*: :code:`PositiveIntegers`                                    |
    |                                                                         |
    | The list of months (1-12).                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`hrs_in_tmp`                                                    |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The number of hours in each timepoint (can be a fraction). For example, |
    | a 15-minute timepoint will have 0.25 hours per timepoint whereas a      |
    | 4-hour timepoint will have 4 hours per timepoint. This parameter is     |
    | used by other modules to track energy (e.g. storage state of charge)    |
    | and when evaluation ramp rates. Timepoints do not need to have the      |
    | same  :code:`hrs_in_tmp` value, i.e. one of them can represent a        |
    | 5-minute segment and another a 24-hour segment.                         |
    +-------------------------------------------------------------------------+
    | | :code:`tmp_weight`                                                    |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | This parameter accounts for the number of other similar 'timepoints'    |
    | that are not explicitly included in the optimization, but that the      |
    | included timepoint represents in the objective function. For example,   |
    | we could include one day from the month to represent the entire month,  |
    | in which case the timepoint_weight for each timepoint on that day will  |
    | be the number of the days in the respective month.                      |
    +-------------------------------------------------------------------------+
    | | :code:`prev_stage_tmp_map`                                            |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`NonNegativeIntegers`                                 |
    |                                                                         |
    | The associated timepoint in the previous stage (if there is any) for    |
    | each timepoint. This is used to pass commitment decisions from one      |
    | stage to the next. E.g. if the real-time stage has 15-minute timepoints |
    | , and the hour-ahead stage had hourly timepoints, all 4 real-time       |
    | timepoints within an hour will point to the same hourly timepoint in    |
    | the previous hour-ahead stage to its commitment decision.               |
    +-------------------------------------------------------------------------+
    | | :code:`month`                                                         |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`MONTHS`                                              |
    |                                                                         |
    | The month that each timepoint belongs to. This is used to determine     |
    | fuel costs during that timepoint, among others.                         |
    +-------------------------------------------------------------------------+

    .. TODO:: varying timepoint durations haven't been extensiveliy tested

    """

    # Sets
    ###########################################################################

    m.TMPS = Set(
        within=PositiveIntegers,
        ordered=True
    )

    m.MONTHS = Set(
        within=PositiveIntegers,
        initialize=list(range(1, 12 + 1))
    )

    # These are the timepoints from the previous subproblem for which we'll
    # have parameters to constrain the current subproblem
    m.LINKED_TMPS = Set(
        within=NonPositiveIntegers
    )

    # Required Params
    ###########################################################################

    m.hrs_in_tmp = Param(
        m.TMPS,
        within=NonNegativeReals
    )

    m.tmp_weight = Param(
        m.TMPS,
        within=NonNegativeReals
    )

    m.prev_stage_tmp_map = Param(
        m.TMPS,
        within=NonNegativeIntegers
    )

    m.link_to_next_subproblem = Param(
        m.TMPS, default=0,
        within=Boolean
    )

    m.month = Param(
        m.TMPS,
        within=m.MONTHS
    )

    m.hrs_in_linked_tmp = Param(
        m.TMPS,
        within=NonNegativeReals
    )

    # These are the timepoints for which we'll export results that will be
    # used in the next subproblem (if relevant)
    m.TMPS_TO_LINK = Set(
        within=m.TMPS,
        ordered=True,
        rule=lambda mod:
        set([tmp for tmp in mod.TMPS if mod.link_to_next_subproblem[tmp]])
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "timepoints.tab"),
        index=m.TMPS,
        param=(m.tmp_weight,
               m.hrs_in_tmp,
               m.prev_stage_tmp_map,
               m.link_to_next_subproblem,
               m.month),
        select=("timepoint",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "previous_stage_timepoint_map",
                "link_to_next_subproblem",
                "month")
    )


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    timepoints = c.execute(
        """SELECT timepoint, period, timepoint_weight,
           number_of_hours_in_timepoint, previous_stage_timepoint_map, 
           link_to_next_subproblem, month
           FROM inputs_temporal_timepoints
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {}
           AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    )

    return timepoints


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    timepoints.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    timepoints = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "timepoints.tab"),
              "w", newline="") as timepoints_tab_file:
        writer = csv.writer(timepoints_tab_file, delimiter="\t",
                            lineterminator="\n")

        # Write header
        writer.writerow(["timepoint", "period", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "previous_stage_timepoint_map",
                         "link_to_next_subproblem", "month"])

        # Write timepoints
        for row in timepoints:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


# Validation
###############################################################################

def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    # timepoints = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)
    # validate timepoint inputs

    # TODO: what checks do we need on the sum of all timepoint weights (x
    #  number of hours in timepoint?)
