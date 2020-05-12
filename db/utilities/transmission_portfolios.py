#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission portfolios
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def insert_transmission_portfolio(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_transmission_portfolios
        (transmission_portfolio_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_transmission_portfolios
           (transmission_portfolio_scenario_id,
           transmission_line, capacity_type)
           VALUES (?, ?, ?);
        """

    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
