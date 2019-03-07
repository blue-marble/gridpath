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

    The module adds the *HORIZONS* set to the model formulation.

    Horizons must be non-negative integers and the set is ordered.

    We will designate the *HORIZONS* set with :math:`H` and the timepoints
    index will be :math:`h`.

    Each horizon is associated with a *boundary* parameter and a *horizon_weight*
    parameter.

    The *boundary*\ :sub:`h`\ parameter can take one of two values:
    'circular' or 'linear.' If the boundary is 'circular,' then the last
    timepoint of the horizon is treated as the 'previous' timepoint for the
    first timepoint of the horizon (e.g. for ramping constraints or tracking
    storage state of charge).

    The *horizon_weight* parameter accounts for the number of other similar
    'horizons' that are not explicitly included in the optimization, but that
    the included horizon represents in the objective function. For example,
    we could include one day from the month to represent the entire month,
    in which case the *horizon_weight*\ :sub:`h`\ will be the number of the
    days in :math:`h`'s respective month.

    This module organizes timepoints into horizons. Each timepoint is
    assigned a *horizon* parameter where :math:`horizon_t\in H`, i.e. each
    timepoint occurs within a specific horizon.

    We also derive the following set and parameters:

    We use :math:`horizon_t` to create the indexed set
    *TIMEPOINTS_ON_HORIZON* (:math:`\{T_h\}_{h\in H}`;
    :math:`T_h\subset T`) that allows us to determine the subsets of
    timepoints :math:`T_h` that occur on each horizon :math:`h`.

    Next, we use the *TIMEPOINTS_ON_HORIZON* set to determine the first and
    last timepoint on each horizon. The respective parameters are
    *first_horizon_timepoint*\ :sub:`h`\ and *last_horizon_timepoint*\
    :sub:`h`\.

    """
    m.HORIZONS = Set(within=NonNegativeIntegers, ordered=True)

    m.boundary = Param(m.HORIZONS, within=['circular', 'linear'])
    # TODO: think through and document what happens with the horizon weights
    #  if we have one horizon that is a day and another horizon that is a week
    # TODO: what checks do we need on the sum of all horizon weights (if a
    #  period is a year, then the sum of the weights of distinct horizons of
    #  timepoints in the same period should sum up to 365 (or 365.25 or 366?)
    #  but is there are more general case? Or maybe we need to be summing
    #  over the the timepoint number_of_hours_represented times the
    #  horizon_weight for the timepoint's horizon and get 8760?
    #  Maybe think of the horizon weight as the number of (not explicitly
    #  modeled) *days* it represents, similar to the timepoint representing
    #  number of *hours*
    m.horizon_weight = Param(m.HORIZONS, within=NonNegativeReals)

    # TODO: are months used anywhere or can we remove them for now?
    # Make a months set to use as index for some params
    m.MONTHS = Set(within=PositiveIntegers, initialize=list(range(1, 12 + 1)))
    m.month = Param(m.HORIZONS, within=m.MONTHS)

    # Assign horizons to timepoints
    m.horizon = Param(m.TIMEPOINTS, within=m.HORIZONS)

    m.TIMEPOINTS_ON_HORIZON = \
        Set(m.HORIZONS, ordered=True,
            initialize=lambda mod, h:
            set(tmp for tmp in mod.TIMEPOINTS if mod.horizon[tmp] == h))

    # Determine the first and last timepoint of the horizon
    # TODO: is there are a better way to do this than relying on min and max?
    m.first_horizon_timepoint = \
        Param(m.HORIZONS,
              initialize=
              lambda mod, h: min(tmp for tmp in mod.TIMEPOINTS_ON_HORIZON[h]))

    m.last_horizon_timepoint = \
        Param(m.HORIZONS,
              initialize=
              lambda mod, h: max(tmp for tmp in mod.TIMEPOINTS_ON_HORIZON[h]))

    # Determine the previous timepoint for each timepoint; depends on
    # whether horizon is circular or linear and relies on having ordered
    # TIMEPONTS set to increment by 1
    m.previous_timepoint = \
        Param(m.TIMEPOINTS,
              initialize=previous_timepoint_init)


def previous_timepoint_init(mod, tmp):
    """
    :param mod:
    :param tmp:
    :return:

    Determine the previous timepoint for each timepoint. If the timepoint is
    the first timepoint of a horizon and the horizon boundary is circular,
    then the previous timepoint is the last timepoint of the respective
    horizon. If the timepoint is the first timepoint of a horizon and the
    horizon boundary is linear, then no previous timepoint is defined. In all
    other cases, the previous timepoints is the one with an index of tmp-1.
    """
    # TODO: can we make this determination more robust than subtracting 1 or
    #  should we require a data check to ensure TIMEPOINTS ordered set has
    #  increments of 1 only? Perhaps we should use the same approach as wth
    #  previous_period and use the timepoint list index not its actual ID.
    prev_tmp_dict = {}
    for tmp in mod.TIMEPOINTS:
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]]:
            if mod.boundary[mod.horizon[tmp]] == "circular":
                prev_tmp_dict[tmp] = \
                    mod.last_horizon_timepoint[mod.horizon[tmp]]
            elif mod.boundary[mod.horizon[tmp]] == "linear":
                prev_tmp_dict[tmp] = None
            else:
                raise ValueError(
                    "Invalid boundary value '{}' for horizon '{}'".
                    format(
                        mod.boundary[mod.horizon[tmp]], mod.horizon[tmp])
                    + "\n" +
                    "Horizon boundary must be either 'circular' or 'linear'"
                )
        else:
            prev_tmp_dict[tmp] = tmp-1

    return prev_tmp_dict


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon,
                                           "inputs", "horizons.tab"),
                     select=("HORIZONS", "boundary", "horizon_weight",
                             "month"),
                     index=m.HORIZONS,
                     param=(m.boundary, m.horizon_weight, m.month)
                     )

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "timepoints.tab"),
                     select=("TIMEPOINTS","horizon"),
                     index=m.TIMEPOINTS,
                     param=m.horizon
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios:
    :param c:
    :param inputs_directory:
    :return:
    """

    # horizons.tab
    with open(os.path.join(inputs_directory, "horizons.tab"), "w") as \
            horizons_tab_file:
        writer = csv.writer(horizons_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["HORIZONS", "boundary", "horizon_weight", "month"])

        horizons = c.execute(
            """SELECT horizon, boundary, horizon_weight, month
               FROM inputs_temporal_horizons
               WHERE timepoint_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID
            )
        ).fetchall()

        for row in horizons:
            writer.writerow(row)
