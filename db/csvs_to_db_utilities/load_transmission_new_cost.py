#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load transmission new cost data
"""

from db.utilities import transmission_new_cost


def recur_dictify(frame):
    """
    Converts DataFrame to nested dictionary using recursion.

    :param frame:
    :return:
    """
    if len(frame.columns) == 1:
        if frame.values.size == 1:
            return frame.values[0][0]
        return frame.values.squeeze()
    grouped = frame.groupby(frame.columns[0])
    d = {k: recur_dictify(g.iloc[:, 1:]) for k, g in grouped}
    return d


def load_transmission_new_cost(io, c, subscenario_input, data_input):
    """
    transmission new cost dictionary
    {transmission_line: {vintage:
        (tx_lifetime_yrs, tx_annualized_real_cost_per_mw_yr)}}
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

        key_cols = ["transmission_line", "period"]
        value_cols = ["tx_lifetime_yrs", "tx_annualized_real_cost_per_mw_yr"]

        df = data_input_subscenario.groupby(key_cols)[value_cols].apply(
            lambda x: x.values.tolist()[0]).to_frame().reset_index()
        tx_line_period_lifetimes_costs = recur_dictify(df)

        transmission_new_cost.transmision_new_cost(
            io=io, c=c,
            transmission_new_cost_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            tx_line_period_lifetimes_costs=tx_line_period_lifetimes_costs
        )
