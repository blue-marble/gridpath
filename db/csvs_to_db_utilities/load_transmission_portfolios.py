#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission portfolios data
"""

from db.utilities import transmission_portfolios

def load_transmission_portfolios(io, c, subscenario_input, data_input):
    """
    transmission portfolios dictionary
    {transmission_line: capacity_type}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['transmission_portfolio_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['transmission_portfolio_scenario_id'] == sc_id)]

        tx_line_cap_types = dict()
        tx_line_cap_types = data_input_subscenario[['transmission_line', 'capacity_type']].dropna().set_index(
            'transmission_line')['capacity_type'].to_dict()

        transmission_portfolios.insert_transmission_portfolio(
            io=io, c=c,
            transmission_portfolio_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_cap_types=tx_line_cap_types
        )

