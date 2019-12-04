#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load system reserves data from csvs
"""

from collections import OrderedDict

from db.utilities import system_reserves

def load_system_reserves(io, c, subscenario_input, data_input, reserve_type_input):
    """
    System reserves dictionary has reserves_ba, stage_id, and then timepoints and data
    {load_zone: {stage_id: {tmp: load_mw}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :param reserve_type_input:
    :return:
    """

    #TODO: Include "frequency_response_partial_mw" column for inputs_system_frequency_response table

    for i in subscenario_input.index:
        sc_id = int(subscenario_input[reserve_type_input + '_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input[reserve_type_input + '_scenario_id'] == sc_id)]
        bas = data_input_subscenario[reserve_type_input + '_ba'].unique()

        ba_stage_timepoint_reserve_req_input = OrderedDict()
        for ba in bas:
            print(ba)
            ba_reserve_req = data_input_subscenario.loc[data_input_subscenario[reserve_type_input + '_ba'] == ba]
            ba_stage_timepoint_reserve_req_input[ba] = OrderedDict()
            for st_id in ba_reserve_req['stage_id'].unique():
                ba_stage_reserve_req = \
                    ba_reserve_req.loc[ba_reserve_req['stage_id'] == st_id, ['timepoint', reserve_type_input + '_mw']]
                ba_stage_reserve_req[['timepoint']] = ba_stage_reserve_req[['timepoint']].astype(int)
                ba_stage_timepoint_reserve_req_input[ba][int(st_id)] = \
                    ba_stage_reserve_req.set_index('timepoint')[reserve_type_input + '_mw'].to_dict() # make sure column name is not part of dictionary

        # Load data into GridPath database
        system_reserves.insert_system_reserves(
            io=io, c=c,
            reserve_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            ba_stage_timepoint_reserve_req=ba_stage_timepoint_reserve_req_input,
            reserve_type=reserve_type_input
        )
