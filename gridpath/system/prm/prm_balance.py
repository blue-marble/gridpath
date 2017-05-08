#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Constraint total PRM contribution to be more than or equal to the requirement.
"""

import csv
import os.path

from pyomo.environ import Constraint, Expression, value

from gridpath.auxiliary.dynamic_components import \
    prm_balance_provision_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.Total_PRM_from_All_Sources_Expression = Expression(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=lambda mod, z, p:
        sum(getattr(mod, component)[z, p] for component
            in getattr(d, prm_balance_provision_components)
            )
    )

    def prm_requirement_rule(mod, z, p):
        """
        Total PRM provision must be greater than or equal to the requirement
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_PRM_from_All_Sources_Expression[z, p] \
            >= mod.prm_requirement_mw[z, p]

    m.PRM_Constraint = Constraint(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=prm_requirement_rule
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
                           "prm.csv"), "wb") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["prm_zone", "period", "prm_requirement_mw",
                         "prm_provision_mw"])
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([
                z,
                p,
                float(m.prm_requirement_mw[z, p]),
                value(m.Total_PRM_from_All_Sources_Expression[z, p])
            ])


def save_duals(m):
    m.constraint_indices["PRM_Constraint"] = \
        ["prm_zone", "period", "dual"]


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

    print("system prm total")

    # PRM contribution from the ELCC surface
    # Prior results should have already been cleared by
    # system.prm.aggregate_project_simple_prm_contribution,
    # then elcc_simple_mw imported
    # Update results_system_prm with NULL for requirement and total just in
    # case (instead of clearing prior results)
    c.execute(
        """UPDATE results_system_prm
        SET prm_requirement_mw = NULL,
        elcc_total_mw = NULL
        WHERE scenario_id = {}""".format(
            scenario_id
        )
    )
    db.commit()

    with open(os.path.join(results_directory,
                           "prm.csv"), "r") as \
            surface_file:
        reader = csv.reader(surface_file)

        reader.next()  # skip header
        for row in reader:
            prm_zone = row[0]
            period = row[1]
            prm_req_mw = row[2]
            prm_prov_mw = row[3]

            c.execute(
                """UPDATE results_system_prm
                SET prm_requirement_mw = {},
                elcc_total_mw = {}
                WHERE scenario_id = {}
                AND prm_zone = '{}'
                AND period = {}""".format(
                    prm_req_mw, prm_prov_mw, scenario_id, prm_zone, period
                )
            )
    db.commit()
