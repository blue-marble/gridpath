#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Contributions to ELCC surface
"""
from __future__ import print_function

from builtins import next
from builtins import str
from builtins import range
import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Binary, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Which projects contribute to the ELCC surface
    m.contributes_to_elcc_surface = Param(m.PRM_PROJECTS, within=Binary)
    m.ELCC_SURFACE_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod: [p for p in mod.PRM_PROJECTS if
                                mod.contributes_to_elcc_surface[p]]
    )

    m.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE = \
        Set(m.PRM_ZONES, within=m.ELCC_SURFACE_PROJECTS,
            initialize=lambda mod, prm_z:
            [p for p in mod.ELCC_SURFACE_PROJECTS
             if mod.prm_zone[p] == prm_z])

    # The coefficient for each project contributing to the ELCC surface
    # Surface is limited to 1000 facets
    m.PROJECT_PERIOD_ELCC_SURFACE_FACETS = Set(
        dimen=3,
        within=m.ELCC_SURFACE_PROJECTS * m.PERIODS * list(range(1, 1001))
    )

    # The project coefficient for the surface
    # This goes into the piecewise linear constraint for the aggregate ELCC
    # calculation; unless we have a very detailed surface, this coefficient
    # would actually likely only vary by technology (e.g. wind and solar for a
    # 2-dimensional surface), but we have it by project here for maximum
    # flexibility
    m.elcc_surface_coefficient = Param(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS, within=NonNegativeReals
    )

    # TODO: how to define this for operational periods only
    # ELCC surface contribution of each project
    def elcc_surface_contribution_rule(mod, prj, p, f):
        """
        
        :param mod: 
        :param prj: 
        :param p: 
        :param f: 
        :return: 
        """
        if (prj, p) in mod.PRJ_OPR_PRDS:
            return mod.elcc_surface_coefficient[prj, p, f] \
                * mod.ELCC_Eligible_Capacity_MW[prj, p]
        else:
            return 0

    m.ELCC_Surface_Contribution_MW = Expression(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
        rule=elcc_surface_contribution_rule
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
    # Projects that contribute to the ELCC surface
    data_portal.load(filename=os.path.join(
                        scenario_directory, subproblem, stage, "inputs",
                        "projects.tab"),
                     select=("project", "contributes_to_elcc_surface"),
                     param=(m.contributes_to_elcc_surface,)
                     )

    # Project-period-facet
    data_portal.load(filename=os.path.join(
                        scenario_directory, subproblem, stage, "inputs",
                        "project_elcc_surface_coefficients.tab"),
                     index=m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
                     param=m.elcc_surface_coefficient,
                     select=("project", "period", "facet",
                             "elcc_surface_coefficient")
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
                           "prm_project_elcc_surface_contribution.csv"),
              "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period", "prm_zone", "facet",
                         "load_zone", "technology", "capacity_mw",
                         "elcc_eligible_capacity_mw",
                         "elcc_surface_coefficient",
                         "elcc_mw"])
        for (prj, period, facet) in m.PROJECT_PERIOD_ELCC_SURFACE_FACETS:
            writer.writerow([
                prj,
                period,
                m.prm_zone[prj],
                facet,
                m.load_zone[prj],
                m.technology[prj],
                value(m.Capacity_MW[prj, period]),
                value(m.ELCC_Eligible_Capacity_MW[prj, period]),
                value(m.elcc_surface_coefficient[prj, period, facet]),
                value(m.ELCC_Surface_Contribution_MW[prj, period, facet])
            ])


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c1 = conn.cursor()
    # Which projects will contribute to the surface
    project_contr = c1.execute(
        """SELECT project, contributes_to_elcc_surface
        FROM 
        (SELECT project
        FROM inputs_project_prm_zones
        WHERE project_prm_zone_scenario_id = {}) as prj_tbl
        LEFT OUTER JOIN 
        (SELECT project, contributes_to_elcc_surface
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as contr_tbl
        USING (project);""".format(
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    )

    c2 = conn.cursor()
    # The coefficients for the surface
    coefficients = c2.execute(
        """SELECT project, period, facet, elcc_surface_coefficient
        FROM inputs_project_elcc_surface
        JOIN inputs_project_portfolios
        USING (project)
        INNER JOIN inputs_temporal_periods
        USING (period)
        WHERE elcc_surface_scenario_id = {}
        AND project_portfolio_scenario_id = {}
        AND temporal_scenario_id = {};""".format(
            subscenarios.ELCC_SURFACE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return project_contr, coefficients


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # project_contr, coefficients = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn

    # do stuff here to validate inputs


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    projects.tab (to be precise, amend it) and
    project_elcc_surface_coefficients.tab files.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    project_contr, coefficients = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_contr_dict = dict()
    for (prj, zone) in project_contr:
        prj_contr_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("contributes_to_elcc_surface")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_contr_dict.keys()):
                row.append(prj_contr_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)

    with open(os.path.join(inputs_directory,
                           "project_elcc_surface_coefficients.tab"), "w", newline="") as \
            coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t", lineterminator="\n")

        # Writer header
        writer.writerow(
            ["project", "period", "facet", "elcc_surface_coefficient"]
        )
        # Write data
        for row in coefficients:
            writer.writerow(row)


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
        print("project elcc surface")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_elcc_surface",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "prm_project_elcc_surface_contribution.csv"), "r") \
            as elcc_file:
        reader = csv.reader(elcc_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            prm_zone = row[2]
            facet = row[3]
            load_zone = row[4]
            technology = row[5]
            capacity = row[6]
            elcc_eligible_capacity = row[7]
            coefficient = row[8]
            elcc = row[9]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                 prm_zone, facet, technology, load_zone,
                 capacity, elcc_eligible_capacity, coefficient, elcc)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_elcc_surface{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        prm_zone, facet, technology, load_zone,
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_surface_coefficient, elcc_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,  ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_elcc_surface
        (scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, facet, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw, 
        elcc_surface_coefficient, elcc_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, facet, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_surface_coefficient, elcc_mw
        FROM temp_results_project_elcc_surface{}
        ORDER BY scenario_id, project, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
