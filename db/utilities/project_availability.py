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
        io, c, project_avail_scenarios, project_avail
):
    """
    :param io:
    :param c:
    :param project_avail_scenarios: two-level dictionary by project and
        subscenario id, with the subscenario name and description as a tuple
        value
    :param project_avail: four-level dictionary with availability derate by
        project, exogenous_availability_scenario_id, stage, and timepoint
    """

    # "Subscenario"
    subs_data = []
    for prj in project_avail_scenarios.keys():
        for scenario_id in project_avail_scenarios[prj].keys():
            subs_data.append(
                (prj, scenario_id,
                 project_avail_scenarios[prj][scenario_id][0],
                 project_avail_scenarios[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_availability_exogenous
        (project, exogenous_availability_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Inputs
    inputs_data = []
    for prj in list(project_avail.keys()):
        for subscenario_id in list(project_avail[prj].keys()):
            for stage in list(project_avail[prj][subscenario_id].keys()):
                for tmp in list(project_avail[prj][subscenario_id][stage]
                                .keys()):
                    inputs_data.append(
                        (prj, subscenario_id, stage, int(tmp),
                         project_avail[prj][subscenario_id][stage][tmp]
                         )
                    )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_availability_exogenous
        (project, exogenous_availability_scenario_id, stage_id, timepoint, 
        availability_derate)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def insert_project_availability_endogenous(
        io, c, project_avail_scenarios, project_avail
):
    """
    :param io:
    :param c:
    :param project_avail_scenarios: two-level dictionary by project and
        subscenario id, with the subscenario name and description as a tuple
        value
    :param project_avail: {project: {scenario_id: (
        unavailable_hours_per_period,
        unavailable_hours_per_event_min,
        available_hours_between_events_min)}}
    """

    # "Subscenario"
    subs_data = []
    for prj in project_avail_scenarios.keys():
        for scenario_id in project_avail_scenarios[prj].keys():
            subs_data.append(
                (prj, scenario_id,
                 project_avail_scenarios[prj][scenario_id][0],
                 project_avail_scenarios[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_availability_endogenous
        (project, endogenous_availability_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Inputs
    inputs_data = []
    for prj in list(project_avail.keys()):
        for subscenario_id in list(project_avail[prj].keys()):
            inputs_data.append(
                (prj,
                 subscenario_id,
                 project_avail[prj][subscenario_id][0],
                 project_avail[prj][subscenario_id][1],
                 project_avail[prj][subscenario_id][2])
            )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_availability_endogenous
        (project, 
        endogenous_availability_scenario_id, 
        unavailable_hours_per_period,
        unavailable_hours_per_event_min,
        available_hours_between_events_min)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def insert_project_availability_exogenous_(
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


def insert_project_availability_endogenous_(
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
