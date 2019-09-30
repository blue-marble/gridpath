#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


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
    subscenario_data = [
        (temporal_scenario_id, scenario_name, scenario_description)
    ]
    subscenario_sql = """
        INSERT INTO subscenarios_temporal
        (temporal_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subscenario_sql,
                          data=subscenario_data)

    print("periods")
    periods_data = []
    for period in periods.keys():
        periods_data.append(
            (temporal_scenario_id, period, periods[period]["discount_factor"],
             periods[period][ "number_years_represented"])
        )
        
    periods_sql = """
        INSERT INTO inputs_temporal_periods
        (temporal_scenario_id, period, discount_factor, 
        number_years_represented)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=periods_sql,
                          data=periods_data)

    print("subproblems")
    # Subproblems
    subproblems_data = []
    for subproblem_id in subproblems:
        subproblems_data.append((temporal_scenario_id, subproblem_id))
        
    subproblems_sql = """
        INSERT INTO inputs_temporal_subproblems
        (temporal_scenario_id, subproblem_id)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subproblems_sql,
                          data=subproblems_data)
    
    print("stages")
    # Stages
    stages_data = []
    for subproblem_id in subproblem_stages.keys():
        for stage in subproblem_stages[subproblem_id]:
            stages_data.append((temporal_scenario_id, subproblem_id, 
                                stage[0], stage[1]))
    stages_sql = """
        INSERT INTO inputs_temporal_subproblems_stages
        (temporal_scenario_id, subproblem_id, stage_id, stage_name)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=stages_sql,
                          data=stages_data)

    # Timepoints
    print("timepoints")
    timepoints_data = []
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
                
                timepoints_data.append(
                    (temporal_scenario_id, subproblem_id, stage_id,
                        timepoint, period, number_of_hours_in_timepoint,
                        timepoint_weight, previous_stage_timepoint_map,
                        spinup_or_lookahead, month, hour_of_day)
                )
    
    timepoints_sql = """
        INSERT INTO inputs_temporal_timepoints
        (temporal_scenario_id, subproblem_id, stage_id, timepoint,
        period, number_of_hours_in_timepoint, timepoint_weight, 
        previous_stage_timepoint_map, 
        spinup_or_lookahead, month, hour_of_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
    
    spin_on_database_lock(conn=io, cursor=c, sql=timepoints_sql,
                          data=timepoints_data)

    print("horizons")
    horizons_data = []
    for subproblem_id in subproblem_horizons.keys():
        for horizon in subproblem_horizons[subproblem_id]:
            balancing_type_horizon = subproblem_horizons[subproblem_id][horizon][
                "balancing_type_horizon"]
            period = subproblem_horizons[subproblem_id][horizon]["period"]
            boundary = subproblem_horizons[subproblem_id][horizon]["boundary"]
            
            horizons_data.append(
                (temporal_scenario_id, subproblem_id, horizon, 
                 balancing_type_horizon, period, boundary)
            )
            
    horizons_sql = """
        INSERT INTO inputs_temporal_horizons
        (temporal_scenario_id, subproblem_id, horizon, 
        balancing_type_horizon, period, boundary)
        VALUES (?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=horizons_sql,
                          data=horizons_data)

    print("horizon timepoints")
    horizon_timepoints_data = []
    for subproblem_id in subproblem_stage_timepoint_horizons.keys():
        for stage_id in subproblem_stage_timepoint_horizons[
                subproblem_id].keys():
            for timepoint in subproblem_stage_timepoint_horizons[
                    subproblem_id][stage_id].keys():
                for horizon_info in subproblem_stage_timepoint_horizons[
                            subproblem_id][stage_id][timepoint]:
                    horizon = horizon_info[0]
                    balancing_type_horizon = horizon_info[1]

                    horizon_timepoints_data.append(
                        (temporal_scenario_id, subproblem_id, stage_id,
                         timepoint, horizon, balancing_type_horizon)
                    )

    horizon_timepoints_sql = """
        INSERT INTO inputs_temporal_horizon_timepoints
        (temporal_scenario_id, subproblem_id, stage_id, timepoint, horizon, 
        balancing_type_horizon)
        VALUES (?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=horizon_timepoints_sql,
                          data=horizon_timepoints_data)


if __name__ == "__main__":
    pass
