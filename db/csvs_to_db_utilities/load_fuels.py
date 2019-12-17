#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load fuels data from csvs
"""

from db.utilities import fuels


def load_fuels(io, c, subscenario_input, data_input):
    """
    fuels dictionary
    {fuel: co2_intensity_tons_per_mmbtu}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['fuel_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['fuel_scenario_id'] == sc_id)]

        fuel_chars = dict()
        fuel_chars = data_input_subscenario[['fuel', 'co2_intensity_tons_per_mmbtu']].set_index(
            'fuel')['co2_intensity_tons_per_mmbtu'].to_dict()

        fuels.update_fuels(
            io=io, c=c,
            fuel_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            fuel_chars=fuel_chars
        )

def load_fuel_prices(io, c, subscenario_input, data_input):
    """
    Fuel prices dictionary
    {fuel: {period: {month: fuel_price_per_mmbtu}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['fuel_price_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['fuel_price_scenario_id'] == sc_id)]

        fuel_month_prices = dict()
        for f in data_input_subscenario['fuel'].unique():
            print(f)
            fuel_month_prices[f] = dict()
            fuel_month_prices_by_fuel = data_input_subscenario.loc[data_input_subscenario['fuel'] == f]
            for p in fuel_month_prices_by_fuel['period'].unique():
                p = int(p)
                fuel_month_prices[f][p] = dict()
                fuel_month_prices_by_fuel_period = fuel_month_prices_by_fuel.loc[
                    fuel_month_prices_by_fuel['period'] == p]
                for m in fuel_month_prices_by_fuel_period['month'].unique():
                    m = int(m)
                    fuel_month_prices[f][p][m] = dict()
                    fuel_month_prices[f][p][m] = float(fuel_month_prices_by_fuel_period.loc[
                        fuel_month_prices_by_fuel_period['month'] == m, 'fuel_price_per_mmbtu'].iloc[0])

        # Load data into GridPath database
        fuels.update_fuel_prices(
            io=io, c=c,
            fuel_price_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            fuel_month_prices=fuel_month_prices
        )
