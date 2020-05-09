#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Fuels data
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def update_fuels(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_fuels (fuel_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    sql = """
        INSERT OR IGNORE INTO inputs_project_fuels
        (fuel_scenario_id, fuel, co2_intensity_tons_per_mmbtu)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=sql, data=inputs_data)

    c.close()


def update_fuel_prices(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_fuel_prices (
        fuel_price_scenario_id, 
        name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_fuel_prices
        (fuel_price_scenario_id, fuel, period, month, 
        fuel_price_per_mmbtu)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


if __name__ == "__main__":
    pass
