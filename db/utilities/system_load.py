#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
System load
"""
from db.common_functions import spin_on_database_lock


def insert_system_static_loads(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:
    """
    c = conn.cursor()

    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_load
        (load_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_system_load
        (load_scenario_id, load_zone, stage_id, timepoint, load_mw)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


if __name__ == "__main__":
    pass
