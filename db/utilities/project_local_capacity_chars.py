#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def insert_project_local_capacity_chars(
        io, c,
        project_local_capacity_chars_scenario_id,
        scenario_name,
        scenario_description,
        project_local_capacity_chars
):
    """
    :param io:
    :param c:
    :param project_local_capacity_chars_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param project_local_capacity_chars: Dictionary with project as key, and the
    values for the local capacity fraction and min duration for full
    capacity credit in hours in a tuple as values
    :return:
    """

    print("project new binary build size")

    # Subscenarios
    subs_data = [(project_local_capacity_chars_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
          INSERT INTO subscenarios_project_local_capacity_chars
           (project_local_capacity_chars_scenario_id, name, description)
           VALUES (?, ?, ?);
          """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for prj in list(project_local_capacity_chars.keys()):
        inputs_data.append(
            (project_local_capacity_chars_scenario_id,
             prj,
             project_local_capacity_chars[prj][0],
             project_local_capacity_chars[prj][1])
        )
    inputs_sql = """
          INSERT INTO inputs_project_local_capacity_chars
          (project_local_capacity_chars_scenario_id, 
          project,
          local_capacity_fraction,
          min_duration_for_full_capacity_credit_hours)
          VALUES (?, ?, ?, ?);
          """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


