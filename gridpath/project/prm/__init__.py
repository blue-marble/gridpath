#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
PRM projects and the zone they contribute to
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
    # First figure out which projects we need to track for PRM contribution
    m.PRM_PROJECTS = Set(within=m.PROJECTS)
    m.prm_zone = Param(m.PRM_PROJECTS, within=m.PRM_ZONES)

    m.PRM_PROJECTS_BY_PRM_ZONE = \
        Set(m.PRM_ZONES, within=m.PRM_PROJECTS,
            initialize=lambda mod, prm_z:
            [p for p in mod.PRM_PROJECTS
             if mod.prm_zone[p] == prm_z])

    # Get operational carbon cap projects - timepoints combinations
    m.PRM_PROJECT_OPERATIONAL_PERIODS = Set(
        within=m.PROJECT_OPERATIONAL_PERIODS,
        rule=lambda mod: [(prj, p) for (prj, p) in
                          mod.PROJECT_OPERATIONAL_PERIODS
                          if prj in mod.PRM_PROJECTS]
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
                     select=("project", "prm_zone"),
                     param=(m.prm_zone,)
                     )

    data_portal.data()['PRM_PROJECTS'] = {
        None: data_portal.data()['prm_zone'].keys()
    }


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    project_zones = c.execute(
        """SELECT project, prm_zone
        FROM inputs_project_prm_zones
            WHERE prm_zone_scenario_id = {}
            AND project_prm_zone_scenario_id = {}""".format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone) in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("prm_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in prj_zone_dict.keys():
                row.append(prj_zone_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)
