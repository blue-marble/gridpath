#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Smallest unit of temporal over which operational variables are defined
"""

import csv
import os.path

from pyomo.environ import Param, Set, NonNegativeReals, NonNegativeIntegers


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True)
    m.number_of_hours_in_timepoint = \
        Param(m.TIMEPOINTS, within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "timepoints.tab"),
                     index=m.TIMEPOINTS,
                     param=m.number_of_hours_in_timepoint,
                     select=("TIMEPOINTS", "number_of_hours_in_timepoint")
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios:
    :param c:
    :param inputs_directory:
    :return:
    """
    # timepoints.tab
    with open(os.path.join(inputs_directory, "timepoints.tab"), "w") as \
            timepoints_tab_file:
        writer = csv.writer(timepoints_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["TIMEPOINTS", "period", "horizon",
                         "number_of_hours_in_timepoint"])

        timepoints = c.execute(
            """SELECT timepoint, period, horizon, number_of_hours_in_timepoint
               FROM inputs_temporal_timepoints
               WHERE timepoint_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID
            )
        ).fetchall()

        for row in timepoints:
            writer.writerow(row)