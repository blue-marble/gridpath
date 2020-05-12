#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""
from db.common_functions import spin_on_database_lock


def local_capacity_requirement(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # TODO: could refactor this with the other system requirements inputs
    #  such as PRM, load, ...
    # Subscenarios

    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_local_capacity_requirement
        (local_capacity_requirement_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_system_local_capacity_requirement
        (local_capacity_requirement_scenario_id, 
        local_capacity_zone, period, local_capacity_requirement_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
