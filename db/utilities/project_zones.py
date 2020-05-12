#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create a list of all projects
"""
from db.common_functions import spin_on_database_lock


def project_load_zones(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    Assign load zones to all projects

    """

    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_load_zones
        (project_load_zone_scenario_id, name, description)
        VALUES (?, ?, ?);
        """.format(

        )
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert all projects with their modeled load_zones
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_load_zones
        (project_load_zone_scenario_id, project, load_zone)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    # Check that all projects got assigned a load zone
    subscenario_id = subscenario_data[0][0]
    all_projects = [
        prj[0] for prj in c.execute(
            """SELECT * FROM inputs_project_all"""
        ).fetchall()
    ]

    for prj in all_projects:
        lz = c.execute(
            """SELECT load_zone
            FROM inputs_project_load_zones
            WHERE project_load_zone_scenario_id = ?
            AND project = ?;
        """,
            (subscenario_id, prj)
        ).fetchall()

        if lz is None:
            raise ValueError("Project ?".format(prj)
                             + " has not been assigned a load_zone")

    c.close()


def project_reserve_bas(
    conn,
    subscenario_data,
    inputs_data,
    reserve_type
):
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_{}_bas
        (project_{}_ba_scenario_id, name, description)
        VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql, data=subscenario_data)

    # Insert projects with BAs
    if reserve_type == "frequency_response":
        inputs_sql = """
            INSERT OR IGNORE INTO inputs_project_{}_bas
            (project_{}_ba_scenario_id, project, {}_ba, contribute_to_partial)
            VALUES (?, ?, ?, ?);
            """.format(reserve_type, reserve_type, reserve_type)
    else:
        inputs_sql = """
            INSERT OR IGNORE INTO inputs_project_{}_bas
            (project_{}_ba_scenario_id, project, {}_ba)
            VALUES (?, ?, ?);
            """.format(reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql, data=inputs_data)

    c.close()


def project_policy_zones(
    conn, subscenario_data, inputs_data, policy_type
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    Can be used for RPS (rps), PRM (prm) and carbon cap (carbon_cap) policy
    types.
    """

    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_{}_zones
        (project_{}_zone_scenario_id, name, description)
        VALUES (?, ?, ?);
        """.format(policy_type, policy_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Project zones data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_{}_zones
        (project_{}_zone_scenario_id, project, {}_zone)
        VALUES (?, ?, ?);
        """.format(policy_type, policy_type, policy_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


if __name__ == "__main__":
    pass
