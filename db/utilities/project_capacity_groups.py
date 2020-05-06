#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Load data for project group capacity requirements.
"""

from db.common_functions import spin_on_database_lock


def insert_capacity_group_requirements(
    conn, subscenario_data, input_data
):
    c = conn.cursor()

    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_capacity_group_requirements
        (project_capacity_group_requirement_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_capacity_group_requirements
        (project_capacity_group_requirement_scenario_id, 
        capacity_group, period,
        capacity_group_new_capacity_min, capacity_group_new_capacity_max,
        capacity_group_total_capacity_min, capacity_group_total_capacity_max)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=input_data)


def insert_capacity_group_projects(
        conn, subscenario_data, input_data
):
    c = conn.cursor()

    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_capacity_groups
        (project_capacity_group_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_capacity_groups
        (project_capacity_group_scenario_id, 
        capacity_group, project)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=input_data)
