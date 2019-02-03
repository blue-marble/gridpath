#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Hurdle rates
"""
from __future__ import print_function


def insert_transmission_hurdle_rates(
        io, c,
        transmission_hurdle_rate_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_period_hurdle_rates
):
    """

    :param io: 
    :param c: 
    :param transmission_hurdle_rate_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_period_hurdle_rates: 
    Two-level dictionary with the names of the transmission line groups as 
    top-level keys, the period as second key, and the positive and 
    negative direction hurdle rates as values in a tuple
    :return: 
    """
    print("transmission hurdle rates")

    # Subscenarios
    c.execute(
         """INSERT INTO subscenarios_transmission_hurdle_rates
            (transmission_hurdle_rate_scenario_id, name, description)
            VALUES ({}, '{}', '{}');""".format(
            transmission_hurdle_rate_scenario_id,
            scenario_name, scenario_description
            )
    )
    io.commit()

    # Insert data
    for tx_line in list(tx_line_period_hurdle_rates.keys()):
        for period in list(tx_line_period_hurdle_rates[tx_line].keys()):
            c.execute(
                """INSERT INTO inputs_transmission_hurdle_rates
                (transmission_hurdle_rate_scenario_id,
                transmission_line, period,
                hurdle_rate_positive_direction_per_mwh,
                hurdle_rate_negative_direction_per_mwh)
                VALUES ({}, '{}', {}, {}, {});""".format(
                    transmission_hurdle_rate_scenario_id,
                    tx_line, period,
                    tx_line_period_hurdle_rates[tx_line][period][0],
                    tx_line_period_hurdle_rates[tx_line][period][1]
                )
            )
    io.commit()
