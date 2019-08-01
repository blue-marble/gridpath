#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
PRM projects and the zone they contribute to
"""

from builtins import next
from builtins import str
from builtins import range
import csv
import os.path
from pyomo.environ import Param, Set, Var, NonNegativeReals, Constraint


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects we need to track for PRM contribution
    m.PRM_PROJECTS = Set(within=m.PROJECTS)
    m.prm_zone = Param(m.PRM_PROJECTS, within=m.PRM_ZONES)
    m.prm_type = Param(m.PRM_PROJECTS)

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


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "projects.tab"),
                     select=("project", "prm_zone", "prm_type"),
                     param=(m.prm_zone, m.prm_type)
                     )

    data_portal.data()['PRM_PROJECTS'] = {
        None: list(data_portal.data()['prm_zone'].keys())
    }


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    project_zones = c.execute(
        """SELECT project, prm_zone, prm_type
        FROM 
        (SELECT project, prm_zone
        FROM inputs_project_prm_zones
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}) as prm_zone_tbl
        LEFT OUTER JOIN
        (SELECT project, prm_type
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as prm_type_tbl
        USING (project)
        """.format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    )

    return project_zones


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # project_zones = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn

    # do stuff here to validate inputs


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    project_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    # Only assign a type to projects that contribute to a PRM zone in case
    # we have projects with missing zones here
    prj_zone_type_dict = dict()
    for (prj, zone, prm_type) in project_zones:
        prj_zone_type_dict[str(prj)] = \
            (".", ".") if zone is None else (str(zone), str(prm_type))

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = next(reader)
        for new_column in ["prm_zone", "prm_type"]:
            header.append(new_column)
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_zone_type_dict.keys()):
                for new_column_value in [
                    prj_zone_type_dict[row[0]][0],
                    prj_zone_type_dict[row[0]][1]
                ]:
                    row.append(new_column_value)
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                for new_column in range(2):
                    row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)
