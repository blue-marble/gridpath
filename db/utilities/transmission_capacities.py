#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission load zones
"""


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
    c.execute(
        """INSERT INTO subscenarios_transmission_existing_capacity
        (transmission_existing_capacity_scenario_id, name,
        description)
        VALUES ({}, '{}', '{}');""".format(
            transmission_existing_capacity_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for tx_line in tx_line_period_capacities.keys():
        for period in tx_line_period_capacities[tx_line].keys():
            c.execute(
                """INSERT INTO inputs_transmission_existing_capacity
                (transmission_existing_capacity_scenario_id,
                transmission_line, period, min_mw, max_mw)
                VALUES ({}, '{}', {}, {}, {});""".format(
                    transmission_existing_capacity_scenario_id,
                    tx_line, period,
                    tx_line_period_capacities[tx_line][period][0],
                    tx_line_period_capacities[tx_line][period][1]
                )
            )
    io.commit()
