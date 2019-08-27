#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate simple local capacity contribution from the project level to the
local-capacity-zone level for each period.
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import \
    local_capacity_balance_provision_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_local_capacity_provision_rule(mod, z, p):
        """

        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Local_Capacity_Contribution_MW[g, p]
            for g in mod.LOCAL_CAPACITY_PROJECTS_BY_LOCAL_CAPACITY_ZONE[z]
            if (g, p) in mod.LOCAL_CAPACITY_PROJECT_OPERATIONAL_PERIODS
        )

    m.Total_Local_Capacity_Contribution_MW = Expression(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=total_local_capacity_provision_rule
    )

    # Add contribtion to local capacity provision components
    getattr(d, local_capacity_balance_provision_components).append(
        "Total_Local_Capacity_Contribution_MW"
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
                           "local_capacity_contribution.csv"), "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["local_capacity_zone", "period", "contribution_mw"])
        for (z, p) in m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([
                z,
                p,
                value(m.Total_Local_Capacity_Contribution_MW[z, p])
            ])


def import_results_into_database(scenario_id, subproblem, stage, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    print("system local capacity")
    c.execute(
        """DELETE FROM results_system_local_capacity 
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_system_local_capacity"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_system_local_capacity"""
        + str(scenario_id) + """(
         scenario_id INTEGER,
         local_capacity_zone VARCHAR(64),
         period INTEGER,
         subproblem_id INTEGER,
         stage_id INTEGER,
         local_capacity_provision_mw FLOAT,
         PRIMARY KEY (scenario_id, local_capacity_zone, period, subproblem_id, stage_id)
         );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "local_capacity_contribution.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            local_capacity_zone = row[0]
            period = row[1]
            elcc = row[2]

            c.execute(
                """INSERT INTO 
                temp_results_system_local_capacity"""
                + str(scenario_id) + """
                 (scenario_id, local_capacity_zone, 
                 period, subproblem_id, stage_id, local_capacity_provision_mw)
                 VALUES ({}, '{}', {}, {}, {}, {});""".format(
                    scenario_id, local_capacity_zone,
                    period, subproblem, stage, elcc
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_system_local_capacity
        (scenario_id, local_capacity_zone, 
        period, subproblem_id, stage_id, local_capacity_provision_mw)
        SELECT scenario_id, local_capacity_zone, period, 
        subproblem_id, stage_id, local_capacity_provision_mw
        FROM temp_results_system_local_capacity"""
        + str(scenario_id)
        + """
         ORDER BY scenario_id, local_capacity_zone, period, subproblem_id, stage_id;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_system_local_capacity"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
