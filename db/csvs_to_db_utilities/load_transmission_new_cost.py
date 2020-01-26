#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission new cost data
"""

from db.utilities import transmission_new_cost

def load_transmission_new_cost(io, c, subscenario_input, data_input):
    """
    transmission new cost dictionary
    {transmission_line: (vintage, tx_lifetime_yrs, tx_annualized_real_cost_per_mw_yr}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['transmission_new_cost_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[
            data_input['transmission_new_cost_scenario_id'] == sc_id]

        tx_line_period_lifetimes_costs = dict()
        for tl in data_input_subscenario['transmission_line'].unique():
            print(tl)
            tx_line_period_lifetimes_costs[tl] = dict()
            tx_line_period_lifetimes_costs[tl] = (int(data_input_subscenario.loc[
                                                      data_input_subscenario[
                                                          'transmission_line'] == tl, 'vintage'].iloc[0]),
                                                  float(data_input_subscenario.loc[
                                                      data_input_subscenario[
                                                          'transmission_line'] == tl, 'tx_lifetime_yrs'].iloc[0]),
                                                  float(data_input_subscenario.loc[
                                                      data_input_subscenario[
                                                          'transmission_line'] == tl, 'tx_annualized_real_cost_per_mw_yr'].iloc[0])
                                                  )

        transmission_new_cost.transmision_new_cost(
            io=io, c=c,
            transmission_new_cost_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_period_lifetimes_costs=tx_line_period_lifetimes_costs
        )
