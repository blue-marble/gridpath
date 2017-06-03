#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project availability
"""


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
    :param project_avail: two-level dictionary with availability by project 
    and horizon
    :return: 
    """
    print("project availability")

    # Subscenario
    c.execute(
        """INSERT INTO subscenarios_project_availability
        (project_availability_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            project_availability_scenario_id, scenario_name,
            scenario_description
        )
    )
    io.commit()

    for prj in project_avail.keys():
        for h in project_avail[prj].keys():
            c.execute(
                """INSERT INTO inputs_project_availability
                (project_availability_scenario_id, project, horizon, 
                availability)
                VALUES ({}, '{}', {}, {});""".format(
                    project_availability_scenario_id, prj, h,
                    project_avail[prj][h]
                )
            )
    io.commit()
