#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate simple PRM contribution from the project level to the PRM zone level 
for each period.
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import \
    prm_balance_provision_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_prm_provision_rule(mod, z, p):
        """
        
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.PRM_Simple_Contribution_MW[g, p]
                   for g in mod.PRM_PROJECTS_BY_PRM_ZONE[z]
                   if (g, p) in mod.PRM_PROJECT_OPERATIONAL_PERIODS)

    m.Total_PRM_Simple_Contribution_MW = Expression(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=total_prm_provision_rule
    )

    # Add to emission imports to carbon balance
    getattr(d, prm_balance_provision_components).append(
        "Total_PRM_Simple_Contribution_MW"
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
                           "prm_elcc_simple.csv"), "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["prm_zone", "period", "elcc_mw"])
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([
                z,
                p,
                value(m.Total_PRM_Simple_Contribution_MW[z, p])
            ])


def import_results_into_database(scenario_id, subproblem, stage, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    print("system prm simple elcc")
    c.execute(
        """DELETE FROM results_system_prm 
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_system_prm"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_system_prm"""
        + str(scenario_id) + """(
         scenario_id INTEGER,
         prm_zone VARCHAR(64),
         period INTEGER,
         subproblem_id INTEGER,
         stage_id INTEGER,
         elcc_simple_mw FLOAT,
         PRIMARY KEY (scenario_id, prm_zone, period, subproblem_id, stage_id)
         );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "prm_elcc_simple.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            prm_zone = row[0]
            period = row[1]
            elcc = row[2]

            c.execute(
                """INSERT INTO 
                temp_results_system_prm"""
                + str(scenario_id) + """
                 (scenario_id, prm_zone, period, subproblem_id, stage_id, 
                 elcc_simple_mw)
                 VALUES ({}, '{}', {}, {}, {}, {});""".format(
                    scenario_id, prm_zone, period, subproblem, stage, elcc
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_system_prm
        (scenario_id, prm_zone, period, subproblem_id, stage_id, elcc_simple_mw)
        SELECT scenario_id, prm_zone, period, subproblem_id, stage_id, elcc_simple_mw
        FROM temp_results_system_prm"""
        + str(scenario_id)
        + """
         ORDER BY scenario_id, prm_zone, period, subproblem_id, stage_id;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_system_prm"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
