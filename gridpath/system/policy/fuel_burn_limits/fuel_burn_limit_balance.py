# Copyright 2016-2021 Blue Marble Analytics LLC.
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
MMBtu [fuel burn unit] limit by horizon.
"""

from builtins import next
import csv
import os.path
import pandas as pd

from pyomo.environ import Var, Constraint, NonNegativeReals, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Fuel_Burn_Limit_Overage_Unit = Var(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT, within=NonNegativeReals
    )

    def violation_expression_rule(mod, f, ba, bt, h):
        return (
            mod.Fuel_Burn_Limit_Overage_Unit[f, ba, bt, h]
            * mod.fuel_burn_limit_allow_violation[f, ba]
        )

    m.Fuel_Burn_Limit_Overage_Unit_Expression = Expression(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        rule=violation_expression_rule,
    )

    def fuel_burn_limit_balance_rule(mod, f, ba, bt, h):
        """
        Total delivered energy-target-eligible energy must exceed target
        :param mod:
        :param z:
        :param bt:
        :param h:
        :return:
        """
        return (
            mod.Total_Period_Fuel_Burn_By_Fuel_and_Fuel_BA_Unit[f, ba, bt, h]
            - mod.Fuel_Burn_Limit_Overage_Unit_Expression[f, ba, bt, h]
            <= mod.fuel_burn_limit_unit[f, ba, bt, h]
        )

    m.Fuel_Burn_Limit_Constraint = Constraint(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        rule=fuel_burn_limit_balance_rule,
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
            "fuel_burn_limits.csv",
        ),
        "w",
        newline="",
    ) as fuel_burn_limit_results_file:
        writer = csv.writer(fuel_burn_limit_results_file)
        writer.writerow(
            [
                "fuel",
                "fuel_ba",
                "balancing_type",
                "horizon",
                "fuel_burn_limit_unit",
                "fuel_burn_unit",
                "fuel_burn_overage_unit",
            ]
        )
        for (f, ba, bt, h) in m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT:
            writer.writerow(
                [
                    f,
                    ba,
                    bt,
                    h,
                    m.fuel_burn_limit_unit[f, ba, bt, h],
                    value(
                        m.Total_Period_Fuel_Burn_By_Fuel_and_Fuel_BA_Unit[f, ba, bt, h]
                    ),
                    value(m.Fuel_Burn_Limit_Overage_Unit_Expression[f, ba, bt, h]),
                ]
            )


def save_duals(m):
    m.constraint_indices["Fuel_Burn_Limit_Constraint"] = [
        "fuel",
        "fuel_ba",
        "balancing_type",
        "horizon",
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
    # Delete prior results and create temporary import table for ordering
    # setup_results_import(
    #     conn=db,
    #     cursor=c,
    #     table="results_system_fuel_limits",
    #     scenario_id=scenario_id,
    #     subproblem=subproblem,
    #     stage=stage,
    # )

    # # Load results into the temporary table
    # results = []
    # with open(
    #     os.path.join(results_directory, "horizon_energy_target.csv"), "r"
    # ) as energy_target_file:
    #     reader = csv.reader(energy_target_file)
    #
    #     next(reader)  # skip header
    #     for row in reader:
    #         energy_target_zone = row[0]
    #         balancing_type = row[1]
    #         horizon = row[2]
    #         energy_target = row[3]
    #         energy_target_provision = row[4]
    #         curtailment = row[5]
    #         total = row[6]
    #         fraction_met = row[7]
    #         fraction_curtailed = row[8]
    #         shortage = row[9]
    #
    #         results.append(
    #             (
    #                 scenario_id,
    #                 energy_target_zone,
    #                 balancing_type,
    #                 horizon,
    #                 subproblem,
    #                 stage,
    #                 energy_target,
    #                 energy_target_provision,
    #                 curtailment,
    #                 total,
    #                 fraction_met,
    #                 fraction_curtailed,
    #                 shortage,
    #             )
    #         )
    #
    # insert_temp_sql = """
    #     INSERT INTO temp_results_system_horizon_energy_target{}
    #      (scenario_id, energy_target_zone, balancing_type_horizon, horizon,
    #      subproblem_id, stage_id, energy_target_mwh,
    #      delivered_energy_target_energy_mwh,
    #      curtailed_energy_target_energy_mwh, total_energy_target_energy_mwh,
    #      fraction_of_energy_target_met, fraction_of_energy_target_energy_curtailed,
    #      energy_target_shortage_mwh)
    #      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    #      """.format(
    #     scenario_id
    # )
    # spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)
    #
    # # Insert sorted results into permanent results table
    # insert_sql = """
    #     INSERT INTO results_system_horizon_energy_target
    #     (scenario_id, energy_target_zone, balancing_type_horizon, horizon,
    #     subproblem_id, stage_id, energy_target_mwh,
    #     delivered_energy_target_energy_mwh,
    #     curtailed_energy_target_energy_mwh, total_energy_target_energy_mwh,
    #     fraction_of_energy_target_met,
    #     fraction_of_energy_target_energy_curtailed,
    #     energy_target_shortage_mwh)
    #     SELECT scenario_id, energy_target_zone, balancing_type_horizon,
    #     horizon, subproblem_id, stage_id, energy_target_mwh,
    #     delivered_energy_target_energy_mwh, curtailed_energy_target_energy_mwh,
    #     total_energy_target_energy_mwh,
    #     fraction_of_energy_target_met, fraction_of_energy_target_energy_curtailed,
    #     energy_target_shortage_mwh
    #     FROM temp_results_system_horizon_energy_target{}
    #     ORDER BY scenario_id, energy_target_zone, balancing_type_horizon,
    #     horizon, subproblem_id, stage_id;
    #     """.format(
    #     scenario_id
    # )
    # spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
    #
    # # Update duals
    # duals_results = []
    # with open(
    #     os.path.join(results_directory, "Horizon_Energy_Target_Constraint.csv"), "r"
    # ) as energy_target_duals_file:
    #     reader = csv.reader(energy_target_duals_file)
    #
    #     next(reader)  # skip header
    #
    #     for row in reader:
    #         duals_results.append(
    #             (row[3], row[0], row[1], row[2], scenario_id, subproblem, stage)
    #         )
    #
    # duals_sql = """
    #     UPDATE results_system_horizon_energy_target
    #     SET dual = ?
    #     WHERE energy_target_zone = ?
    #     AND balancing_type_horizon = ?
    #     AND horizon = ?
    #     AND scenario_id = ?
    #     AND subproblem_id = ?
    #     AND stage_id = ?;
    #     """
    # spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)
    #
    # # # Calculate marginal energy-target cost per MWh
    # # mc_sql = """
    # #     UPDATE results_system_horizon_energy_target
    # #     SET energy_target_marginal_cost_per_mwh =
    # #     dual / (discount_factor * number_years_represented)
    # #     WHERE scenario_id = ?
    # #     AND subproblem_id = ?
    # #     and stage_id = ?;
    # #     """
    # # spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
    # #                       data=(scenario_id, subproblem, stage),
    # #                       many=False)
