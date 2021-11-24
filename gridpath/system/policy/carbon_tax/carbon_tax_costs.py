# Copyright 2021 (c) Crown Copyright, GC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Add the carbon tax cost components.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
import csv
import os.path

from pyomo.environ import Expression, value, NonNegativeReals, Var, Constraint

from db.common_functions import spin_on_database_lock


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    # Variables
    ###########################################################################

    m.Carbon_Tax_Cost = Var(
        m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX, within=NonNegativeReals
    )

    # Constraints
    ###########################################################################
    def carbon_tax_cost_constraint_rule(mod, z, p):
        return (
            mod.Carbon_Tax_Cost[z, p]
            >= (
                mod.Total_Carbon_Tax_Project_Emissions[z, p]
                - mod.Total_Carbon_Tax_Project_Allowance[z, p]
            )
            * mod.carbon_tax[z, p]
        )

    m.Carbon_Tax_Cost_Constraint = Constraint(
        m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX, rule=carbon_tax_cost_constraint_rule
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
    with open(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "results", "carbon_tax.csv"
        ),
        "w",
        newline="",
    ) as carbon_tax_results_file:
        writer = csv.writer(carbon_tax_results_file)
        writer.writerow(
            [
                "carbon_tax_zone",
                "period",
                "discount_factor",
                "number_years_represented",
                "carbon_tax_per_ton",
                "total_carbon_emissions_tons",
                "total_carbon_tax_allowance_tons",
                "total_carbon_tax_cost",
            ]
        )
        for (z, p) in m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX:
            writer.writerow(
                [
                    z,
                    p,
                    m.discount_factor[p],
                    m.number_years_represented[p],
                    float(m.carbon_tax[z, p]),
                    value(m.Total_Carbon_Tax_Project_Emissions[z, p]),
                    value(m.Total_Carbon_Tax_Project_Allowance[z, p]),
                    value(m.Carbon_Tax_Cost[z, p]),
                ]
            )


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
        print("system carbon tax emissions (total)")
    # Carbon emissions from imports
    # Prior results should have already been cleared by
    # system.policy.carbon_tax.aggregate_project_carbon_emissions,
    # then project total emissions imported
    # Update results_system_carbon_tax_emissions with NULL just in case (instead of
    # clearing prior results)
    nullify_sql = """
        UPDATE results_system_carbon_tax_emissions
        SET carbon_tax_cost = NULL
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(
        conn=db,
        cursor=c,
        sql=nullify_sql,
        data=(scenario_id, subproblem, stage),
        many=False,
    )

    results = []
    with open(os.path.join(results_directory, "carbon_tax.csv"), "r") as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            carbon_tax_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            costs = row[7]

            results.append(
                (
                    costs,
                    discount_factor,
                    number_years,
                    scenario_id,
                    carbon_tax_zone,
                    period,
                    subproblem,
                    stage,
                )
            )

    total_sql = """
        UPDATE results_system_carbon_tax_emissions
        SET carbon_tax_cost = ?,
        discount_factor = ?,
        number_years_represented = ?
        WHERE scenario_id = ?
        AND carbon_tax_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?;"""

    spin_on_database_lock(conn=db, cursor=c, sql=total_sql, data=results)
