#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios
"""
from __future__ import print_function


def temporal(
        io, c,
        temporal_scenario_id,
        scenario_name,
        scenario_description,
        periods,
        subproblems,
        subproblem_stages,
        subproblem_stage_timepoints,
        subproblem_horizons,
        subproblem_stage_timepoint_horizons
):
    """

    :param io:
    :param c:
    :param temporal_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param periods:
    :param subproblems: list of subproblems
    :param subproblem_stages: dictionary with subproblems as keys and a list of
        tuples containing (stage_id, stage_name) as values
    :param subproblem_stage_timepoints: dictionary with subproblems as first
        key, stage_id as second key, timepoint as third key, and the various
        timepoint params as a dictionary value for each timepoint (with the
        name of the param as key and its value as value)
    :param subproblem_horizons: dictionary with subproblems as the first
        key, horizons as the second key, and a dictionary containing the
        horizon params (balancing_type_horizon, period, and boundary) as the
        value for each horizon
    :param subproblem_stage_timepoint_horizons: dictionary with subproblem IDs
        as the first key, stage IDs as the second key, the timepoint as the
        third key, and list of tuple with the (horizon,
        balancing_type_horizons) that the timepoint belongs to
    """

    # Create subscenario
    c.execute(
        """INSERT INTO subscenarios_temporal
        (temporal_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            temporal_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    print("periods")
    for period in periods.keys():
        c.execute(
            """INSERT INTO inputs_temporal_periods
            (temporal_scenario_id, period, discount_factor,
            number_years_represented)
            VALUES ({}, {}, {}, {});""".format(
                temporal_scenario_id, period,
                periods[period]["discount_factor"],
                periods[period]["number_years_represented"]
            )
        )
    io.commit()

    print("subproblems")
    # Subproblems
    for subproblem_id in subproblems:
        c.execute(
            """INSERT INTO inputs_temporal_subproblems
            (temporal_scenario_id, subproblem_id)
            VALUES ({}, {});""".format(
                temporal_scenario_id, subproblem_id
            )
        )
    io.commit()

    print("stages")
    # Stages
    for subproblem_id in subproblem_stages.keys():
        for stage in subproblem_stages[subproblem_id]:
            c.execute(
                """INSERT INTO inputs_temporal_subproblems_stages
                (temporal_scenario_id, subproblem_id, stage_id, stage_name)
                VALUES ({}, {}, {}, '{}')""".format(
                    temporal_scenario_id, subproblem_id, stage[0], stage[1]
                )
            )
    io.commit()

    # Timepoints
    print("timepoints")
    for subproblem_id in subproblem_stage_timepoints.keys():
        for stage_id in subproblem_stage_timepoints[subproblem_id].keys():
            for timepoint in \
                    subproblem_stage_timepoints[subproblem_id][stage_id].keys():
                timepoint_dict = \
                    subproblem_stage_timepoints[subproblem_id][stage_id][timepoint]
                period = timepoint_dict["period"]
                number_of_hours_in_timepoint = \
                    timepoint_dict["number_of_hours_in_timepoint"]
                timepoint_weight = timepoint_dict["timepoint_weight"]
                previous_stage_timepoint_map = \
                    timepoint_dict["previous_stage_timepoint_map"]
                spinup_or_lookahead = timepoint_dict["spinup_or_lookahead"]
                month = timepoint_dict["month"]
                hour_of_day = timepoint_dict["hour_of_day"]
                c.execute(
                    """INSERT INTO inputs_temporal_timepoints
                    (temporal_scenario_id, subproblem_id, stage_id, timepoint,
                    period, number_of_hours_in_timepoint, timepoint_weight, 
                    previous_stage_timepoint_map, 
                    spinup_or_lookahead, month, hour_of_day)
                    VALUES ({}, {}, {},  {}, {}, {}, {}, {}, {}, {}, {});"""
                    .format(
                        temporal_scenario_id, subproblem_id, stage_id,
                        timepoint, period, number_of_hours_in_timepoint,
                        timepoint_weight, previous_stage_timepoint_map,
                        spinup_or_lookahead, month, hour_of_day
                    )
                )
    io.commit()

    print("horizons")
    for subproblem_id in subproblem_horizons.keys():
        for horizon in subproblem_horizons[subproblem_id]:
            balancing_type_horizon = subproblem_horizons[subproblem_id][horizon][
                "balancing_type_horizon"]
            period = subproblem_horizons[subproblem_id][horizon]["period"]
            boundary = subproblem_horizons[subproblem_id][horizon]["boundary"]
            c.execute(
                """INSERT INTO inputs_temporal_horizons
                (temporal_scenario_id, subproblem_id, horizon, 
                balancing_type_horizon, period, boundary)
                VALUES ({}, {}, {}, '{}', {}, '{}');""".format(
                    temporal_scenario_id, subproblem_id, horizon,
                    balancing_type_horizon, period, boundary
                )
            )
    io.commit()

    print("horizon timepoints")
    for subproblem_id in subproblem_stage_timepoint_horizons.keys():
        for stage_id in subproblem_stage_timepoint_horizons[
                subproblem_id].keys():
            for timepoint in subproblem_stage_timepoint_horizons[
                    subproblem_id][stage_id].keys():
                for horizon_info in subproblem_stage_timepoint_horizons[
                            subproblem_id][stage_id][timepoint]:
                    horizon = horizon_info[0]
                    balancing_type_horizon = horizon_info[1]
                    c.execute("""INSERT INTO 
                    inputs_temporal_horizon_timepoints
                    (temporal_scenario_id, subproblem_id, stage_id, 
                    timepoint, horizon, balancing_type_horizon)
                    VALUES ({}, {}, {}, {}, {}, '{}')""".format(
                        temporal_scenario_id, subproblem_id, stage_id,
                        timepoint, horizon, balancing_type_horizon
                    ))
    io.commit()


if __name__ == "__main__":
    pass
