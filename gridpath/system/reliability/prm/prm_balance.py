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
Constraint total PRM contribution to be more than or equal to the requirement.
"""


import csv
import os.path

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import prm_balance_provision_components
from gridpath.common_functions import create_results_df
from gridpath.system.reliability.prm import PRM_ZONE_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Total_PRM_from_All_Sources_Expression = Expression(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=lambda mod, z, p: sum(
            getattr(mod, component)[z, p]
            for component in getattr(d, prm_balance_provision_components)
        ),
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
        return (
            mod.Total_PRM_from_All_Sources_Expression[z, p]
            + mod.PRM_Shortage_MW_Expression[z, p]
            >= mod.prm_requirement_mw[z, p]
        )

    m.PRM_Constraint = Constraint(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT, rule=prm_requirement_rule
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
        "elcc_total_mw",
        "prm_shortage_mw",
    ]
    data = [
        [
            z,
            p,
            value(m.Total_PRM_from_All_Sources_Expression[z, p]),
            value(m.PRM_Shortage_MW_Expression[z, p]),
        ]
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT
    ]
    results_df = create_results_df(
        index_columns=["prm_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, PRM_ZONE_PRD_DF)[c] = None
    getattr(d, PRM_ZONE_PRD_DF).update(results_df)


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    instance.constraint_indices["PRM_Constraint"] = ["prm_zone", "period", "dual"]


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
        os.path.join(results_directory, "PRM_Constraint.csv"), "r"
    ) as prm_duals_file:
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
    spin_on_database_lock(
        conn=db, cursor=c, sql=mc_sql, data=(scenario_id, subproblem, stage), many=False
    )
