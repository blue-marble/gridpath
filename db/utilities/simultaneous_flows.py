#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simultaneous flow limits
"""
from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def insert_into_database(
        io, c,
        subscenario_data,
        input_data
):
    """

    :param io: 
    :param c: 
    :param subscenario_data: list of tuples with subscenario data
        (transmission_simultaneous_flow_limit_scenario_id, name,
        description)
    :param input_data: list of tuples with data for all subscenarios
         (transmission_simultaneous_flow_limit_scenario_id,
         transmission_simultaneous_flow_limit, period, max_flow_mw)
    """
    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(
        conn=io, cursor=c, sql=subs_sql, data=subscenario_data
    )

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO
        inputs_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id,
        transmission_simultaneous_flow_limit, period,
        max_flow_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=input_data)
