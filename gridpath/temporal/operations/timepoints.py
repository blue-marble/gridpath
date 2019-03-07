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

    .. warning:: The *TIMEPOINTS* set must have increments of 1, for the
        calculations of previous timepoint to work in the **horizons** module.
    .. TODO:: see warning above and todo in horizons module; we need to
        enforce increments of 1 or come up with a more robust method for
        determining previous timepoint
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
