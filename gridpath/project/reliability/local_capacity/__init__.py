#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Local capacity projects and the zone they contribute to
"""

from builtins import next
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
    m.LOCAL_CAPACITY_PRJ_OPR_PRDS = Set(
        within=m.PRJ_OPR_PRDS,
        rule=lambda mod: [(prj, p) for (prj, p) in
                          mod.PRJ_OPR_PRDS
                          if prj in mod.LOCAL_CAPACITY_PROJECTS]
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
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "local_capacity_zone"),
                     param=(m.local_capacity_zone,)
                     )

    data_portal.data()['LOCAL_CAPACITY_PROJECTS'] = {
        None: list(data_portal.data()['local_capacity_zone'].keys())
    }


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    c = conn.cursor()
    project_zones = c.execute(
        """SELECT project, local_capacity_zone
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
        ) as prj_tbl
        LEFT OUTER JOIN
        (SELECT project, local_capacity_zone
        FROM inputs_project_local_capacity_zones
        WHERE project_local_capacity_zone_scenario_id = {}) as lc_zone_tbl
        USING (project)
        -- Filter out projects whose LC zone is not one included in our 
        -- local_capacity_zone_sceenario_id
        WHERE local_capacity_zone in (
                SELECT local_capacity_zone
                    FROM inputs_geography_local_capacity_zones
                    WHERE local_capacity_zone_scenario_id = {}
        );
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID
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

    prj_zones_dict = {p: "." if z is None else z for (p, z) in project_zones}

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("local_capacity_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_zones_dict.keys()):
                row.append(prj_zones_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)
