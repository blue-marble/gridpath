#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project availability
"""

from db.common_functions import spin_on_database_lock


def make_scenario_and_insert_types_and_ids(
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
        INSERT OR IGNORE INTO subscenarios_project_availability (
        project_availability_scenario_id, name,
        description) VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert all projects into project availability types table
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_availability_types
        (project_availability_scenario_id, project, availability_type,
        exogenous_availability_scenario_id, 
        endogenous_availability_scenario_id)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def insert_project_availability_exogenous(
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
        INSERT OR IGNORE INTO subscenarios_project_availability_exogenous
        (project, exogenous_availability_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Inputs
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_availability_exogenous
        (project, exogenous_availability_scenario_id, stage_id, timepoint, 
        availability_derate)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def insert_project_availability_endogenous(
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
        INSERT OR IGNORE INTO subscenarios_project_availability_endogenous
        (project, endogenous_availability_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Inputs
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_availability_endogenous
        (project, 
        endogenous_availability_scenario_id, 
        unavailable_hours_per_period,
        unavailable_hours_per_event_min,
        available_hours_between_events_min)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
