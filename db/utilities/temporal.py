#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios.
"""

import os.path
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock


def temporal(
        io, c,
        temporal_scenario_id,
        scenario_name,
        scenario_description,
        periods,
        subscenario_subproblems,
        subscenario_subproblem_stages,
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
    :param subscenario_subproblems: list of tuples (subscenario_id,
        subproblem_id)
    :param subscenario_subproblem_stages: list of tuples (subscenario_id,
        subproblem_id, stage_id)
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

    # Subproblems
    subproblems_sql = """
        INSERT INTO inputs_temporal_subproblems
        (temporal_scenario_id, subproblem_id)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subproblems_sql,
                          data=subscenario_subproblems)

    # Stages
    # TODO: stage_name not currently included; decide whether to keep this
    #  column in the database and how to import data for it if we do want it
    stages_sql = """
        INSERT INTO inputs_temporal_subproblems_stages
        (temporal_scenario_id, subproblem_id, stage_id)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=stages_sql,
                          data=subscenario_subproblem_stages)

    # Periods
    periods_sql = """
        INSERT INTO inputs_temporal_periods
        (temporal_scenario_id, period, discount_factor, 
        number_years_represented)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=periods_sql,
                          data=periods)

    # Timepoints
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


def load_temporal_deprecate(io, c, subscenario_input, data_input):
    """
    data_input is a dictionary with all temporal csv tables
    subproblems = [subproblems]
    subproblems_stages = {subproblem_id: [(stage_id, stage_name)]}
    periods = {period: {number_years_represented, discount_factor}}
    subproblem_horizons = {subproblem_id: {horizon: {period, balancing_type_horizon, boundary}}}
    timepoints = {subproblem_id: {stage_id: {timepoint: {period, number_of_hours_in_timepoint,
                    timepoint_weight, hour_of_day, previous_stage_timepoint_map, spinup_or_lookahead}}}}
    timepoint_horizons = {subproblem_id: {stage_id: {timepoint: {horizon, balancing_type}}}}

    :param io:
    :param c:
    :param subscenario_input:
    :param data_input: dictionary with 6 temporal csv tables
    :return:
    """

    temporal_tables = data_input.keys()

    for sc_id in subscenario_input['temporal_scenario_id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['temporal_scenario_id']
                                  == sc_id, 'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['temporal_scenario_id']
                                  == sc_id, 'description'].iloc[0]

        data_input_subscenario = {}
        for tbl in temporal_tables:
            data_input_subscenario[tbl] = data_input[tbl].loc[data_input[tbl]['temporal_scenario_id'] == sc_id]

        ## SUBPROBLEMS ##
        subproblems_df = data_input_subscenario['subproblems']
        subproblems_df[['subproblem_id']] = subproblems_df[['subproblem_id']].astype(int)
        subproblems = subproblems_df['subproblem_id'].to_list()

        ## STAGES ##
        subproblem_stages = {}
        subproblem_stages_df = data_input_subscenario['subproblems_stages']
        for sub_id in subproblems:
            subproblem_stages_df_subproblem = subproblem_stages_df.loc[subproblem_stages_df['subproblem_id'] == sub_id]
            stages_list = []
            for st_id in subproblem_stages_df_subproblem['stage_id'].to_list():
                stages_list.append((st_id, subproblem_stages_df_subproblem.loc[
                    subproblem_stages_df_subproblem['stage_id'] == st_id, 'stage_name'].iloc[0]))
            subproblem_stages[sub_id] = stages_list

        ## PERIODS ##
        periods = dict(dict())
        periods_df = data_input_subscenario['periods']
        periods_df = periods_df.set_index('period')
        periods = periods_df[['discount_factor', 'number_years_represented']].to_dict(orient='index')

        ## HORIZONS ##
        subproblem_horizons = dict()
        subproblem_horizons_df = data_input_subscenario['horizons']
        subproblem_horizons_df[['horizon']] = subproblem_horizons_df[['horizon']].astype(int)
        subproblem_horizons_df[['period']] = subproblem_horizons_df[['period']].astype(int)
        for sub_id in subproblem_stages.keys():
            subproblem_horizons[sub_id] = dict()
            subproblem_horizons_df_by_subproblems = subproblem_horizons_df.loc[subproblem_horizons_df['subproblem_id'] == sub_id,
                                                      ['horizon', 'balancing_type_horizon', 'period', 'boundary']]
            subproblem_horizons[sub_id] = subproblem_horizons_df_by_subproblems[[
                    'horizon', 'balancing_type_horizon', 'period', 'boundary']].set_index(['horizon']).to_dict(orient='index')

        ## TIMEPOINTS
        timepoints = dict()
        timepoints_df = data_input_subscenario['timepoints']
        timepoints_df[['timepoint']] = timepoints_df[['timepoint']].astype(int)
        timepoints_df[['period']] = timepoints_df[['period']].astype(int)
        timepoints_df[['number_of_hours_in_timepoint']] = timepoints_df[['number_of_hours_in_timepoint']].astype(int)
        timepoints_df[['timepoint_weight']] = timepoints_df[['timepoint_weight']].astype(float)
        timepoints_df[['month']] = timepoints_df[['month']].astype(int)
        timepoints_df[['hour_of_day']] = timepoints_df[['hour_of_day']].astype(float)
        # TODO: what should the validation behavior be here
        if timepoints_df[['previous_stage_timepoint_map']].isnull().values.any():
            # print('temporal scenario id ' + str(sc_id) + ' does not have previous stage timepoint map.')
            pass
        else:
            timepoints_df[['previous_stage_timepoint_map']] = timepoints_df[['previous_stage_timepoint_map']].astype(
                int)
        if timepoints_df[['spinup_or_lookahead']].isnull().values.any():
            # print('temporal scenario id ' + str(sc_id) + ' does not have spinup or lookahead.')
            pass
        else:
            timepoints_df[['spinup_or_lookahead']] = timepoints_df[['spinup_or_lookahead']].astype(
                int)

        for sub_id in subproblem_stages.keys():
            timepoints[sub_id] = dict()
            timepoints_df_by_subproblem = timepoints_df.loc[timepoints_df['subproblem_id'] == sub_id]
            for st_id in timepoints_df_by_subproblem['stage_id'].unique():
                st_id = int(st_id)
                timepoints[sub_id][st_id] = dict()
                timepoints_df_by_subproblem_stage = timepoints_df_by_subproblem.loc[
                    timepoints_df_by_subproblem['stage_id'] == st_id]
                timepoints[sub_id][st_id] = timepoints_df_by_subproblem_stage[[
                    'timepoint', 'period', 'number_of_hours_in_timepoint',
                    'timepoint_weight', 'month', 'hour_of_day',
                    'previous_stage_timepoint_map', 'spinup_or_lookahead']].set_index(['timepoint']).to_dict(orient='index')

        ## HORIZON TIMEPOINTS ##
        # This code searches for each row to match subproblem id, stage id, timepoint to ensure there is no mismatch
        # But this may slow down the script. Another way is to just add rows of dataframe to dictionary
        # assuming user has valid data. See alternate code below.
        timepoint_horizons = dict()
        timepoint_horizons_df = data_input_subscenario['horizon_timepoints']
        for sub_id in timepoints.keys():
            timepoint_horizons[sub_id] = dict()
            for st_id in timepoints[sub_id].keys():
                timepoint_horizons[sub_id][st_id] = dict()
                for tmp in timepoints[sub_id][st_id].keys():
                    horizon = timepoint_horizons_df.loc[
                        (timepoint_horizons_df['subproblem_id'] == sub_id)
                        & (timepoint_horizons_df['stage_id'] == st_id)
                        & (timepoint_horizons_df['timepoint'] == tmp),
                        'horizon'].astype(int)

                    balancing_type = timepoint_horizons_df.loc[
                        (timepoint_horizons_df['subproblem_id'] == sub_id)
                        & (timepoint_horizons_df['stage_id'] == st_id)
                        & (timepoint_horizons_df['timepoint'] == tmp),
                        'balancing_type_horizon']

                    timepoint_horizons[sub_id][st_id][tmp] = list(
                        zip(horizon, balancing_type))

        # Load data into GridPath database
        temporal(
                io=io, c=c,
                temporal_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                periods=periods,
                subscenario_subproblems=subproblems,
                subproblem_stages=subproblem_stages,
                subproblem_stage_timepoints=timepoints,
                subproblem_horizons=subproblem_horizons,
                subproblem_stage_timepoint_horizons=timepoint_horizons
    )


def load_from_csvs(conn, subscenario_directory):
    """

    :param conn:
    :param subscenario_directory:
    :return:
    """
    # Required input files
    description_file = os.path.join(subscenario_directory, "description.txt")
    raw_data_file = os.path.join(subscenario_directory, "raw_data.csv")
    periods_file = os.path.join(subscenario_directory, "periods.csv")
    horizons_file = os.path.join(subscenario_directory, "horizons.csv")

    # Get subscenario ID, name, and description
    # The subscenario directory must start with an integer for the
    # subscenario_id followed by "_" and then the subscenario name
    # The subscenario description must be in the description.txt file under
    # the subscenario directory
    directory_basename = os.path.basename(subscenario_directory)
    subscenario_id = int(directory_basename.split("_")[0])
    subscenario_name = directory_basename.split("_")[1]
    with open(description_file, "r") as f:
        subscenario_description = f.read()

    # Load timepoints data into Pandas dataframe
    # The subproblem, stage, and horizon information is also contained here
    tmp_df = pd.read_csv(raw_data_file, delimiter=",")

    # SUBPROBLEMS
    # Get the data for the inputs_temporal_subproblems table
    subproblems = set(tmp_df["subproblem_id"].to_list())
    subscenario_subproblems = [
        (subscenario_id, subproblem_id) for subproblem_id in subproblems
    ]

    # STAGES
    # TODO: stage_name not currently included; decide whether to keep this
    #  column in the database and how to import data for it if we do want it
    # Get the data for the inputs_temporal_subproblems_stages table
    subproblem_stages = set(zip(tmp_df["subproblem_id"], tmp_df["stage_id"]))
    subscenario_subproblem_stages = [
        (subscenario_id, ) + subpr_stage for subpr_stage in subproblem_stages
    ]

    # PERIODS
    # Load periods data into Pandas dataframe
    period_df = pd.read_csv(periods_file, delimiter=",")

    # Check if the periods are unique
    if period_df['period'].duplicated().any():
        warnings.warn("Duplicate periods found in periods.csv. Periods must "
                      "be unique.")

    # Check if the set of periods in periods.csv is the same as the set of
    # periods assigned to timepoints in timepoints.csv.
    tmp_periods = set(tmp_df["period"].tolist())
    period_set = set(period_df["period"].tolist())

    if tmp_periods != period_set:
        warnings.warn("The set of periods in timepoints.csv and periods.csv "
                      "are not the same. Check your data.")

    periods = [tuple(x) for x in period_df.to_records(index=False)]

    # HORIZONS
    # Load horizons data into Pandas dataframe
    horizon_df = pd.read_csv(horizons_file, delimiter=",")





if __name__ == "__main__":
    load_from_csvs(None, "/Users/ana/dev/gridpath_dev/db/csvs_test_examples"
                         "/temporal/1_1horizon_1period")
