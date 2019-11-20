#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.


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

    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
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


def determine_relevant_timepoints_forward(mod, g, tmp, min_time):
    """
    Find relevant timepoints for determining the startup power during a certain
    tmp.

    Example:
    1. The startup duration is 3 hours and timepoints have an hourly resolution.
    For tmp 15, this means the relevant timepoints are 16, 17, 18, since any
    any starts in tmps 16, 17, or 18 will have an impact on timepoint 15. For
    instance, if you start in timepoint 18, it means there weill be 3-h startup
    trajectory leading to that, starting in timepoint 15 and ending in timepoint
    17. The power outputs at the end of each timepoint will be respectively
    0.33 * Pmin, 0.66 * Pmin and Pmin for tmps 15, 16, 17.
    2. The startup duration is 3 hours and timepoints have a 4-hour resolution.
    For tmp 15, this means that the relevant timepoint is just tmp 16, with
    a power output of Pmin.
    (or nothing at all??) - NO

        # EXAMPLE:
        # unit starts in tmp = 15, so the runup will happen during tmp = 14
        # tmp = 14 has duration of 3 hours and startup
        # duration is only 2 hours. That means tmp = 14 will contain the full
        # startup and output will be zero in # tmp = 13 and can be anything in
        # tmp = 15.
        # if we're checking relevant tmps for tmp = 14, we should at least get
        # tmp = 15 returned.

    Note that "starting" a unit during a timepoint means that the unit will be
    fully online for the first time in that timepoint, with fully controllable
    power output, but it might have a startup trajectory during the previous
    timepoints to get there.

    Note 2: We need to end at Pmin at the end of a startup to match constraint
    (6) in Morales-Espana. Our power expression is different from their energy
    expression, and the power needs to come from here rather than the Pmin
    * commitment since commitment in this timepoint (the one before the timepoint
    in which the unit binary start variable is 1) is zero.

    Note 3: in extreme cases, this might lead you to provide a lot of power for
    a long duration when it might not have been exactly necessary. E.g. startup-
    duration is 1 hour, but the timepoint duration is 10 hours. To start in
    timepoint x, you will need to end at Pmin at timepiont x-1. But since we
    don't do energy vs. power, we will see this as providing pmin for the
    whole 10-hours from an energy perspective.

    :param mod:
    :param g:
    :param tmp:
    :param min_time: duration of the startup trajectory in hours
    :return: a list of timepoints that affect the startup power output for
    the given timepoint.


    """

    # If we are on the last timepoint on a linear horizon,  no future starts
    # affect the units output so there are no relevant timepoints.
    if tmp == mod.last_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        relevant_tmps = []
        # TODO: could add hours_from_tmps to help calculations
    else:
        # A start in the next timepoint will always affect the startup power in
        # the current timepoint, regardless of startup times and timepoint
        # durations
        relevant_tmp = mod.next_timepoint[tmp, mod.balancing_type_project[g]]
        relevant_tmps = [relevant_tmp]

        # If we haven't exceed the startup duration yet, a startup in the
        # next next timepoint would affect the current timepoint, so we need
        # to add it to our list.
        hours_from_tmp = mod.number_of_hours_in_timepoint[relevant_tmp]
        while hours_from_tmp < min_time:
            # In a 'linear' horizon setting, once we reach the last timepoint
            # of the horizon, we break out of the loop since there are no more
            # timepoints to consider
            if mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                    == "linear" \
                    and relevant_tmp == \
                    mod.last_horizon_timepoint[
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
            # Otherwise, we move on to the relevant timepoint's next
            # timepoint and will add that timepoint's duration to
            # hours_from_tmp
            else:
                relevant_tmp = mod.next_timepoint[
                    relevant_tmp, mod.balancing_type_project[g]]
                hours_from_tmp += \
                    mod.number_of_hours_in_timepoint[relevant_tmp]
                relevant_tmps.append(relevant_tmp)

    return relevant_tmps


def determine_relevant_timepoints_startup(mod, g, tmp, t1, t2):
    """
    Find relevant timepoints within t1 hours and t2 hours from tmp
    If the unit has been down in any of these relevant timepoints, we can
    activate the startup variable of the associated startup type.

    See constraint (1) in Morales-Espana 2013c
    :param mod:
    :param g:
    :param tmp:
    :param t1:
    :param t2:
    :return:
    """

    # TODO: think of what happens when you reach tmp in circular setting or
    #  when you reach first tmp in linear setting
    # --> this means you are less than TSU,l+1 away from start, so constraint
    # should not hold for the tmp, since we have no way to know whether unit
    # was down longer than TSU,l+1 hours, which would push it to be a colder
    # start

    relevant_tmps = []

    # TODO: in timepoints.py, for each timepoint calculate number of hours from
    #  start of horizon (if there is a start, doesn't apply if circular)

    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        pass  # no relevant timepoints
    else:
        current_tmp = mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
        hours_from_tmp = mod.number_of_hours_in_timepoint[current_tmp]

        # If we haven't exceeded t2 hours from tmp yet, we keep going back to
        # previous timepoints.
        while hours_from_tmp < t2:
            # if we are within [t1-t2) hours from tmp, add tmp to list
            if hours_from_tmp >= t1:
                relevant_tmps.append(current_tmp)

            # In a 'linear' horizon setting, if we reach the first timepoint
            # of the horizon, it means we are within t2 hrs from the start of
            # the horizon, and the constraint should be skipped, so we return an
            # empty list of tmps.
            if mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                    == "linear" \
                    and current_tmp == \
                    mod.first_horizon_timepoint[
                        mod.horizon[tmp, mod.balancing_type_project[g]]]:
                relevant_tmps = []
                break
            # In a 'circular' horizon setting, if we reach timepoint *tmp*, it
            # means the horizon length is shorter than t2, and the constraint
            # should be skipped, so we return an empty list of tmps.
            elif mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                    == "circular" \
                    and current_tmp == tmp:
                relevant_tmps = []
                break

            # Otherwise, we move on to the current timepoint's previous
            # timepoint and will add that timepoint's duration to hours_from_tmp
            else:
                current_tmp = mod.previous_timepoint[
                    current_tmp, mod.balancing_type_project[g]]
                hours_from_tmp += mod.number_of_hours_in_timepoint[current_tmp]

    return relevant_tmps
