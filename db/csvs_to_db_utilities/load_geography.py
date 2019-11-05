#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load geography data
"""

from collections import OrderedDict

from db.utilities import geography

def load_geography_load_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :return:
    """

    subscenario_input = OrderedDict(sorted(subscenario_input.items()))

    for sub_id in subscenario_input.keys():
        print('load zones')
        print(subscenario_input[sub_id]['name'])
        print(subscenario_input[sub_id]['description'])

        data_input_sub = data_input.loc[data_input['load_zone_scenario_id'] == sub_id]
        load_zones = data_input_sub['load_zone'].to_list()
        load_zone_overgen_penalties = dict(zip(data_input_sub.load_zone, data_input_sub.overgeneration_penalty_per_mw))
        load_zone_unserved_energy_penalties = dict(
            zip(data_input_sub.load_zone, data_input_sub.unserved_energy_penalty_per_mw))

        # Load data into GridPath database
        geography.geography_load_zones(
            io=io, c=c,
            load_zone_scenario_id=sub_id,
            scenario_name=subscenario_input[sub_id]['name'],
            scenario_description=subscenario_input[sub_id]['description'],
            zones=load_zones,
            zone_overgen_penalties=load_zone_overgen_penalties,
            zone_unserved_energy_penalties=load_zone_unserved_energy_penalties
    )