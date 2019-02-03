#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission portfolios
"""
from __future__ import print_function


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
    print("transmission portfolios")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_transmission_portfolios
        (transmission_portfolio_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            transmission_portfolio_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for tx_line in list(tx_line_cap_types.keys()):
        c.execute(
            """INSERT INTO inputs_transmission_portfolios
               (transmission_portfolio_scenario_id,
               transmission_line, capacity_type)
               VALUES ({}, '{}', '{}');""".format(
                transmission_portfolio_scenario_id,
                tx_line, tx_line_cap_types[tx_line]
        )
        )
    io.commit()
