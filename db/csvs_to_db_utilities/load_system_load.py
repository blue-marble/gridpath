#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load system load data
"""

from collections import OrderedDict

from db.utilities import system_load

def load_system_static_load(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    Load dictionary has load_zone, stage_id, and then timepoints and data
    {load_zone: {stage_id: {tmp: load_mw}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for sc_id in subscenario_input['load_scenario_id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['load_scenario_id'] == sc_id, 'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['load_scenario_id'] == sc_id, 'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input['load_scenario_id'] == sc_id]

        load = OrderedDict()
        for z in data_input_subscenario['load_zone'].unique():
            print(z)
            zone_load = data_input_subscenario.loc[data_input_subscenario['load_zone'] == z]
            load[z] = OrderedDict()
            for st_id in zone_load['stage_id'].unique():
                zone_stage_load = zone_load.loc[zone_load['stage_id'] == st_id, ['timepoint', 'load_mw']]
                zone_stage_load[['timepoint']] = zone_stage_load[['timepoint']].astype(int)
                load[z][int(st_id)] = zone_stage_load.set_index('timepoint')['load_mw'].to_dict() # make sure column name is not part of dictionary

        # Load data into GridPath database
        system_load.insert_system_static_loads(
            io=io, c=c,
            load_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zone_stage_timepoint_static_loads=load
        )
