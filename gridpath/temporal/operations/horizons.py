#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.temporal.operations.horizons** module describes the
operational grouping of timepoints in the optimization (i.e. which
operational decisions are linked together and which are independent). Some
operational constraints are enforced at the horizon level.
"""

from builtins import range
import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeIntegers, NonNegativeReals,\
    PositiveIntegers


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the dynamic inputs class object; not used here

    The module adds the * BALANCING_TYPES* and *HORIZONS_BY_BALANCING_TYPE*
    sets to the model formulation.

    Balancing types are strings, e.g. year, month, week, day.

    Horizons must be non-negative integers and each value of the
    HORIZONS_BY_BALANCING_TYPE indexed set is ordered (i.e. the horizons
    within a balancing type are ordered).

    We will designate the *BALANCING_TYPES* set with :math:`B` and
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
    m.BALANCING_TYPE_HORIZONS = Set(dimen=2)
    m.boundary = Param(m.BALANCING_TYPE_HORIZONS, within=['circular', 'linear'])

    def balancing_types_init(mod):
        """
        :param mod:
        :return:
        """
        balancing_types = list()
        for key in mod.BALANCING_TYPE_HORIZONS:
            if key[0] in balancing_types:
                pass
            else:
                balancing_types.append(key[0])

        return balancing_types

    m.BALANCING_TYPES = Set(initialize=balancing_types_init)

    def horizons_by_balancing_type_init(mod, t):
        """
        :param mod:
        :param t:
        :return:
        """
        horizons_of_balancing_type = []
        for (balancing_type, horizon) in mod.BALANCING_TYPE_HORIZONS:
            if balancing_type == t:
                horizons_of_balancing_type.append(horizon)

        return horizons_of_balancing_type

    m.HORIZONS_BY_BALANCING_TYPE = Set(
        m.BALANCING_TYPES, within=PositiveIntegers,
        initialize=horizons_by_balancing_type_init
    )

    m.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON = Set(
        m.BALANCING_TYPE_HORIZONS, within=PositiveIntegers, ordered=True
    )

    m.horizon = Param(m.TIMEPOINTS, m.BALANCING_TYPES)

    # Determine the first and last timepoint of the horizon
    # TODO: is there are a better way to do this than relying on min and max?
    # NOTE: it's an ordered set, so getting the first and last element seems
    # fine; do this in a separate commit
    m.first_horizon_timepoint = Param(
        m.BALANCING_TYPE_HORIZONS, within=PositiveIntegers,
        initialize=lambda mod, t, h:
        list(mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[t, h])[0]
    )

    m.last_horizon_timepoint = Param(
        m.BALANCING_TYPE_HORIZONS, within=PositiveIntegers,
        initialize=lambda mod, t, h:
        list(mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[t, h])[-1]
    )

    # Determine the previous timepoint for each timepoint; depends on
    # whether horizon is circular or linear and relies on having ordered
    # TIMEPOINTS
    m.previous_timepoint = Param(
        m.BALANCING_TYPES, m.TIMEPOINTS, initialize=previous_timepoint_init
    )

    # Determine the next timepoint for each timepoint; depends on
    # whether horizon is circular or linear and relies on having ordered
    # TIMEPOINTS
    m.next_timepoint = Param(
        m.BALANCING_TYPES, m.TIMEPOINTS, initialize=next_timepoint_init
    )


def previous_timepoint_init(mod, balancing_type, tmp):
    """
    :param mod:
    :param balancing_type:
    :param tmp:
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
    for horizon in mod.HORIZONS_BY_BALANCING_TYPE[balancing_type]:
        for tmp in mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[balancing_type,
                                                          horizon]:
            if tmp == mod.first_horizon_timepoint[
                    balancing_type, horizon]:
                if mod.boundary[balancing_type, horizon] == "circular":
                    prev_tmp_dict[balancing_type, int(tmp)] = \
                        mod.last_horizon_timepoint[
                            balancing_type, horizon]
                elif mod.boundary[balancing_type, horizon] == "linear":
                    prev_tmp_dict[balancing_type, int(tmp)] = None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for "
                        "balancing_type {} horizon '{}'".
                        format(
                            mod.boundary[balancing_type, horizon],
                            balancing_type, horizon)
                        + "\n" +
                        "Horizon boundary must be either 'circular' or "
                        "'linear'"
                    )
            else:
                prev_tmp_dict[balancing_type, int(tmp)] = \
                    list(mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[
                             balancing_type, horizon])[
                        list(mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[
                             balancing_type, horizon])
                        .index(tmp) - 1
                        ]

    return prev_tmp_dict


def next_timepoint_init(mod, balancing_type, tmp):
    """
    :param mod:
    :param balancing_type:
    :param tmp:
    :return:
    Determine the next timepoint for each timepoint. If the timepoint is
    the last timepoint of a horizon and the horizon boundary is circular,
    then the next timepoint is the first timepoint of the respective
    horizon. If the timepoint is the last timepoint of a horizon and the
    horizon boundary is linear, then no next timepoint is defined. In all
    other cases, the next timepoint is the one with an index of tmp+1.
    """
    next_tmp_dict = {}
    for horizon in mod.HORIZONS_BY_BALANCING_TYPE[balancing_type]:
        for tmp in mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[balancing_type,
                                                          horizon]:
            if tmp == mod.last_horizon_timepoint[
                    balancing_type, horizon]:
                if mod.boundary[balancing_type, horizon] == "circular":
                    next_tmp_dict[balancing_type, int(tmp)] = \
                        mod.first_horizon_timepoint[
                            balancing_type, horizon]
                elif mod.boundary[balancing_type, horizon] == "linear":
                    next_tmp_dict[balancing_type, int(tmp)] = None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for "
                        "balancing_type {} horizon '{}'".
                        format(
                            mod.boundary[balancing_type, horizon],
                            balancing_type, horizon)
                        + "\n" +
                        "Horizon boundary must be either 'circular' or "
                        "'linear'"
                    )
            else:
                next_tmp_dict[balancing_type, int(tmp)] = \
                    list(mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[
                             balancing_type, horizon])[
                        list(mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[
                                 balancing_type, horizon])
                        .index(tmp) + 1
                        ]

    return next_tmp_dict


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "horizons.tab"),
                     select=("balancing_type", "horizon", "boundary"),
                     index=m.BALANCING_TYPE_HORIZONS,
                     param=m.boundary
                     )

    with open(os.path.join(scenario_directory, subproblem, stage,
                           "inputs", "horizon_timepoints.tab")
              ) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        tmps_on_balancing_type_horizon = dict()
        horizon_by_tmp = dict()
        for row in reader:
            if (row[0], int(row[1])) not in tmps_on_balancing_type_horizon.keys():
                tmps_on_balancing_type_horizon[row[0], int(row[1])] = [int(row[2])]
            else:
                tmps_on_balancing_type_horizon[row[0], int(row[1])].append(int(row[2]))

            horizon_by_tmp[int(row[2]), row[0]] = int(row[1])


    data_portal.data()[
        "TIMEPOINTS_ON_BALANCING_TYPE_HORIZON"
    ] = tmps_on_balancing_type_horizon

    data_portal.data()["horizon"] = horizon_by_tmp


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    horizons = c.execute(
        """SELECT horizon, boundary, horizon_weight
           FROM inputs_temporal_horizons
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem
        )
    )

    return horizons


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

    horizons = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "horizons.tab"), "w", newline="") as \
            horizons_tab_file:
        writer = csv.writer(horizons_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["HORIZONS", "boundary", "horizon_weight"])

        for row in horizons:
            writer.writerow(row)
