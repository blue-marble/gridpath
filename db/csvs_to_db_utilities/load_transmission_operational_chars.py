#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission operational chars data
"""

from db.utilities import transmission_operational_chars

def load_transmission_operational_chars(io, c, subscenario_input, data_input):
    """
    transmission operational chars dictionary
    {transmission_line: (operational_type, reactance_ohms}
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

        data_input_subscenario = data_input.loc[
            data_input['id'] == sc_id]

        tx_line_chars = dict()
        for tl in data_input_subscenario['transmission_line'].unique():
            tx_line_chars[tl] = dict()
            tx_line_chars[tl] = (
                data_input_subscenario.loc[
                    data_input_subscenario['transmission_line'] == tl,
                    'operational_type'].iloc[0],
                data_input_subscenario.loc[
                    data_input_subscenario['transmission_line'] == tl,
                    'tx_simple_loss_factor'].iloc[0],
                data_input_subscenario.loc[
                    data_input_subscenario['transmission_line'] == tl,
                    'reactance_ohms'].iloc[0]
            )

        transmission_operational_chars.transmision_operational_chars(
            io=io, c=c,
            transmission_operational_chars_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_chars=tx_line_chars
        )
