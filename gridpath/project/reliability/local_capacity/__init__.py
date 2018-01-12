#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Local capacity projects and the zone they contribute to
"""
import csv
import os.path
from pyomo.environ import Param, Set


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects we need to track for local capacity
    # contribution
    m.LOCAL_CAPACITY_PROJECTS = Set(within=m.PROJECTS)
    m.local_capacity_zone = Param(
        m.LOCAL_CAPACITY_PROJECTS, within=m.LOCAL_CAPACITY_ZONES
    )

    m.LOCAL_CAPACITY_PROJECTS_BY_LOCAL_CAPACITY_ZONE = \
        Set(m.LOCAL_CAPACITY_ZONES, within=m.LOCAL_CAPACITY_PROJECTS,
            initialize=lambda mod, local_capacity_z:
            [p for p in mod.LOCAL_CAPACITY_PROJECTS
             if mod.local_capacity_zone[p] == local_capacity_z])

    # Get operational local capacity projects - timepoints combinations
    m.LOCAL_CAPACITY_PROJECT_OPERATIONAL_PERIODS = Set(
        within=m.PROJECT_OPERATIONAL_PERIODS,
        rule=lambda mod: [(prj, p) for (prj, p) in
                          mod.PROJECT_OPERATIONAL_PERIODS
                          if prj in mod.LOCAL_CAPACITY_PROJECTS]
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "local_capacity_zone"),
                     param=(m.local_capacity_zone,)
                     )

    data_portal.data()['LOCAL_CAPACITY_PROJECTS'] = {
        None: data_portal.data()['local_capacity_zone'].keys()
    }


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    project_zones = c.execute(
        """SELECT project, local_capacity_zone
        FROM inputs_project_local_capacity_zones
        WHERE local_capacity_zone_scenario_id = {}
        AND project_local_capacity_zone_scenario_id = {};""".format(
            subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID
        )
    ).fetchall()

    prj_zones_dict = {p: "." if z is None else z for (p, z) in project_zones}

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("local_capacity_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in prj_zones_dict.keys():
                row.append(prj_zones_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)
