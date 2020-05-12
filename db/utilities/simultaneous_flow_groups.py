#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Groups of transmission lines over which simultaneous flow constraints will 
be applied
"""

from db.common_functions import spin_on_database_lock


def insert_into_database(
        conn,
        subscenario_data,
        inputs_data
):
    """
    :param conn:
    :param subscenario_data: list of tuples with subscenario data
        (transmission_simultaneous_flow_limit_line_group_scenario_id, name,
        description)
    :param inputs_data: list of tuples with data for all subscenarios
        (transmission_simultaneous_flow_limit_line_group_scenario_id,
        transmission_simultaneous_flow_limit,
        transmission_line, simultaneous_flow_direction)

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO
        subscenarios_transmission_simultaneous_flow_limit_line_groups
        (transmission_simultaneous_flow_limit_line_group_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(
        conn=conn, cursor=c, sql=subs_sql, data=subscenario_data
    )

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO 
        inputs_transmission_simultaneous_flow_limit_line_groups
        (transmission_simultaneous_flow_limit_line_group_scenario_id,
        transmission_simultaneous_flow_limit,
        transmission_line, simultaneous_flow_direction)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql, data=inputs_data)

    c.close()
