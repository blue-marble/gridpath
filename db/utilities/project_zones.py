#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create a list of all projects
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock

def project_load_zones(
        io, c,
        load_zone_scenario_id,
        project_load_zone_scenario_id,
        scenario_name,
        scenario_description,
        project_load_zones
):
    """
    Assign load zones to all projects
    :param io: 
    :param c: 
    :param load_zone_scenario_id: 
    :param project_load_zone_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param project_load_zones: 
    :return: 
    """

    print("project load zones")

    # Subscenarios
    subs_data = [(load_zone_scenario_id, project_load_zone_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_load_zones
        (load_zone_scenario_id, project_load_zone_scenario_id, name,
        description)
        VALUES (?, ?, ?, ?);
        """.format(

        )
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert all projects with their modeled load_zones
    inputs_data = []
    for p in list(project_load_zones.keys()):
        inputs_data.append(
            (load_zone_scenario_id, project_load_zone_scenario_id,
             p, project_load_zones[p])
        )

    inputs_sql = """
        INSERT INTO inputs_project_load_zones
        (load_zone_scenario_id, project_load_zone_scenario_id, project, 
        load_zone)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)

    # Check that all projects got assigned a load zone
    all_projects = [
        prj[0] for prj in c.execute(
            """SELECT * FROM inputs_project_all"""
        ).fetchall()
    ]

    for prj in all_projects:
        lz = c.execute(
            """SELECT load_zone
            FROM inputs_project_load_zones
            WHERE load_zone_scenario_id = ?
            AND project_load_zone_scenario_id = ?
            AND project = ?;
        """,
            (load_zone_scenario_id, project_load_zone_scenario_id, prj)
        ).fetchall()

        if lz is None:
            raise ValueError("Project ?".format(prj)
                             + " has not been assigned a load_zone")


def project_reserve_bas(
        io, c,
        reserve_type,
        reserve_ba_scenario_id,
        project_reserve_scenario_id,
        scenario_name,
        scenario_description,
        project_bas,
):

    print("project " + reserve_type + " bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, project_reserve_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_{}_bas
        ({}_ba_scenario_id, project_{}_ba_scenario_id, 
        name, description)
        VALUES (?, ?, ?, ?);
        """.format(reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert projects with BAs
    inputs_data = []
    for project in list(project_bas.keys()):
        inputs_data.append(
            (reserve_ba_scenario_id, project_reserve_scenario_id,
                project, project_bas[project])
        )
    inputs_sql = """
        INSERT INTO inputs_project_{}_bas
        ({}_ba_scenario_id, 
        project_{}_ba_scenario_id, project, {}_ba)
        VALUES (?, ?, ?, ?);
        """.format(reserve_type, reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def project_policy_zones(
        io, c,
        policy_zone_scenario_id,
        project_policy_zone_scenario_id,
        scenario_name,
        scenario_description,
        project_zones,
        policy_type
):
    """
    Can be used for RPS (rps), PRM (prm) and carbon cap (carbon_cap) policy 
    types.
    :param io: 
    :param c: 
    :param policy_zone_scenario_id: 
    :param project_policy_zone_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param project_zones: 
    :param policy_type: 
    :return: 
    """
    print("project " + policy_type + " zones")
    
    # Subscenarios
    subs_data = [(policy_zone_scenario_id, project_policy_zone_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_{}_zones
        ({}_zone_scenario_id, project_{}_zone_scenario_id, name,
        description)
        VALUES (?, ?, ?, ?);
        """.format(policy_type, policy_type, policy_type)
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Project zones data
    inputs_data = []
    for project in list(project_zones.keys()):
        inputs_data.append(
            (policy_zone_scenario_id, project_policy_zone_scenario_id,
             project, project_zones[project])
        )
    inputs_sql = """
        INSERT INTO inputs_project_{}_zones
        ({}_zone_scenario_id, project_{}_zone_scenario_id, project, 
        {}_zone)
        VALUES (?, ?, ?, ?);
        """.format(policy_type, policy_type, policy_type, policy_type)
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
