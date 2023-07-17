# Copyright 2016-2020 Blue Marble Analytics LLC.
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
Constraint total carbon emissions to be less than cap
"""


import csv
import os.path

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import carbon_cap_balance_emission_components
from gridpath.common_functions import create_results_df
from gridpath.system.policy.carbon_cap import CARBON_CAP_ZONE_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Carbon_Cap_Overage = Var(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p):
        return mod.Carbon_Cap_Overage[z, p] * mod.carbon_cap_allow_violation[z]

    m.Carbon_Cap_Overage_Expression = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP, rule=violation_expression_rule
    )

    m.Total_Carbon_Emissions_from_All_Sources_Expression = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=lambda mod, z, p: sum(
            getattr(mod, component)[z, p]
            for component in getattr(d, carbon_cap_balance_emission_components)
        ),
    )

    def carbon_cap_target_rule(mod, z, p):
        """
        Total carbon emitted must be less than target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return (
            mod.Total_Carbon_Emissions_from_All_Sources_Expression[z, p]
            - mod.Carbon_Cap_Overage_Expression[z, p]
            <= mod.carbon_cap_target[z, p]
        )

    m.Carbon_Cap_Constraint = Constraint(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP, rule=carbon_cap_target_rule
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

    results_columns = [
        "total_emissions",
    ]
    data = [
        [
            z,
            p,
            value(m.Total_Carbon_Emissions_from_All_Sources_Expression[z, p]),
        ]
        for (z, p) in m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP
    ]
    results_df = create_results_df(
        index_columns=["carbon_cap_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, CARBON_CAP_ZONE_PRD_DF)[c] = None
    getattr(d, CARBON_CAP_ZONE_PRD_DF).update(results_df)


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    instance.constraint_indices["Carbon_Cap_Constraint"] = [
        "carbon_cap_zone",
        "period",
        "dual",
    ]


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

    # Update duals
    duals_results = []
    with open(
        os.path.join(results_directory, "Carbon_Cap_Constraint.csv"), "r"
    ) as carbon_cap_duals_file:
        reader = csv.reader(carbon_cap_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )
    duals_sql = """ 
        UPDATE results_system_carbon_cap
        SET dual = ?
        WHERE carbon_cap_zone = ?
        AND period = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;"""
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal carbon cost per emission
    mc_sql = """
        UPDATE results_system_carbon_cap
        SET carbon_cap_marginal_cost_per_emission = 
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=mc_sql, data=(scenario_id, subproblem, stage), many=False
    )
