#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission new costs
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def transmision_new_cost(
        io, c,
        transmission_new_cost_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_period_lifetimes_costs
):
    """

    :param io: 
    :param c: 
    :param transmission_portfolio_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_period_lifetimes_costs:
    Dictionary with the names of the transmission line as keys and tuples
    containing the vintage, transmission line lifetime in years and
    transmission line's annualized real cost per MW-y
    :return: 
    """
    print("transmission new costs")

    # Subscenarios
    subs_data = [(transmission_new_cost_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_new_cost
        (transmission_new_cost_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for tx_line in list(tx_line_period_lifetimes_costs.keys()):
        inputs_data.append(
            (transmission_new_cost_scenario_id,
             tx_line,
             tx_line_period_lifetimes_costs[tx_line][0],
             tx_line_period_lifetimes_costs[tx_line][1],
             tx_line_period_lifetimes_costs[tx_line][2])
        )
    inputs_sql = """
        INSERT INTO inputs_transmission_new_cost
        (transmission_new_cost_scenario_id,
        transmission_line, vintage, tx_lifetime_yrs, tx_annualized_real_cost_per_mw_yr)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
