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


def determine_relevant_timepoints_forward(mod, g, tmp, startup_time):
    """
    Get the list of future timepoints for which a start in that timepoint would
    lead to startup power in timepoint *tmp*. The longer the startup duration,
    the longer the lists of relevant timepoints, since the startup trajectory
    stretches many timepoints. This list is used when calculating the startup
    power expression in the dispatchable_binary_commit module.

    The returned list doesn't include the timepoint right after timepoint *tmp*,
    even though a start in the next timepoint would certainly lead to some type
    of startup power in the timepoint before it. This is because another
    constraint will already govern the startup power for that timepoint.

    Examples:
    1. The startup duration is 3 hours and timepoints have an hourly resolution.
    For tmp 15, this means the relevant timepoints are 16, 17, 18, since any
    any starts in tmps 16, 17, or 18 will have an impact on timepoint 15 (note:
    timepoint 16 will be excluded, see above). E.g. if you start in timepoint
    17, you will have a 3-h startup trajectory that starts in timepoint 14 and
    ends in timepoint 16.
    2. The startup duration is 3 hours and timepoints have a 4-hour resolution.
    For tmp 15, this means that the relevant timepoint is just tmp 16, which
    will be excluded since it's the next timepoint from tmp 15 (see above).

    Note 1: "starting" a unit during a timepoint means that the unit will be
    fully online for the first time in that timepoint, with fully controllable
    power output, but it might have a startup trajectory during the previous
    timepoints to get there.

    Note 2: We need to end at Pmin at the end of a startup to match constraint
    (6) in Morales-Espana. Our power expression is different from their energy
    expression, and the power needs to come from here rather than the Pmin
    * commitment since commitment in this timepoint (the one before the
    timepoint in which the unit binary start variable is 1) is zero.

    Note 3: in extreme cases, this might lead you to provide a lot of power for
    a long duration when it might not have been exactly necessary. E.g. startup-
    duration is 1 hour, but the timepoint duration is 10 hours. To start in
    timepoint x, you will need to end at Pmin at timepiont x-1. But since we
    don't do energy vs. power, we will see this as providing pmin for the
    whole 10-hours from an energy perspective.

    :param mod:
    :param g:
    :param tmp:
    :param startup_time: duration of the startup trajectory in hours
    :return: a list of timepoints that affect the startup power output for
    the given timepoint. List of timepoines is ordered chronologically (but
    could wrap around the horizon if circular horizon boundary).


    """

    relevant_tmps = []
    hours_from_tmp = 0

    # 1. Move ahead to the timepoint 2 timepoints away from *tmp*. We skip the
    # timepoint right after *tmp* since the provide_power_operations_rule
    # already governs the startup power of that timepoint.

    # If we are on the last timepoint on a linear horizon, no future starts
    # affect the units output so there are no relevant timepoints.
    if tmp == mod.last_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return relevant_tmps
    relevant_tmp = mod.next_timepoint[tmp, mod.balancing_type_project[g]]
    hours_from_tmp += mod.number_of_hours_in_timepoint[relevant_tmp]

    if relevant_tmp == mod.last_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return relevant_tmps
    relevant_tmp = mod.next_timepoint[
        relevant_tmp, mod.balancing_type_project[g]]
    hours_from_tmp += mod.number_of_hours_in_timepoint[relevant_tmp]
    relevant_tmps = [relevant_tmp]

    # 2. If we haven't exceed the startup duration yet, a startup in the
    # next next timepoint would affect the current timepoint, so we need
    # to add it to our list.
    while hours_from_tmp < startup_time:
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
        # Otherwise, we move on to the relevant timepoint's next timepoint
        # and will add that timepoint's duration to hours_from_tmp
        else:
            relevant_tmp = mod.next_timepoint[
                relevant_tmp, mod.balancing_type_project[g]]
            hours_from_tmp += mod.number_of_hours_in_timepoint[relevant_tmp]
            relevant_tmps.append(relevant_tmp)

    # TODO: could add hours_from_tmps to help calculations
    return relevant_tmps


def determine_relevant_timepoints_startup(mod, g, tmp, t1, t2):
    """
    Get the list of past timepoints within t1-t2 hours from timepoint *tmp*.

    If the unit has been down in any of these timepoints, we can activate the
    the startup variable of the associated startup type for timepoint *tmp*
    (but only if the unit is actually starting in timepoint *tmp*; see
    startup_type_constraint_rule in dispatchable_binary_commit.py).

    See constraint (7) in Morales-Espana 2017 or constraint (1) in
    Morales-Espana 2013c.
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

    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return relevant_tmps  # no relevant timepoints

    relevant_tmp = mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
    hours_from_tmp = mod.number_of_hours_in_timepoint[relevant_tmp]

    # If we haven't exceeded t2 hours from tmp yet, we keep going back to
    # previous timepoints.
    while hours_from_tmp < t2:
        # if we are within [t1-t2) hours from tmp, add tmp to list
        if hours_from_tmp >= t1:
            relevant_tmps.append(relevant_tmp)

        # In a 'linear' horizon setting, if we reach the first timepoint
        # of the horizon, it means we are within t2 hrs from the start of
        # the horizon, and the constraint should be skipped, so we return an
        # empty list of tmps.
        if mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear" \
                and relevant_tmp == \
                mod.first_horizon_timepoint[
                    mod.horizon[tmp, mod.balancing_type_project[g]]]:
            return []
        # In a 'circular' horizon setting, if we reach timepoint *tmp*, it
        # means the horizon length is shorter than t2, and the constraint
        # should be skipped, so we return an empty list of tmps.
        elif mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "circular" \
                and relevant_tmp == tmp:
            return []

        # Otherwise, we move on to the current timepoint's previous
        # timepoint and will add that timepoint's duration to hours_from_tmp
        else:
            relevant_tmp = mod.previous_timepoint[
                relevant_tmp, mod.balancing_type_project[g]]
            hours_from_tmp += mod.number_of_hours_in_timepoint[relevant_tmp]

    return relevant_tmps
