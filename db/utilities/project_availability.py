#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project availability
"""
from __future__ import print_function


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
    c.execute(
        """INSERT INTO subscenarios_project_availability
        (project_availability_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            project_availability_scenario_id, scenario_name,
            scenario_description
        )
    )
    io.commit()

    for prj in list(project_avail.keys()):
        for stage in list(project_avail[prj].keys()):
            for tmp in list(project_avail[prj][stage].keys()):
                c.execute(
                    """INSERT INTO inputs_project_availability
                    (project_availability_scenario_id, project, stage_id, 
                    timepoint, availability)
                    VALUES ({}, '{}', {}, {}, {});""".format(
                        project_availability_scenario_id, prj, stage, tmp,
                        project_avail[prj][stage][tmp]
                    )
                )
    io.commit()
