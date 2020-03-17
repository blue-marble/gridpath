#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission hurdle rates data
"""

from db.utilities import transmission_hurdle_rates

def load_transmission_hurdle_rates(io, c, subscenario_input, data_input):
    """
    transmission capacities dictionary
    {transmission_line: {period: (hurdle_rate_positive_direction_per_mwh, hurdle_rate_negative_direction_per_mwh)}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['id'] == sc_id)]

        tx_line_period_hurdle_rates = dict()
        for tl in data_input_subscenario['transmission_line'].unique():
            tx_line_period_hurdle_rates[tl] = dict()
            tx_line_period_hurdle_rates_by_tx_line = data_input_subscenario.loc[
                data_input_subscenario['transmission_line'] == tl]
            for p in tx_line_period_hurdle_rates_by_tx_line['period'].unique():
                p = int(p)
                tx_line_period_hurdle_rates[tl][p] = dict()
                tx_line_period_hurdle_rates[tl][p] = (float(tx_line_period_hurdle_rates_by_tx_line.loc[
                                                              tx_line_period_hurdle_rates_by_tx_line[
                                                                  'period'] == p,
                                                              'hurdle_rate_positive_direction_per_mwh'].iloc[0]),
                                                    float(tx_line_period_hurdle_rates_by_tx_line.loc[
                                                              tx_line_period_hurdle_rates_by_tx_line[
                                                                  'period'] == p,
                                                              'hurdle_rate_negative_direction_per_mwh'].iloc[0]))

        transmission_hurdle_rates.insert_transmission_hurdle_rates(
            io=io, c=c,
            transmission_hurdle_rate_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_period_hurdle_rates=tx_line_period_hurdle_rates
        )
