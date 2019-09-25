#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.temporal.operations.timepoints** module describes the smallest
temporal unit over which operational variables are defined.
"""

import csv
import os.path

from pyomo.environ import Param, Set, NonNegativeReals, NonNegativeIntegers,\
    PositiveIntegers


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the dynamic inputs class object; not used here

    The module adds the *TIMEPOINTS* set to the model formulation.

    Timepoints must be non-negative integers and the set is ordered.

    We will designate the *TIMEPOINTS* set with :math:`T` and the timepoints
    index will be :math:`t`.

    In addition, the *number_of_hours_in_timepoint* parameter (indexed by
    TIMEPOINTS) is added to the formulation here. For example, a 15-minute
    timepoint will have 0.25 hours per timepoint whereas a 4-hour timepoint
    will have 4 hours per timepoint. This parameter is used by other modules
    to track energy (e.g. storage state of charge).

    The *timepoint_weight* parameter accounts for the number of other similar
    'timepoints' that are not explicitly included in the optimization, but that
    the included timepoint represents in the objective function. For example,
    we could include one day from the month to represent the entire month,
    in which case the *timepoint_weight*\ :sub:`t`\ for each timepoint
    on that day will be the number of the days in :math:`h`'s respective month.

    Timepoints do not need to have the same *number_of_hours_in_timepoint*
    value, i.e. one of them can represent a 5-minute segment and another a
    24-hour segment.

    .. TODO:: we need to check there are no exceptions to the above statement

    """
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True)
    m.number_of_hours_in_timepoint = \
        Param(m.TIMEPOINTS, within=NonNegativeReals)
    # TODO: what checks do we need on the sum of all timepoint weights (x
    #  number of hours in timepoint?)
    m.timepoint_weight = Param(m.TIMEPOINTS, within=NonNegativeReals)
    m.previous_stage_timepoint_map = \
        Param(m.TIMEPOINTS, within=NonNegativeIntegers)

    # Make a months set to use as index for some params
    m.MONTHS = Set(within=PositiveIntegers, initialize=list(range(1, 12 + 1)))
    m.month = Param(m.TIMEPOINTS, within=m.MONTHS)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "timepoints.tab"),
                     index=m.TIMEPOINTS,
                     param=(m.timepoint_weight,
                            m.number_of_hours_in_timepoint,
                            m.previous_stage_timepoint_map,
                            m.month),
                     select=("TIMEPOINTS",
                             "timepoint_weight",
                             "number_of_hours_in_timepoint",
                             "previous_stage_timepoint_map",
                             "month")
                     )


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
           number_of_hours_in_timepoint, previous_stage_timepoint_map, month
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


def validate_inputs(subscenarios, subproblem, stage, conn):
    """

    :param inputs: dictionary with inputs (loaded from database) by module name
    :param subscenarios: SubScenarios object with all subscenario info
    :param conn: database connection
    :return:
    """
    # timepoints = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)
    # validate timepoint inputs


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
        writer = csv.writer(timepoints_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["TIMEPOINTS", "period", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "previous_stage_timepoint_map", "month"])

        # Write timepoints
        for row in timepoints:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
