#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.temporal.operations.timepoints** module describes the smallest
temporal unit over which operational variables are defined.
"""

import csv
import os.path

from pyomo.environ import Param, Set, NonNegativeReals, NonNegativeIntegers


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

    Timepoints do not need to have the same *number_of_hours_in_timepoint*
    value, i.e. one of them can represent a 5-minute segment and another a
    24-hour segment.

    .. TODO:: we need to check there are no exceptions to the above statement

    """
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True)
    m.number_of_hours_in_timepoint = \
        Param(m.TIMEPOINTS, within=NonNegativeReals)
    m.previous_stage_timepoint_map = \
        Param(m.TIMEPOINTS, within=NonNegativeIntegers)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "timepoints.tab"),
                     index=m.TIMEPOINTS,
                     param=(m.number_of_hours_in_timepoint,
                            m.previous_stage_timepoint_map),
                     select=("TIMEPOINTS", "number_of_hours_in_timepoint",
                             "previous_stage_timepoint_map")
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
        """SELECT timepoint, period, horizon, 
           number_of_hours_in_timepoint, previous_stage_timepoint_map
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

    with open(os.path.join(inputs_directory, "timepoints.tab"), "w") as \
            timepoints_tab_file:
        writer = csv.writer(timepoints_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["TIMEPOINTS", "period", "horizon",
                         "number_of_hours_in_timepoint",
                         "previous_stage_timepoint_map"])

        # Write timepoints
        for row in timepoints:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
