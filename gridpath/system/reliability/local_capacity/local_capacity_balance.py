#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Constraint total local capacity contribution to be more than or equal to the 
requirement.
"""
from __future__ import print_function

from builtins import next
import csv
import os.path

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import \
    local_capacity_balance_provision_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.Total_Local_Capacity_from_All_Sources_Expression_MW = Expression(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=lambda mod, z, p:
        sum(getattr(mod, component)[z, p] for component
            in getattr(d, local_capacity_balance_provision_components)
            )
    )

    m.Local_Capacity_Shortage_MW = Var(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
        within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p):
        return mod.Local_Capacity_Shortage_MW[z, p] * \
               mod.local_capacity_allow_violation[z]

    m.Local_Capacity_Shortage_MW_Expression = Expression(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=violation_expression_rule
    )

    def local_capacity_requirement_rule(mod, z, p):
        """
        Total local capacity provision must be greater than or equal to the
        requirement
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Local_Capacity_from_All_Sources_Expression_MW[z, p] \
            + mod.Local_Capacity_Shortage_MW_Expression[z, p] \
            >= mod.local_capacity_requirement_mw[z, p]

    m.Local_Capacity_Constraint = Constraint(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=local_capacity_requirement_rule
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
                           "local_capacity.csv"), "w", newline="") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["local_capacity_zone", "period",
                         "discount_factor", "number_years_represented",
                         "local_capacity_requirement_mw",
                         "local_capacity_provision_mw",
                         "local_capacity_shortage_mw"])
        for (z, p) in m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                float(m.local_capacity_requirement_mw[z, p]),
                value(
                    m.Total_Local_Capacity_from_All_Sources_Expression_MW[z, p]
                ),
                value(m.Local_Capacity_Shortage_MW_Expression[z, p])
            ])


def save_duals(m):
    m.constraint_indices["Local_Capacity_Constraint"] = \
        ["local_capacity_zone", "period", "dual"]


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
        print("system local_capacity total")

    # Local capacity contribution
    nullify_sql = """
        UPDATE results_system_local_capacity
        SET local_capacity_requirement_mw = NULL,
        local_capacity_provision_mw = NULL,
        local_capacity_shortage_mw = NULL
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(scenario_id, subproblem, stage)
    spin_on_database_lock(conn=db, cursor=c, sql=nullify_sql, 
                          data=(scenario_id, subproblem, stage),
                          many=False)

    results = []
    with open(os.path.join(results_directory,
                           "local_capacity.csv"), "r") as \
            surface_file:
        reader = csv.reader(surface_file)

        next(reader)  # skip header
        for row in reader:
            local_capacity_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            local_capacity_req_mw = row[4]
            local_capacity_prov_mw = row[5]
            shortage_mw = row[6]

            results.append(
                (local_capacity_req_mw, local_capacity_prov_mw,
                 shortage_mw,
                 discount_factor, number_years,
                 scenario_id, local_capacity_zone, period)
            )

    update_sql = """
        UPDATE results_system_local_capacity
        SET local_capacity_requirement_mw = ?,
        local_capacity_provision_mw = ?,
        local_capacity_shortage_mw = ?,
        discount_factor = ?,
        number_years_represented = ?
        WHERE scenario_id = ?
        AND local_capacity_zone = ?
        AND period = ?"""
    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)

    # Update duals
    duals_results = []
    with open(os.path.join(results_directory, "Local_Capacity_Constraint.csv"),
              "r") as local_capacity_duals_file:
        reader = csv.reader(local_capacity_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )

    duals_sql = """
        UPDATE results_system_local_capacity
        SET dual = ?
        WHERE local_capacity_zone = ?
        AND period = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;"""

    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal carbon cost per MMt
    mc_sql = """
        UPDATE results_system_local_capacity
        SET local_capacity_marginal_cost_per_mw = 
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)
