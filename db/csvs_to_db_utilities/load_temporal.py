#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load temporal data
"""

from db.utilities import temporal

def load_temporal(io, c, subscenario_input, data_input):
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
            subscenario_input.loc[subscenario_input['temporal_scenario_id'] == sc_id, 'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['temporal_scenario_id'] == sc_id, 'description'].iloc[0]

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
        if timepoints_df[['previous_stage_timepoint_map']].isnull().values.any():
            print('temporal scenario id ' + str(sc_id) + ' does not have previous stage timepoint map.')
        else:
            timepoints_df[['previous_stage_timepoint_map']] = timepoints_df[['previous_stage_timepoint_map']].astype(
                int)
        if timepoints_df[['spinup_or_lookahead']].isnull().values.any():
            print('temporal scenario id ' + str(sc_id) + ' does not have spinup or lookahead.')
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
        temporal.temporal(
                io=io, c=c,
                temporal_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                periods=periods,
                subproblems=subproblems,
                subproblem_stages=subproblem_stages,
                subproblem_stage_timepoints=timepoints,
                subproblem_horizons=subproblem_horizons,
                subproblem_stage_timepoint_horizons=timepoint_horizons
    )
