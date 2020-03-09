#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission zones data
"""

from db.utilities import transmission_zones

def load_transmission_zones(io, c, subscenario_input, data_input):
    """
    TODO: correct function docs
    transmission zones dictionary
    {load_zone: {stage_id: {tmp: load_mw}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        tl_sc_id = int(subscenario_input['transmission_load_zone_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['transmission_load_zone_scenario_id'] == tl_sc_id)]

        tx_line_load_zones = dict()
        for tl in data_input_subscenario['transmission_line'].unique():
            tx_line_load_zones[tl] = dict()
            tx_line_load_zones[tl] = (data_input_subscenario.loc[
                                          data_input_subscenario['transmission_line'] == tl, 'load_zone_from'].iloc[0],
                                      data_input_subscenario.loc[
                                          data_input_subscenario['transmission_line'] == tl, 'load_zone_to'].iloc[0])

        transmission_zones.insert_transmission_load_zones(
            io=io, c=c,
            transmission_load_zone_scenario_id=tl_sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_load_zones=tx_line_load_zones
        )


def load_transmission_carbon_cap_zones(io, c, subscenario_input, data_input):
    """
    {tx_line: (carbon_cap_zone, direction, intensity)}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        tl_sc_id = int(subscenario_input[
                           'transmission_carbon_cap_zone_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['transmission_carbon_cap_zone_scenario_id'] == tl_sc_id)]

        tx_line_carbon_cap_zones = dict()
        # TODO: should flag if there are non-unique inputs
        for tl in data_input_subscenario['transmission_line'].unique():
            tx_line_carbon_cap_zones[tl] = (data_input_subscenario.loc[
                                          data_input_subscenario['transmission_line'] == tl, 'carbon_cap_zone'].iloc[0],
                                      data_input_subscenario.loc[
                                          data_input_subscenario[
                                              'transmission_line'] == tl, 'import_direction'].iloc[0],
                                      data_input_subscenario.loc[
                                          data_input_subscenario[
                                              'transmission_line'] == tl, 'tx_co2_intensity_tons_per_mwh'].iloc[0])

        transmission_zones.insert_transmission_carbon_cap_zones(
            io=io, c=c,
            transmission_carbon_cap_zone_scenario_id=tl_sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_carbon_cap_zones=tx_line_carbon_cap_zones
        )
