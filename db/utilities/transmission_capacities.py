#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission load zones
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def insert_transmission_capacities(
        io, c,
        transmission_existing_capacity_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_period_capacities
):
    """

    :param io: 
    :param c: 
    :param transmission_existing_capacity_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_period_capacities: 
    Two-level dictionary with the names of the transmission line as the 
    top-level key, the period as the second key, and tuples containing the 
    'min MW' and 'max MW' capacities as values
    :return: 
    """
    print("transmission capacities")

    # Subscenarios
    subs_data = [(transmission_existing_capacity_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_existing_capacity
        (transmission_existing_capacity_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for tx_line in list(tx_line_period_capacities.keys()):
        for period in list(tx_line_period_capacities[tx_line].keys()):
            inputs_data.append(
                (transmission_existing_capacity_scenario_id,
                 tx_line, period,
                 tx_line_period_capacities[tx_line][period][0],
                 tx_line_period_capacities[tx_line][period][1])
            )
    inputs_sql = """
        INSERT INTO inputs_transmission_existing_capacity
        (transmission_existing_capacity_scenario_id,
        transmission_line, period, min_mw, max_mw)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
