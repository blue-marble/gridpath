#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simple local capacity contribution where each local project contributes a 
fraction of its installed capacity.
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
        m.LOCAL_CAPACITY_PROJECT_OPERATIONAL_PERIODS, rule=local_capacity_rule
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
                     select=("project", "local_capacity_fraction"),
                     param=(m.local_capacity_fraction,)
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
                           "project_local_capacity_contribution.csv"),
              "wb") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period", "local_capacity_zone", 
                         "technology",
                         "load_zone",
                         "capacity_mw",
                         "local_capacity_fraction",
                         "local_capacity_contribution_mw"])
        for (prj, period) in m.LOCAL_CAPACITY_PROJECT_OPERATIONAL_PERIODS:
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


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    project_frac = c.execute(
        """SELECT project, local_capacity_fraction
        FROM 
        (SELECT project
        FROM inputs_project_local_capacity_zones
        WHERE local_capacity_zone_scenario_id = {}
        AND project_local_capacity_zone_scenario_id = {}) as proj_tbl
        LEFT OUTER JOIN 
        (SELECT project, local_capacity_fraction
        FROM inputs_project_local_capacity_chars
        WHERE project_local_capacity_chars_scenario_id = {}) as frac_tbl
        USING (project);""".format(
            subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_LOCAL_CAPACITY_CHARS_SCENARIO_ID
        )
    ).fetchall()

    prj_frac_dict = {p: "." if f is None else f for (p, f) in project_frac}

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("local_capacity_fraction")
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
    print("project local capacity contributions")

    c.execute(
        """DELETE FROM results_project_local_capacity 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary ta ble, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_local_capacity"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_local_capacity""" + str(
            scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            local_capacity_zone VARCHAR(32),
            technology VARCHAR(32),
            load_zone VARCHAR(32),
            capacity_mw FLOAT,
            local_capacity_fraction FLOAT,
            local_capacity_contribution_mw FLOAT,
            PRIMARY KEY (scenario_id, project, period)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(
            results_directory,
            "project_local_capacity_contribution.csv"), "r"
    ) as local_capacity_results_file:
        reader = csv.reader(local_capacity_results_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            local_capacity_zone = row[2]
            technology = row[3]
            load_zone = row[4]
            capacity = row[5]
            local_capacity_fraction = row[6]
            contribution_mw = row[7]

            c.execute(
                """INSERT INTO temp_results_project_local_capacity"""
                + str(scenario_id) + """
                    (scenario_id, project, period, local_capacity_zone, 
                    technology, load_zone, capacity_mw, 
                    local_capacity_fraction,
                    local_capacity_contribution_mw)
                    VALUES ({}, '{}', {}, '{}', '{}', 
                    '{}', {}, {}, {});""".format(
                    scenario_id, project, period, local_capacity_zone, technology,
                    load_zone, capacity, local_capacity_fraction,
                    contribution_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_local_capacity
        (scenario_id, project, period, local_capacity_zone, technology, 
        load_zone, capacity_mw, local_capacity_fraction, local_capacity_contribution_mw)
        SELECT
        scenario_id, project, period, local_capacity_zone, technology, 
        load_zone, capacity_mw, local_capacity_fraction, 
        local_capacity_contribution_mw
        FROM temp_results_project_local_capacity""" + str(scenario_id) +
        """ ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_local_capacity"""
        + str(scenario_id) + """;"""
    )
    db.commit()
