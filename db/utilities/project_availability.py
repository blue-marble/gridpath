#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project availability
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def update_project_availability(
        io, c,
        project_availability_scenario_id,
        scenario_name,
        scenario_description,
        project_avail
):
    """
    :param io: 
    :param c: 
    :param project_availability_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param project_avail: three-level dictionary with availability by
        project, stage, and timepoint
    """
    print("project availability")

    # Subscenario
    subs_data = [(project_availability_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = \
        """INSERT INTO subscenarios_project_availability
        (project_availability_scenario_id, name, description)
        VALUES (?, ?, ?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Inputs
    inputs_data = []
    for prj in list(project_avail.keys()):
        for stage in list(project_avail[prj].keys()):
            for tmp in list(project_avail[prj][stage].keys()):
                inputs_data.append((project_availability_scenario_id, prj,
                                    stage, tmp,
                                    project_avail[prj][stage][tmp]))
    inputs_sql = \
        """INSERT INTO inputs_project_availability
        (project_availability_scenario_id, project, stage_id, 
        timepoint, availability)
        VALUES (?, ?, ?, ?, ?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
