#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simple local capacity contribution where each local project contributes a 
fraction of its installed capacity.
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # The fraction of capacity that counts for the local capacity requirement
    m.local_capacity_fraction = Param(m.LOCAL_CAPACITY_PROJECTS,
                                      within=PercentFraction)

    def local_capacity_rule(mod, g, p):
        """

        :param mod:
        :param g:
        :param p:
        :return: 
        """
        return mod.Capacity_MW[g, p] \
            * mod.local_capacity_fraction[g]

    m.Local_Capacity_Contribution_MW = Expression(
        m.LOCAL_CAPACITY_PRJ_OPR_PRDS, rule=local_capacity_rule
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
                     select=("project", "local_capacity_fraction"),
                     param=(m.local_capacity_fraction,)
                     )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "project_local_capacity_contribution.csv"),
              "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period", "local_capacity_zone", 
                         "technology",
                         "load_zone",
                         "capacity_mw",
                         "local_capacity_fraction",
                         "local_capacity_contribution_mw"])
        for (prj, period) in m.LOCAL_CAPACITY_PRJ_OPR_PRDS:
            writer.writerow([
                prj,
                period,
                m.local_capacity_zone[prj],
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_MW[prj, period]),
                value(m.local_capacity_fraction[prj]),
                value(m.Local_Capacity_Contribution_MW[prj, period])
            ])


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    project_frac = c.execute(
        """SELECT project, local_capacity_fraction
        FROM 
        (SELECT project
        FROM inputs_project_local_capacity_zones
        WHERE project_local_capacity_zone_scenario_id = {}) as proj_tbl
        LEFT OUTER JOIN 
        (SELECT project, local_capacity_fraction
        FROM inputs_project_local_capacity_chars
        WHERE project_local_capacity_chars_scenario_id = {}) as frac_tbl
        USING (project);""".format(
            subscenarios.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_LOCAL_CAPACITY_CHARS_SCENARIO_ID
        )
    )

    return project_frac


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # project_frac = get_inputs_from_database(
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
    project_frac = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    prj_frac_dict = {p: "." if f is None else f for (p, f) in project_frac}

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("local_capacity_fraction")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_frac_dict.keys()):
                row.append(prj_frac_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id: 
    :param c: 
    :param db: 
    :param results_directory:
    :param quiet:
    :return: 
    """
    if not quiet:
        print("project local capacity contributions")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_local_capacity",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(
            results_directory,
            "project_local_capacity_contribution.csv"), "r"
    ) as local_capacity_results_file:
        reader = csv.reader(local_capacity_results_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            local_capacity_zone = row[2]
            technology = row[3]
            load_zone = row[4]
            capacity = row[5]
            local_capacity_fraction = row[6]
            contribution_mw = row[7]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                 local_capacity_zone, technology, load_zone,
                 capacity, local_capacity_fraction, contribution_mw)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_local_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id,
        local_capacity_zone, technology, load_zone, 
        capacity_mw, local_capacity_fraction,
        local_capacity_contribution_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_local_capacity
        (scenario_id, project, period, subproblem_id, stage_id,
        local_capacity_zone, technology, load_zone, 
        capacity_mw, local_capacity_fraction, local_capacity_contribution_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        local_capacity_zone, technology, load_zone,
        capacity_mw, local_capacity_fraction, local_capacity_contribution_mw
        FROM temp_results_project_local_capacity{}
        ORDER BY scenario_id, project, subproblem_id, stage_id, period;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
