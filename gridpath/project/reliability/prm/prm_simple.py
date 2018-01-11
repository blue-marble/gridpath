#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simplest PRM contribution where each PRM project contributes a fraction of 
its installed capacity.
"""

import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # The fraction of ELCC-eligible capacity that counts for the PRM via the
    # simple PRM method (whether or not project also contributes through the
    # ELCC surface)
    m.elcc_simple_fraction = Param(m.PRM_PROJECTS, within=PercentFraction)

    def elcc_simple_rule(mod, g, p):
        """
        
        :param g: 
        :param p: 
        :return: 
        """
        return mod.ELCC_Eligible_Capacity_MW[g, p] \
            * mod.elcc_simple_fraction[g]

    m.PRM_Simple_Contribution_MW = Expression(
        m.PRM_PROJECT_OPERATIONAL_PERIODS, rule=elcc_simple_rule
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
                     select=("project", "elcc_simple_fraction"),
                     param=(m.elcc_simple_fraction,)
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
                           "prm_project_elcc_simple_contribution.csv"),
              "wb") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period", "prm_zone", "technology",
                         "load_zone",
                         "capacity_mw",
                         "elcc_eligible_capacity_mw",
                         "elcc_simple_fraction",
                         "elcc_mw"])
        for (prj, period) in m.PRM_PROJECT_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                period,
                m.prm_zone[prj],
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_MW[prj, period]),
                value(m.ELCC_Eligible_Capacity_MW[prj, period]),
                value(m.elcc_simple_fraction[prj]),
                value(m.PRM_Simple_Contribution_MW[prj, period])
            ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    project_zones = c.execute(
        """SELECT project, elcc_simple_fraction
        FROM 
        (SELECT project
        FROM inputs_project_prm_zones
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}) as proj_tbl
        LEFT OUTER JOIN 
        (SELECT project, elcc_simple_fraction
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as frac_tbl
        USING (project);""".format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_frac_dict = dict()
    for (prj, zone) in project_zones:
        prj_frac_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("elcc_simple_fraction")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in prj_frac_dict.keys():
                row.append(prj_frac_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)


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
    print("project simple elcc")

    c.execute(
        """DELETE FROM results_project_elcc_simple 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_elcc_simple"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_elcc_simple""" + str(
            scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            prm_zone VARCHAR(32),
            technology VARCHAR(32),
            load_zone VARCHAR(32),
            capacity_mw FLOAT,
            elcc_eligible_capacity_mw FLOAT,
            elcc_simple_contribution_fraction FLOAT,
            elcc_mw FLOAT,
            PRIMARY KEY (scenario_id, project, period)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "prm_project_elcc_simple_contribution.csv"), "r") \
            as elcc_file:
        reader = csv.reader(elcc_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            prm_zone = row[2]
            technology = row[3]
            load_zone = row[4]
            capacity = row[5]
            elcc_eligible_capacity = row[6]
            prm_fraction = row[7]
            elcc = row[8]

            c.execute(
                """INSERT INTO temp_results_project_elcc_simple"""
                + str(scenario_id) + """
                    (scenario_id, project, period, prm_zone, technology, 
                    load_zone, capacity_mw, 
                    elcc_eligible_capacity_mw,
                    elcc_simple_contribution_fraction,
                    elcc_mw)
                    VALUES ({}, '{}', {}, '{}', '{}', 
                    '{}', {}, {}, {}, {});""".format(
                    scenario_id, project, period, prm_zone, technology,
                    load_zone, capacity, elcc_eligible_capacity,
                    prm_fraction, elcc
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_elcc_simple
        (scenario_id, project, period, prm_zone, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_simple_contribution_fraction, elcc_mw)
        SELECT
        scenario_id, project, period, prm_zone, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_simple_contribution_fraction, elcc_mw
        FROM temp_results_project_elcc_simple""" + str(scenario_id) +
        """ ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_elcc_simple"""
        + str(scenario_id) + """;"""
    )
    db.commit()
