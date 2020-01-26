#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission capacities data
"""

from db.utilities import transmission_capacities

def load_transmission_capacities(io, c, subscenario_input, data_input):
    """
    transmission capacities dictionary
    {transmission_line: {period: (min_mw, max_mw)}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['transmission_existing_capacity_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['transmission_existing_capacity_scenario_id'] == sc_id)]

        tx_line_period_capacities = dict()
        for tl in data_input_subscenario['transmission_line'].unique():
            print(tl)
            tx_line_period_capacities[tl] = dict()
            tx_line_period_capacities_by_zone = data_input_subscenario.loc[
                data_input_subscenario['transmission_line'] == tl]
            for p in tx_line_period_capacities_by_zone['period'].unique():
                p = int(p)
                tx_line_period_capacities[tl][p] = dict()
                tx_line_period_capacities[tl][p] = (float(tx_line_period_capacities_by_zone.loc[
                                                              tx_line_period_capacities_by_zone[
                                                                  'period'] == p, 'min_mw'].iloc[0]),
                                                    float(tx_line_period_capacities_by_zone.loc[
                                                              tx_line_period_capacities_by_zone[
                                                                  'period'] == p, 'max_mw'].iloc[0]))

        transmission_capacities.insert_transmission_capacities(
            io=io, c=c,
            transmission_existing_capacity_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_period_capacities=tx_line_period_capacities
        )
