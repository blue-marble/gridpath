# Copyright 2022 (c) Crown Copyright, GC.
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
Constraint total carbon emissions to be less than performance standard
"""
from __future__ import division
from __future__ import print_function

from builtins import next
import csv
import os.path

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import carbon_cap_balance_emission_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Performance_Standard_Overage = Var(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        within=NonNegativeReals,
    )

    def violation_expression_rule(mod, z, p):
        return (
            mod.Performance_Standard_Overage[z, p]
            * mod.performance_standard_allow_violation[z]
        )

    m.Performance_Standard_Overage_Expression = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        rule=violation_expression_rule,
    )

    def performance_standard_rule(mod, z, p):
        """
        Total carbon emitted must be less than performance standard
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Performance_Standard_Project_Emissions[
            z, p
        ] - mod.Performance_Standard_Overage_Expression[z, p] <= (
            mod.Total_Performance_Standard_Project_Energy[z, p]
            * mod.performance_standard[z, p]
        )

    m.Performance_Standard_Constraint = Constraint(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        rule=performance_standard_rule,
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
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "performance_standard.csv",
        ),
        "w",
        newline="",
    ) as performance_standard_results_file:
        writer = csv.writer(performance_standard_results_file)
        writer.writerow(
            [
                "performance_standard_zone",
                "period",
                "discount_factor",
                "number_years_represented",
                "performance_standard_tco2_per_mwh",
                "performance_standard_carbon_emissions_tco2",
                "performance_standard_total_energy_mwh",
                "performance_standard_overage",
            ]
        )
        for (z, p) in m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD:
            writer.writerow(
                [
                    z,
                    p,
                    m.discount_factor[p],
                    m.number_years_represented[p],
                    float(m.performance_standard[z, p]),
                    value(m.Total_Performance_Standard_Project_Emissions[z, p]),
                    value(m.Total_Performance_Standard_Project_Energy[z, p]),
                    value(m.Performance_Standard_Overage_Expression[z, p]),
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
        print("system performance standard")
    nullify_sql = """
        UPDATE results_system_performance_standard
        SET performance_standard_overage = NULL
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
    with open(
        os.path.join(results_directory, "performance_standard.csv"), "r"
    ) as performance_standard_file:
        reader = csv.reader(performance_standard_file)

        next(reader)  # skip header
        for row in reader:
            performance_standard_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            overage = row[5]

            results.append(
                (
                    overage,
                    discount_factor,
                    number_years,
                    scenario_id,
                    performance_standard_zone,
                    period,
                    subproblem,
                    stage,
                )
            )

    total_sql = """
        UPDATE results_system_performance_standard
        SET performance_standard_overage = ?,
        discount_factor = ?,
        number_years_represented = ?
        WHERE scenario_id = ?
        AND performance_standard_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?;"""

    spin_on_database_lock(conn=db, cursor=c, sql=total_sql, data=results)
