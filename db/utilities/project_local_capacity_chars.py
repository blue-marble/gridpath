#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

from db.common_functions import spin_on_database_lock


def insert_project_local_capacity_chars(
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
          INSERT OR IGNORE INTO subscenarios_project_local_capacity_chars
           (project_local_capacity_chars_scenario_id, name, description)
           VALUES (?, ?, ?);
          """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
          INSERT OR IGNORE INTO inputs_project_local_capacity_chars
          (project_local_capacity_chars_scenario_id, 
          project,
          local_capacity_fraction,
          min_duration_for_full_capacity_credit_hours)
          VALUES (?, ?, ?, ?);
          """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
