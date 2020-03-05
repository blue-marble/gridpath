#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path

from db.common_functions import spin_on_database_lock
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint, get_column_row_value


def determine_relevant_timepoints(mod, g, tmp, min_time):
    """
    :param mod:
    :param g:
    :param tmp:
    :param min_time:
    :return: the relevant timepoints to look at for the minimum up/down time
        constraints

    We need to figure out how far back we need to look,
    i.e. which timepoints we need to consider when capacity could have
    been turned on/off that must still be on/off in the current timepoint *t*.

    Any capacity that was turned on/off between t and t-1 must still be
    on/off in t, so timepoint *t* is a relevant timepoint.

    Capacity must also still be on/off if it was turned on/off less than its
    up/down time ago, i.e. if it was turned on/off between timepoints that
    are within the min up/down time from the beginning of the current
    timepoint. Once we reach a timepoint whose duration takes us to a
    point in time that is removed from the beginning of timepoint *t* by a
    time greater than or equal to the min_time, that timepoint is not
    relevant anymore and we have completed our list of relevant timepoints.

    In a simple case, let's assume all timepoints have durations of 1 hour.
    Timepoint t-1 is removed from the start of timepoint *t* by an hour,
    timepoint t-2 by 2 hours, timepoint t-3 by 3 hours, etc. Therefore, if
    if a generator has a 4-hour minimum up time and was started up in t-3 (
    i.e. between t-4 and t-3), then it must still be on in the current
    timepoint. If it was started up in t-4, it has already been up for 4
    hours by the time timepoint *t* begins, so it can be turned off. The
    relevant timepoints are therefore t-1, t-2, and t-3; we do not need to
    constrain capacity turned on/off in t-4 or farther in the past.

    If t-2 has duration of 2-hours, on the other hand, the total duration of
    the previous three timepoints would be 4 hours and the generator turned
    on in t-3 should therefore be allowed to turn off in the current
    timepoint *t*. In this case, the relevant timepoints would be t-1 and
    t-2. By the time we reach t-3, we will have reached the 4-hour minimum
    up/down time, so t-3 will not be relevant for the minimum up time
    constraint in timepoint *t*.
    """
    relevant_tmps = [tmp]

    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        pass  # no relevant timepoints, keep list limited to *t*
    else:
        # The first possible relevant timepoint is the previous timepoint,
        # so we'll check its duration (if it's longer than or equal to the
        # minimum up/down time, we'll break out of the loop immediately)
        relevant_tmp = mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
        hours_from_tmp = \
            mod.number_of_hours_in_timepoint[
                mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]

        while hours_from_tmp < min_time:
            # If we haven't exceed the minimum up/down time yet, this timepoint
            # is relevant and we add it to our list
            relevant_tmps.append(relevant_tmp)

            # In a 'linear' horizon setting, once we reach the first timepoint
            # of the horizon, we break out of the loop since there are no more
            # timepoints to consider
            if mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                    == "linear" \
                    and relevant_tmp == \
                    mod.first_horizon_timepoint[
                        mod.horizon[tmp, mod.balancing_type_project[g]]]:
                break
            # In a 'circular' horizon setting, once we reach timepoint *t*,
            # we break out of the loop since there are no more timepoints to
            # consider (we have already added all horizon timepoints as
            # relevant)
            elif mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                    == "circular" \
                    and relevant_tmp == tmp:
                break
            # Otherwise, we move on to the relevant timepoint's previous
            # timepoint and will add that timepoint's duration to
            # hours_from_tmp
            else:
                hours_from_tmp += \
                    mod.number_of_hours_in_timepoint[
                        mod.previous_timepoint[
                            relevant_tmp, mod.balancing_type_project[g]
                        ]
                    ]
                relevant_tmp = mod.previous_timepoint[
                    relevant_tmp, mod.balancing_type_project[g]]

    return relevant_tmps


def update_dispatch_results_table(
     db, c, results_directory, scenario_id, subproblem, stage, results_file
):
    results = []
    with open(os.path.join(results_directory, results_file), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        header = next(reader)

        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            n_hours_in_tmp = row[6]
            technology = row[7]
            load_zone = row[8]
            power = row[9]
            scheduled_curtailment_mw = get_column_row_value(
                header, "scheduled_curtailment_mw", row)
            subhourly_curtailment_mw = get_column_row_value(
                header,"subhourly_curtailment_mw", row)
            subhourly_energy_delivered_mw = get_column_row_value(
                header, "subhourly_energy_delivered_mw", row)
            total_curtailment_mw = get_column_row_value(
                header, "total_curtailment_mw", row)
            committed_mw = get_column_row_value(header, "committed_mw", row)
            committed_units = get_column_row_value(header, "committed_units", row)
            started_units = get_column_row_value(header, "started_units", row)
            stopped_units = get_column_row_value(header, "stopped_units", row)
            synced_units = get_column_row_value(header, "synced_units", row)

            results.append(
                (scheduled_curtailment_mw, subhourly_curtailment_mw,
                 subhourly_energy_delivered_mw, total_curtailment_mw,
                 committed_mw, committed_units, started_units,
                 stopped_units, synced_units,
                 scenario_id, project, period, subproblem, stage, timepoint)
            )

    # Update the results table with the module-specific results
    update_sql = """
        UPDATE results_project_dispatch
        SET scheduled_curtailment_mw = ?,
        subhourly_curtailment_mw = ?,
        subhourly_energy_delivered_mw = ?,
        total_curtailment_mw = ?,
        committed_mw = ?,
        committed_units = ?,
        started_units = ?,
        stopped_units = ?,
        synced_units = ?
        WHERE scenario_id = ?
        AND project = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?
        AND timepoint = ?;
        """

    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)
