#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Constraint total PRM contribution to be more than or equal to the requirement.
"""

from __future__ import print_function

from builtins import next
import csv
import os.path

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
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

    m.PRM_Shortage_MW = Var(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p):
        return mod.PRM_Shortage_MW[z, p] * mod.prm_allow_violation[z]

    m.PRM_Shortage_MW_Expression = Expression(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT, rule=violation_expression_rule
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
            + mod.PRM_Shortage_MW_Expression[z, p] \
            >= mod.prm_requirement_mw[z, p]

    m.PRM_Constraint = Constraint(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=prm_requirement_rule
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
                           "prm.csv"), "w", newline="") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["prm_zone", "period",
                         "discount_factor", "number_years_represented",
                         "prm_requirement_mw",
                         "prm_provision_mw",
                         "prm_shortage_mw"])
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                float(m.prm_requirement_mw[z, p]),
                value(m.Total_PRM_from_All_Sources_Expression[z, p]),
                value(m.PRM_Shortage_MW_Expression[z, p])
            ])


def save_duals(m):
    m.constraint_indices["PRM_Constraint"] = \
        ["prm_zone", "period", "dual"]


def import_results_into_database(scenario_id, subproblem, stage, c, db, results_directory):
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
    nullify_sql = """
        UPDATE results_system_prm
        SET prm_requirement_mw = NULL,
        elcc_total_mw = NULL,
        prm_shortage_mw = NULL,
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=nullify_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)

    results = []
    with open(os.path.join(results_directory,
                           "prm.csv"), "r") as \
            surface_file:
        reader = csv.reader(surface_file)

        next(reader)  # skip header
        for row in reader:
            prm_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            prm_req_mw = row[4]
            prm_prov_mw = row[5]
            shortage_mw = row[6]
            
            results.append(
                (prm_req_mw, prm_prov_mw, shortage_mw,
                 discount_factor, number_years,
                 scenario_id, prm_zone, period,
                 subproblem, stage)
            )

    update_sql = """
        UPDATE results_system_prm
        SET prm_requirement_mw = ?,
        elcc_total_mw = ?,
        prm_shortage_mw = ?,
        discount_factor = ?,
        number_years_represented = ?
        WHERE scenario_id = ?
        AND prm_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?"""
    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)

    # Update duals
    duals_results = []
    with open(os.path.join(results_directory, "PRM_Constraint.csv"),
              "r") as prm_duals_file:
        reader = csv.reader(prm_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )
    duals_sql = """
        UPDATE results_system_prm
        SET dual = ?
        WHERE prm_zone = ?
        AND period = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal carbon cost per MMt
    mc_sql = """
        UPDATE results_system_prm
        SET prm_marginal_cost_per_mw = 
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)
