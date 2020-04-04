#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Constraint total carbon emissions to be less than cap
"""
from __future__ import division
from __future__ import print_function

from builtins import next
import csv
import os.path

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import \
    carbon_cap_balance_emission_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.Carbon_Cap_Overage_MMt = Var(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p):
        return mod.Carbon_Cap_Overage_MMt[z, p] * \
               mod.carbon_cap_allow_violation[z]

    m.Carbon_Cap_Overage_MMt_Expression = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=violation_expression_rule
    )

    m.Total_Carbon_Emissions_from_All_Sources_Expression = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=lambda mod, z, p:
        sum(getattr(mod, component)[z, p] for component
            in getattr(d, carbon_cap_balance_emission_components)
            )
    )

    def carbon_cap_target_rule(mod, z, p):
        """
        Total carbon emitted must be less than target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Carbon_Emissions_from_All_Sources_Expression[z, p] \
            - mod.Carbon_Cap_Overage_MMt_Expression[z, p] * 10**6 \
            <= mod.carbon_cap_target_mmt[z, p] * 10**6  # convert to tons

    m.Carbon_Cap_Constraint = Constraint(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=carbon_cap_target_rule
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
                           "carbon_cap.csv"), "w", newline="") as carbon_cap_results_file:
        writer = csv.writer(carbon_cap_results_file)
        writer.writerow(["carbon_cap_zone", "period",
                         "discount_factor", "number_years_represented",
                         "carbon_cap_target_mmt",
                         "carbon_emissions_mmt",
                         "carbon_cap_overage_mmt"])
        for (z, p) in m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                float(m.carbon_cap_target_mmt[z, p]),
                value(m.Total_Carbon_Emissions_from_All_Sources_Expression[z, p]
                      / 10**6),
                value(m.Carbon_Cap_Overage_MMt_Expression[z, p])# MMT
            ])


def save_duals(m):
    m.constraint_indices["Carbon_Cap_Constraint"] = \
        ["carbon_cap_zone", "period", "dual"]


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
        print("system carbon emissions (total)")
    # Carbon emissions from imports
    # Prior results should have already been cleared by
    # system.policy.carbon_cap.aggregate_project_carbon_emissions,
    # then project total emissions imported
    # Update results_system_carbon_emissions with NULL just in case (instead of
    # clearing prior results)
    nullify_sql = """
        UPDATE results_system_carbon_emissions
        SET total_emissions_mmt = NULL,
        carbon_cap_overage_mmt = NULL
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=nullify_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)

    results = []
    with open(os.path.join(results_directory,
                           "carbon_cap.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            carbon_cap_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            total_emissions_mmt = row[5]
            overage = row[6]
            
            results.append(
                (total_emissions_mmt, overage, discount_factor, number_years,
                 scenario_id, carbon_cap_zone, period,
                 subproblem, stage)
            )

    total_sql = """
        UPDATE results_system_carbon_emissions
        SET total_emissions_mmt = ?,
        carbon_cap_overage_mmt = ?,
        discount_factor = ?,
        number_years_represented = ?
        WHERE scenario_id = ?
        AND carbon_cap_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?;"""

    spin_on_database_lock(conn=db, cursor=c, sql=total_sql, data=results)

    # Update duals
    duals_results = []
    with open(os.path.join(results_directory, "Carbon_Cap_Constraint.csv"),
              "r") as carbon_cap_duals_file:
        reader = csv.reader(carbon_cap_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )
    duals_sql = """ 
        UPDATE results_system_carbon_emissions
        SET dual = ?
        WHERE carbon_cap_zone = ?
        AND period = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;"""
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal carbon cost per MMt
    mc_sql = """
        UPDATE results_system_carbon_emissions
        SET carbon_cap_marginal_cost_per_mmt = 
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)
