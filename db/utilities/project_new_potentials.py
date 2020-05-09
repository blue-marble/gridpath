#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Candidate project potentials
"""

from db.common_functions import spin_on_database_lock


def update_project_potentials(
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
        INSERT OR IGNORE INTO subscenarios_project_new_potential
         (project_new_potential_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_new_potential
        (project_new_potential_scenario_id, project, period,
        minimum_cumulative_new_build_mw,
        maximum_cumulative_new_build_mw,
        minimum_cumulative_new_build_mwh, 
        maximum_cumulative_new_build_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def update_project_binary_build_sizes(
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
        INSERT OR IGNORE INTO subscenarios_project_new_binary_build_size
         (project_new_binary_build_size_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_new_binary_build_size
        (project_new_binary_build_size_scenario_id, 
        project,
        binary_build_size_mw,
        binary_build_size_mwh)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
