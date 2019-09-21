#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.temporal.operations.horizons** module describes the
operational grouping of timepoints in the optimization (i.e. which
operational decisions are linked together and which are independent). Some
operational constraints are enforced at the horizon level.
"""

import csv
import os.path

from pyomo.environ import Set, Param, PositiveIntegers


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the dynamic inputs class object; not used here

    The module adds the * HORIZON_LENGTH_TYPES* and *HORIZONS_BY_BALANCING_TYPE*
    sets to the model formulation.

    Balancing types are strings, e.g. year, month, week, day.

    Horizons must be non-negative integers and each value of the
    HORIZONS_BY_BALANCING_TYPE indexed set is ordered (i.e. the horizons
    within a balancing type are ordered).

    We will designate the *HORIZON_LENGTH_TYPES* set with :math:`B` and
    balancing t ype index with :math:`b`.

    The *HORIZONS_BY_BALANCING_TYPE* set is designated with :math:`H_b` and
    the horizons index will be :math:`h_b`.

    Each horizon is associated with a *boundary* parameter.

    The *boundary*\ :sub:`h`\ parameter can take one of two values:
    'circular' or 'linear.' If the boundary is 'circular,' then the last
    timepoint of the horizon is treated as the 'previous' timepoint for the
    first timepoint of the horizon (e.g. for ramping constraints or tracking
    storage state of charge).

    This module organizes timepoints into balancing types and horizons. Each
    timepoint is assigned a *horizon* parameter for each balancing type where
    :math:`horizon_{t,b}\in H`, i.e. each timepoint occurs within a
    specific horizon for each balancing type.

    """
    m.HORIZONS = Set(ordered=True)
    m.horizon_length_type = Param(m.HORIZONS)
    m.boundary = Param(m.HORIZONS, within=['circular', 'linear'])

    def horizon_length_types_init(mod):
        """
        :param mod:
        :return:
        """
        horizon_length_types = list()
        for h in mod.HORIZONS:
            if mod.horizon_length_type[h] in horizon_length_types:
                pass
            else:
                horizon_length_types.append(mod.horizon_length_type[h])

        return horizon_length_types

    m.HORIZON_LENGTH_TYPES = Set(initialize=horizon_length_types_init)

    def horizons_by_horizon_length_type_init(mod, bt):
        """
        :param mod:
        :param bt:
        :return:
        """
        horizons_of_horizon_length_type = []
        for horizon in mod.HORIZONS:
            if mod.horizon_length_type[horizon] == bt:
                horizons_of_horizon_length_type.append(horizon)

        return horizons_of_horizon_length_type

    m.HORIZONS_BY_BALANCING_TYPE = Set(
        m.HORIZON_LENGTH_TYPES, within=PositiveIntegers,
        initialize=horizons_by_horizon_length_type_init
    )

    m.TIMEPOINTS_ON_HORIZON = Set(
        m.HORIZONS, within=PositiveIntegers, ordered=True
    )

    # TODO: can create here instead of upstream in data (i.e. we can get teh
    #  balancing type index from the horizon of the timepoint)
    m.horizon = Param(m.TIMEPOINTS, m.HORIZON_LENGTH_TYPES)

    # Determine the first and last timepoint of the horizon
    # NOTE: it's an ordered set, so getting the first and last element seems
    # fine; do this in a separate commit
    m.first_horizon_timepoint = Param(
        m.HORIZONS, within=PositiveIntegers,
        initialize=lambda mod, h:
        list(mod.TIMEPOINTS_ON_HORIZON[h])[0]
    )

    m.last_horizon_timepoint = Param(
        m.HORIZONS, within=PositiveIntegers,
        initialize=lambda mod, h:
        list(mod.TIMEPOINTS_ON_HORIZON[h])[-1]
    )

    # Determine the previous timepoint for each timepoint; depends on
    # whether horizon is circular or linear and relies on having ordered
    # TIMEPOINTS
    m.previous_timepoint = Param(
        m.TIMEPOINTS, m.HORIZON_LENGTH_TYPES, initialize=previous_timepoint_init
    )

    # Determine the next timepoint for each timepoint; depends on
    # whether horizon is circular or linear and relies on having ordered
    # TIMEPOINTS
    m.next_timepoint = Param(
        m.TIMEPOINTS, m.HORIZON_LENGTH_TYPES, initialize=next_timepoint_init
    )


def previous_timepoint_init(mod, tmp, horizon_length_type):
    """
    :param mod:
    :param tmp:
    :param horizon_length_type:
    :return:

    Determine the previous timepoint for each timepoint. If the timepoint is
    the first timepoint of a horizon and the horizon boundary is circular,
    then the previous timepoint is the last timepoint of the respective
    horizon (for each horizon type). If the timepoint is the first timepoint
    of a horizon and the horizon boundary is linear, then no previous
    timepoint is defined. In all other cases, the previous timepoints is the
    one with an index of tmp-1.
    """
    prev_tmp_dict = {}
    for horizon in mod.HORIZONS_BY_BALANCING_TYPE[horizon_length_type]:
        for tmp in mod.TIMEPOINTS_ON_HORIZON[horizon]:
            if tmp == mod.first_horizon_timepoint[horizon]:
                if mod.boundary[horizon] == "circular":
                    prev_tmp_dict[tmp, horizon_length_type] = \
                        mod.last_horizon_timepoint[
                            horizon]
                elif mod.boundary[horizon] == "linear":
                    prev_tmp_dict[tmp, horizon_length_type] = None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for horizon '{}'".
                        format(
                            mod.boundary[horizon],
                            horizon)
                        + "\n" +
                        "Horizon boundary must be either 'circular' or "
                        "'linear'"
                    )
            else:
                prev_tmp_dict[tmp, horizon_length_type] = \
                    list(mod.TIMEPOINTS_ON_HORIZON[horizon])[
                        list(mod.TIMEPOINTS_ON_HORIZON[horizon])
                        .index(tmp) - 1
                        ]

    return prev_tmp_dict


def next_timepoint_init(mod, tmp, horizon_length_type):
    """
    :param mod:
    :param tmp:
    :param horizon_length_type:
    :return:
    Determine the next timepoint for each timepoint. If the timepoint is
    the last timepoint of a horizon and the horizon boundary is circular,
    then the next timepoint is the first timepoint of the respective
    horizon. If the timepoint is the last timepoint of a horizon and the
    horizon boundary is linear, then no next timepoint is defined. In all
    other cases, the next timepoint is the one with an index of tmp+1.
    """
    next_tmp_dict = {}
    for horizon in mod.HORIZONS_BY_BALANCING_TYPE[horizon_length_type]:
        for tmp in mod.TIMEPOINTS_ON_HORIZON[horizon]:
            if tmp == mod.last_horizon_timepoint[horizon]:
                if mod.boundary[horizon] == "circular":
                    next_tmp_dict[tmp, horizon_length_type] = \
                        mod.first_horizon_timepoint[horizon]
                elif mod.boundary[horizon] == "linear":
                    next_tmp_dict[tmp, horizon_length_type] = None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for horizon '{}'".
                        format(mod.boundary[horizon], horizon)
                        + "\n" +
                        "Horizon boundary must be either 'circular' or "
                        "'linear'"
                    )
            else:
                next_tmp_dict[tmp, horizon_length_type] = \
                    list(mod.TIMEPOINTS_ON_HORIZON[horizon])[
                        list(mod.TIMEPOINTS_ON_HORIZON[horizon])
                        .index(tmp) + 1
                        ]

    return next_tmp_dict


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "horizons.tab"),
                     select=("horizon", "horizon_length_type", "boundary"),
                     index=m.HORIZONS,
                     param=(m.horizon_length_type, m.boundary)
                     )

    with open(os.path.join(scenario_directory, subproblem, stage,
                           "inputs", "horizon_timepoints.tab")
              ) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        tmps_on_horizon = dict()
        horizon_by_tmp = dict()
        for row in reader:
            if int(row[0]) not in tmps_on_horizon.keys():
                tmps_on_horizon[int(row[0])] = [int(row[2])]
            else:
                tmps_on_horizon[int(row[0])].append(int(row[2]))

            horizon_by_tmp[int(row[2]), row[1]] = int(row[0])

    data_portal.data()[
        "TIMEPOINTS_ON_HORIZON"
    ] = tmps_on_horizon

    data_portal.data()["horizon"] = horizon_by_tmp


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c1 = conn.cursor()
    horizons = c1.execute(
        """SELECT horizon, horizon_length_type, boundary
           FROM inputs_temporal_horizons
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem
        )
    )

    c2 = conn.cursor()
    timepoint_horizons = c2.execute(
        """SELECT horizon, horizon_length_type, timepoint
        FROM inputs_temporal_horizon_timepoints
        WHERE temporal_scenario_id = {}
       AND subproblem_id = {}
       AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    )

    return horizons, timepoint_horizons


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # horizons = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    horizons.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    horizons, timepoint_horizons = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "horizons.tab"),
              "w", newline="") as horizons_tab_file:
        hwriter = csv.writer(horizons_tab_file, delimiter="\t")

        # Write header
        hwriter.writerow(["horizon", "horizon_length_type", "boundary"])

        for row in horizons:
            hwriter.writerow(row)

    with open(os.path.join(inputs_directory, "horizon_timepoints.tab"), "w",
              newline="") as timepoint_horizons_tab_file:
        thwriter = csv.writer(timepoint_horizons_tab_file, delimiter="\t")

        # Write header
        thwriter.writerow(["horizon", "horizon_length_type", "timepoint"])

        for row in timepoint_horizons:
            thwriter.writerow(row)

