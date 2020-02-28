#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission portfolios
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def insert_transmission_portfolio(
        io, c,
        transmission_portfolio_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_cap_types
):
    """

    :param io: 
    :param c: 
    :param transmission_portfolio_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_cap_types: 
    Dictionary with the names of the transmission line as keys and each 
    line's capacity type as value
    :return: 
    """

    # Subscenarios
    subs_data = [(transmission_portfolio_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_portfolios
        (transmission_portfolio_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for tx_line in list(tx_line_cap_types.keys()):
        inputs_data.append(
            (transmission_portfolio_scenario_id,
             tx_line, tx_line_cap_types[tx_line])
        )
    inputs_sql = """
        INSERT INTO inputs_transmission_portfolios
           (transmission_portfolio_scenario_id,
           transmission_line, capacity_type)
           VALUES (?, ?, ?);
        """

    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
