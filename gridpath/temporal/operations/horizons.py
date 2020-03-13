#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
GridPath organizes timepoints into *balancing types* and *horizons* that
describe how *timepoints* are grouped together when making operational
decisions, with some operational constraints enforced over the *horizon* for
each *balancing type*, e.g. hydro budgets or storage energy balance. As a
simple example, in the case of modeling a full year with 8760 timepoints, we
could have three *balancing types*: a day, a month, and a year; there would
then be 365 *horizons* of the *balancing type* 'day,' 12 *horizons* of the
*balancing type* 'month,' and 1 *horizon* of the *balancing type* 'year.'
Within each balancing types, horizons are modeled as independent from each
other for operational purposes (i.e operational decisions made on one
horizon do not affect those made on another horizon). Generator and storage
resources in GridPath are also assigned *balancing types*: a hydro plant
of the *balancing type* 'day' would have to meet an energy budget constraint
on each of the 365 'day' *horizons* whereas one of the *balancing type*
'year' would only have a single energy budget constraint grouping all 8760
timepoints.

Each *horizon* has boundary condition that can be 'circular' or 'linear.' With
the 'circular' approach, the last timepoint of the horizon is considered the
previous timepoint for the first timepoint of the horizon (for the purposes
of functionality such as ramp constraints or tracking storage state of
charge). If the boundary is 'linear,' then we ignore constraints relating to
the previous timepoint in the first timepoint of a horizon.
"""

import csv
import os.path

from pyomo.environ import Set, Param, PositiveIntegers


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`BLN_TYPE_HRZS`                                                 |
    |                                                                         |
    | Two dimensional set of balancing types and their associated horizons.   |
    | Balancing types are strings, e.g. year, month, week, day, whereas       |
    | horizons must be non-negative integers.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`TMPS_BY_BLN_TYPE_HRZ`                                          |
    | | *Defined over*: :code:`BLN_TYPE_HRZS`                                 |
    |                                                                         |
    | Ordered, indexed set that describes the the horizons associated with    |
    | each balancing type. The timepoins within a horizon-balancing type      |
    | are ordered.                                                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`BLN_TYPES`                                                     |
    |                                                                         |
    | The list of all balancing types.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`HRZS_BY_BLN_TYPE`                                              |
    | | *Defined over*: :code:`BLN_TYPES`                                     |
    |                                                                         |
    | Ordered, indexed set that describes the horizons associated with        |
    | each balancing type. The horizons within a balancing type are ordered.  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`horizon`                                                       |
    | | *Defined over*: :code:`TIMEPOINTS x BLN_TYPES`                        |
    |                                                                         |
    | Describes the horizon that each timeoint belongs to for a given         |
    | balancing type. Depending on the balancing type, timepoints can be      |
    | grouped in different horizons.                                          |
    +-------------------------------------------------------------------------+
    | | :code:`boundary`                                                      |
    | | *Defined over*: :code:`BLN_TYPE_HRZS`                                 |
    | | *Within*: :code:`['circular', 'linear']`                              |
    |                                                                         |
    | The boundary for each horizon. If the boundary is 'circular,' then the  |
    | last timepoint of the horizon is treated as the 'previous' timepoint    |
    | for the first timepoint of the horizon (e.g. for ramping constraints    |
    | or tracking storage state of charge).                                   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Input Params                                                    |
    +=========================================================================+
    | | :code:`first_hrz_tmp`                                                 |
    | | *Defined over*: :code:`BLN_TYPE_HRZS`                                 |
    |                                                                         |
    | Derived parameter describing the first timepoint in each horizon for a  |
    | given balancing type. Note: this relies on :code:`TMPS_BY_BLN_TYPE_HRZ` |
    | being an ordered (indexed) set.                                         |
    +-------------------------------------------------------------------------+
    | | :code:`last_hrz_tmp`                                                  |
    | | *Defined over*: :code:`BLN_TYPE_HRZS`                                 |
    |                                                                         |
    | Derived parameter describing the last timepoint in each horizon for a   |
    | given balancing type. Note: this relies on :code:`TMPS_BY_BLN_TYPE_HRZ` |
    | being an ordered (indexed) set.                                         |
    +-------------------------------------------------------------------------+
    | | :code:`prev_tmp`                                                      |
    | | *Defined over*: :code:`TIMEPOINTS x BLN_TYPES`                        |
    |                                                                         |
    | Derived parameter describing the previous timepoint for each timepoint  |
    | in each balancing type; depends on whether horizon is circular or       |
    | linear and relies on having ordered :code:`TIMEPOINTS`.                 |
    +-------------------------------------------------------------------------+
    | | :code:`next_tmp`                                                      |
    | | *Defined over*: :code:`TIMEPOINTS x BLN_TYPES`                        |
    |                                                                         |
    | Derived parameter describing the next timepoint for each timepoint in   |
    | each balancing type; depends on whether horizon is circular or linear   |
    | and relies on having ordered :code:`TIMEPOINTS`.                        |
    +-------------------------------------------------------------------------+



    """

    # Sets
    ###########################################################################

    m.BLN_TYPE_HRZS = Set(
        dimen=2, ordered=True
    )

    m.TMPS_BY_BLN_TYPE_HRZ = Set(
        m.BLN_TYPE_HRZS,
        within=PositiveIntegers, ordered=True
    )

    # Derived Sets
    ###########################################################################

    m.BLN_TYPES = Set(
        initialize=balancing_types_init
    )

    m.HRZS_BY_BLN_TYPE = Set(
        m.BLN_TYPES,
        within=PositiveIntegers,
        initialize=horizons_by_balancing_type_init
    )

    # Required Params
    ###########################################################################

    # TODO: can create here instead of upstream in data (i.e. we can get the
    #  balancing type index from the horizon of the timepoint)
    m.horizon = Param(
        m.TIMEPOINTS, m.BLN_TYPES
    )

    m.boundary = Param(
        m.BLN_TYPE_HRZS,
        within=['circular', 'linear']
    )

    # Derived Params
    ###########################################################################

    m.first_hrz_tmp = Param(
        m.BLN_TYPE_HRZS,
        within=PositiveIntegers,
        initialize=lambda mod, b, h:
        list(mod.TMPS_BY_BLN_TYPE_HRZ[b, h])[0]
    )

    m.last_hrz_tmp = Param(
        m.BLN_TYPE_HRZS,
        within=PositiveIntegers,
        initialize=lambda mod, b, h:
        list(mod.TMPS_BY_BLN_TYPE_HRZ[b, h])[-1]
    )

    m.prev_tmp = Param(
        m.TIMEPOINTS, m.BLN_TYPES,
        initialize=prev_tmp_init
    )

    m.next_tmp = Param(
        m.TIMEPOINTS, m.BLN_TYPES,
        initialize=next_tmp_init
    )


# Set Rules
###############################################################################

def balancing_types_init(mod):
    """
    **Set Name**: BLN_TYPES

    Derives the unique set of balancing types from the 2-dimensional
    BLN_TYPE_HRZS set.
    """
    balancing_types = list()
    for (b, h) in mod.BLN_TYPE_HRZS:
        if b in balancing_types:
            pass
        else:
            balancing_types.append(b)

    return balancing_types


def horizons_by_balancing_type_init(mod, bt):
    """
    **Set Name**: HRZS_BY_BLN_TYPE
    **Defined Over**: BLN_TYPES

    Re-arranges the 2-dimensional BLN_TYPE_HRZS set into a 1-dimensional set of
    horizons by balancing type.
    """
    horizons_of_balancing_type = []
    for (b, h) in mod.BLN_TYPE_HRZS:
        if b == bt:
            horizons_of_balancing_type.append(h)

    return horizons_of_balancing_type


# Param Rules
###############################################################################

def prev_tmp_init(mod, tmp, balancing_type_horizon):
    """
    **Param Name**: prev_tmp
    **Defined Over**: TIMEPOINTS x BLN_TYPES

    Determine the previous timepoint for each timepoint. If the timepoint is
    the first timepoint of a horizon and the horizon boundary is circular,
    then the previous timepoint is the last timepoint of the respective
    horizon (for each horizon type). If the timepoint is the first timepoint
    of a horizon and the horizon boundary is linear, then no previous
    timepoint is defined. In all other cases, the previous timepoints is the
    one with an index of tmp-1.
    """
    prev_tmp_dict = {}
    for (bt, hrz) in mod.BLN_TYPE_HRZS:
        for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]:
            if tmp == mod.first_hrz_tmp[bt, hrz]:
                if mod.boundary[bt, hrz] == "circular":
                    prev_tmp_dict[tmp, bt] = mod.last_hrz_tmp[bt, hrz]
                elif mod.boundary[bt, hrz] == "linear":
                    prev_tmp_dict[tmp, bt] = None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for balancing type "
                        "horizon '{} {}'".
                        format(mod.boundary[bt, hrz], bt, hrz)
                        + "\n" +
                        "Horizon boundary must be either 'circular' or "
                        "'linear'"
                    )
            else:
                prev_tmp_dict[tmp, bt] = list(
                    mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
                )[list(mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]).index(tmp) - 1]

    return prev_tmp_dict


def next_tmp_init(mod, tmp, balancing_type_horizon):
    """
    **Param Name**: next_tmp
    **Defined Over**: TIMEPOINTS x BLN_TYPES

    Determine the next timepoint for each timepoint. If the timepoint is
    the last timepoint of a horizon and the horizon boundary is circular,
    then the next timepoint is the first timepoint of the respective
    horizon. If the timepoint is the last timepoint of a horizon and the
    horizon boundary is linear, then no next timepoint is defined. In all
    other cases, the next timepoint is the one with an index of tmp+1.
    """
    next_tmp_dict = {}
    for (bt, hrz) in mod.BLN_TYPE_HRZS:
        for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]:
            if tmp == mod.last_hrz_tmp[bt, hrz]:
                if mod.boundary[bt, hrz] == "circular":
                    next_tmp_dict[tmp, bt] = mod.first_hrz_tmp[bt, hrz]
                elif mod.boundary[bt, hrz] == "linear":
                    next_tmp_dict[tmp, bt] = None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for balancing "
                        "type horizon '{} {}'".
                        format(mod.boundary[bt, hrz], bt, hrz)
                        + "\n" +
                        "Horizon boundary must be either 'circular' or "
                        "'linear'"
                    )
            else:
                next_tmp_dict[tmp, bt] = list(
                    mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
                )[list(mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]).index(tmp) + 1]

    return next_tmp_dict


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "horizons.tab"),
        select=("balancing_type_horizon", "horizon", "boundary"),
        index=m.BLN_TYPE_HRZS,
        param=m.boundary
    )

    with open(os.path.join(scenario_directory, subproblem, stage,
                           "inputs", "horizon_timepoints.tab")
              ) as f:
        reader = csv.reader(f, delimiter="\t", lineterminator="\n")
        next(reader)
        tmps_on_horizon = dict()
        horizon_by_tmp = dict()
        for row in reader:
            if (row[1], int(row[0])) not in tmps_on_horizon.keys():
                tmps_on_horizon[row[1], int(row[0])] = [int(row[2])]
            else:
                tmps_on_horizon[row[1], int(row[0])].append(int(row[2]))

            horizon_by_tmp[int(row[2]), row[1]] = int(row[0])

    data_portal.data()["TMPS_BY_BLN_TYPE_HRZ"] = tmps_on_horizon
    data_portal.data()["horizon"] = horizon_by_tmp


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
    c1 = conn.cursor()
    horizons = c1.execute(
        """SELECT horizon, balancing_type_horizon, boundary
        FROM inputs_temporal_horizons
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        ORDER BY balancing_type_horizon, horizon;
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    )

    c2 = conn.cursor()
    timepoint_horizons = c2.execute(
        """SELECT horizon, balancing_type_horizon, timepoint
        FROM inputs_temporal_horizon_timepoints
        WHERE temporal_scenario_id = {}
       AND subproblem_id = {}
       AND stage_id = {}
       ORDER BY balancing_type_horizon, timepoint;""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    )

    return horizons, timepoint_horizons


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
        hwriter = csv.writer(horizons_tab_file, delimiter="\t",
                             lineterminator="\n")

        # Write header
        hwriter.writerow(["horizon", "balancing_type_horizon", "boundary"])

        for row in horizons:
            hwriter.writerow(row)

    with open(os.path.join(inputs_directory, "horizon_timepoints.tab"), "w",
              newline="") as timepoint_horizons_tab_file:
        thwriter = csv.writer(timepoint_horizons_tab_file, delimiter="\t",
                              lineterminator="\n")

        # Write header
        thwriter.writerow(["horizon", "balancing_type_horizon", "timepoint"])

        for row in timepoint_horizons:
            thwriter.writerow(row)


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
    pass
    # Validation to be added
    # horizons = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

