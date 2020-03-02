#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Fuels data
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


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
    subs_data = [(fuel_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_fuels (fuel_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    data = []
    for f in list(fuel_chars.keys()):
        data.append((fuel_scenario_id, f, fuel_chars[f]))
    sql = """
        INSERT INTO inputs_project_fuels
        (fuel_scenario_id, fuel, co2_intensity_tons_per_mmbtu)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=sql, data=data)


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

    # Subscenario
    subs_data = [(fuel_price_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_fuel_prices (
        fuel_price_scenario_id, 
        name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for f in list(fuel_month_prices.keys()):
        for p in list(fuel_month_prices[f].keys()):
            for m in list(fuel_month_prices[f][p].keys()):
                inputs_data.append((fuel_price_scenario_id, f, p, m,
                             fuel_month_prices[f][p][m]))
    inputs_sql = """
        INSERT INTO inputs_project_fuel_prices
        (fuel_price_scenario_id, fuel, period, month, 
        fuel_price_per_mmbtu)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
