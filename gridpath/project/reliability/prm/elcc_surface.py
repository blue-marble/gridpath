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
        dimen=3, within=m.ELCC_SURFACE_PROJECTS * m.PERIODS * list(range(1, 1001))
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
        if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS:
            return mod.elcc_surface_coefficient[prj, p, f] \
                * mod.ELCC_Eligible_Capacity_MW[prj, p]
        else:
            return 0

    m.ELCC_Surface_Contribution_MW = Expression(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
        rule=elcc_surface_contribution_rule
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
    # Projects that contribute to the ELCC surface
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "contributes_to_elcc_surface"),
                     param=(m.contributes_to_elcc_surface,)
                     )

    # Project-period-facet
    data_portal.load(filename=os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "project_elcc_surface_coefficients.tab"
    ),
                     index=m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
                     param=m.elcc_surface_coefficient,
                     select=("project", "period", "facet",
                             "elcc_surface_coefficient")
                     )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "prm_project_elcc_surface_contribution.csv"),
              "w") as \
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


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    # Which projects will contribute to the surface
    project_contr = c.execute(
        """SELECT project, contributes_to_elcc_surface
        FROM 
        (SELECT project
        FROM inputs_project_prm_zones
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}) as prj_tbl
        LEFT OUTER JOIN 
        (SELECT project, contributes_to_elcc_surface
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as contr_tbl
        USING (project);""".format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_contr_dict = dict()
    for (prj, zone) in project_contr:
        prj_contr_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

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

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)

    # The coefficients for the surface
    coefficients = c.execute(
        """SELECT project, period, facet, elcc_surface_coefficient
        FROM inputs_project_elcc_surface
        JOIN inputs_project_portfolios
        USING (project)
        INNER JOIN inputs_temporal_periods
        USING (period)
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}
        AND elcc_surface_scenario_id = {}
        AND project_portfolio_scenario_id = {}
        AND timepoint_scenario_id = {};""".format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.ELCC_SURFACE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.TIMEPOINT_SCENARIO_ID
        )
    ).fetchall()

    with open(os.path.join(inputs_directory,
                           "project_elcc_surface_coefficients.tab"), "w") as \
            coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t")

        # Writer header
        writer.writerow(
            ["project", "period", "facet", "elcc_surface_coefficient"]
        )
        # Write data
        for row in coefficients:
            writer.writerow(row)


def import_results_into_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id: 
    :param c: 
    :param db: 
    :param results_directory:
    :return: 
    """
    print("project elcc surface")

    c.execute(
        """DELETE FROM results_project_elcc_surface 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_elcc_surface"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_elcc_surface""" + str(
            scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            prm_zone VARCHAR(32),
            facet INTEGER,
            technology VARCHAR(32),
            load_zone VARCHAR(32),
            capacity_mw FLOAT,
            elcc_eligible_capacity_mw FLOAT,
            elcc_surface_coefficient FLOAT,
            elcc_mw FLOAT,
            PRIMARY KEY (scenario_id, project, period, facet)
                );"""
    )
    db.commit()

    # Load results into the temporary table
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

            c.execute(
                """INSERT INTO temp_results_project_elcc_surface"""
                + str(scenario_id) + """
                    (scenario_id, project, period, prm_zone, facet, 
                    technology, load_zone, capacity_mw, 
                    elcc_eligible_capacity_mw,
                    elcc_surface_coefficient, elcc_mw)
                    VALUES ({}, '{}', {}, '{}', {}, '{}', '{}',  
                    {}, {}, {}, {});""".format(
                    scenario_id, project, period, prm_zone, facet, technology,
                    load_zone, capacity, elcc_eligible_capacity,
                    coefficient, elcc
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_elcc_surface
        (scenario_id, project, period, prm_zone, facet, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw, 
        elcc_surface_coefficient, elcc_mw)
        SELECT
        scenario_id, project, period, prm_zone, facet, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_surface_coefficient, elcc_mw
        FROM temp_results_project_elcc_surface""" + str(scenario_id) +
        """ ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_elcc_surface"""
        + str(scenario_id) + """;"""
    )
    db.commit()
