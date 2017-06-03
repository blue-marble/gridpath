#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Fuels data
"""


def update_fuels(
        io, c,
        fuel_scenario_id,
        scenario_name,
        scenario_description,
        fuel_chars
):
    """
    :param io: 
    :param c: 
    :param fuel_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param fuel_chars: Dictionary with fuel as key that currently only 
    includes values for fuel CO2 intensity
    :return: 
    """
    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_project_fuels (fuel_scenario_id, name,
        description)
        VALUES ({}, '{}', '{}');""".format(
            fuel_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for f in fuel_chars.keys():
        c.execute(
            """INSERT INTO inputs_project_fuels
            (fuel_scenario_id, fuel, co2_intensity_tons_per_mmbtu)
            VALUES ({}, '{}', {});""".format(
                fuel_scenario_id, f, fuel_chars[f]
            )
        )
    io.commit()


def update_fuel_prices(
        io, c,
        fuel_price_scenario_id,
        scenario_name,
        scenario_description,
        fuel_month_prices
):
    """
    
    :param io: 
    :param c: 
    :param fuel_price_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param fuel_month_prices: Nested dictionary with fuel as the first key 
    period as the second, month as the third, and the price by 
    fuel/period/month as values
    :return: 
    """
    print("fuel prices")
    # Subscenario
    c.execute(
        """INSERT INTO subscenarios_project_fuel_prices (
        fuel_price_scenario_id, 
        name,
        description)
        VALUES ({}, '{}', '{}');""".format(
            fuel_price_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for f in fuel_month_prices.keys():
        for p in fuel_month_prices[f].keys():
            for m in fuel_month_prices[f][p].keys():
                c.execute(
                    """INSERT INTO inputs_project_fuel_prices
                    (fuel_price_scenario_id, fuel, period, month, 
                    fuel_price_per_mmbtu)
                    VALUES ({}, '{}', {}, {}, {});""".format(
                        fuel_price_scenario_id, f, p, m,
                        fuel_month_prices[f][p][m]
                    )
                )
    io.commit()


if __name__ == "__main__":
    pass
