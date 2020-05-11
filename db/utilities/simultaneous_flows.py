#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simultaneous flow limits
"""
from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def insert_into_database(
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
        INSERT OR IGNORE INTO subscenarios_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(
        conn=conn, cursor=c, sql=subs_sql, data=subscenario_data
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
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)
