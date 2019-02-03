#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create a list of all projects
"""
from __future__ import print_function


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
    c.execute(
        """INSERT INTO subscenarios_project_load_zones
        (load_zone_scenario_id, project_load_zone_scenario_id, name,
        description)
        VALUES ({}, {}, '{}', '{}');""".format(
            load_zone_scenario_id, project_load_zone_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert all projects with their modeled load_zones
    for project in list(project_load_zones.keys()):
        c.execute(
            """INSERT INTO inputs_project_load_zones
            (load_zone_scenario_id, project_load_zone_scenario_id, project, 
            load_zone)
            VALUES ({}, {}, '{}', '{}');""".format(
                load_zone_scenario_id, project_load_zone_scenario_id,
                project, project_load_zones[project]
            )
        )
    io.commit()

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
            WHERE load_zone_scenario_id = {}
            AND project_load_zone_scenario_id = {}
            AND project = '{}';""".format(
                load_zone_scenario_id, project_load_zone_scenario_id, prj
            )
        ).fetchall()

        if lz is None:
            raise ValueError("Project {}".format(prj)
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
    c.execute(
        """INSERT INTO subscenarios_project_{}_bas
        ({}_ba_scenario_id, project_{}_ba_scenario_id, 
        name, description)
        VALUES ({}, {}, '{}', '{}');""".format(
            reserve_type, reserve_type, reserve_type,
            reserve_ba_scenario_id, project_reserve_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert projects with BAs
    for project in list(project_bas.keys()):
        c.execute(
            """INSERT INTO inputs_project_{}_bas
            ({}_ba_scenario_id, 
            project_{}_ba_scenario_id, project, {}_ba)
            VALUES ({}, {}, '{}', '{}');""".format(
                reserve_type, reserve_type, reserve_type, reserve_type,
                reserve_ba_scenario_id, project_reserve_scenario_id,
                project, project_bas[project]
            )
        )
    io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_project_{}_zones
        ({}_zone_scenario_id, project_{}_zone_scenario_id, name,
        description)
        VALUES ({}, {}, '{}', '{}');""".format(
            policy_type, policy_type, policy_type,
            policy_zone_scenario_id, project_policy_zone_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Project zones data
    for project in list(project_zones.keys()):
        c.execute(
            """INSERT INTO inputs_project_{}_zones
            ({}_zone_scenario_id, project_{}_zone_scenario_id, project, 
            {}_zone)
            VALUES ({}, {}, '{}', '{}');""".format(
                policy_type, policy_type, policy_type, policy_type,
                policy_zone_scenario_id, project_policy_zone_scenario_id,
                project, project_zones[project]
            )
        )
    io.commit()


if __name__ == "__main__":
    pass
