#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission operational chars
"""

from db.common_functions import spin_on_database_lock


def transmision_operational_chars(
        io, c,
        transmission_operational_chars_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_chars
):
    """

    :param io: 
    :param c: 
    :param transmission_portfolio_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_chars:
        Dictionary with the names of the transmission line as keys and tuples
        containing the operational type, simple loss factor, and the reactance in
        ohms
    :return: 
    """

    # Subscenarios
    subs_data = [(transmission_operational_chars_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_operational_chars
        (transmission_operational_chars_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for tx_line in list(tx_line_chars.keys()):
        inputs_data.append(
            (transmission_operational_chars_scenario_id,
             tx_line,
             tx_line_chars[tx_line][0],
             tx_line_chars[tx_line][1],
             tx_line_chars[tx_line][2])
        )
    inputs_sql = """
        INSERT INTO inputs_transmission_operational_chars
        (transmission_operational_chars_scenario_id,
        transmission_line, operational_type, 
        tx_simple_loss_factor, reactance_ohms)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
