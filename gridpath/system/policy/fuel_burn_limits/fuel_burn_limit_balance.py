# Copyright 2016-2022 Blue Marble Analytics LLC.
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

import csv
import os.path

from pyomo.environ import Var, Constraint, NonNegativeReals, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import fuel_burn_balance_components


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

    m.Total_Horizon_Fuel_Burn_By_Fuel_and_Fuel_BA_from_All_Sources_Expression = (
        Expression(
            m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
            rule=lambda mod, f, ba, bt, h: sum(
                getattr(mod, component)[f, ba, bt, h]
                for component in getattr(d, fuel_burn_balance_components)
            ),
        )
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
            mod.Total_Horizon_Fuel_Burn_By_Fuel_and_Fuel_BA_from_All_Sources_Expression[
                f, ba, bt, h
            ]
            - mod.Fuel_Burn_Limit_Overage_Unit_Expression[f, ba, bt, h]
            <= mod.fuel_burn_limit_unit[f, ba, bt, h]
        )

    m.Meet_Fuel_Burn_Limit_Constraint = Constraint(
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
                "balancing_type",
                "horizon",
                "number_years_represented",
                "discount_factor",
                "fuel",
                "fuel_ba",
                "fuel_burn_limit_unit",
                "total_fuel_burn_unit",
                "fuel_burn_overage_unit",
            ]
        )
        for (f, ba, bt, h) in m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT:
            writer.writerow(
                [
                    bt,
                    h,
                    m.number_years_represented[m.period[m.last_hrz_tmp[bt, h]]],
                    m.discount_factor[m.period[m.last_hrz_tmp[bt, h]]],
                    f,
                    ba,
                    m.fuel_burn_limit_unit[f, ba, bt, h],
                    value(
                        m.Total_Horizon_Fuel_Burn_By_Fuel_and_Fuel_BA_from_All_Sources_Expression[
                            f, ba, bt, h
                        ]
                    ),
                    value(m.Fuel_Burn_Limit_Overage_Unit_Expression[f, ba, bt, h]),
                ]
            )


def save_duals(m):
    m.constraint_indices["Meet_Fuel_Burn_Limit_Constraint"] = [
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
    if not quiet:
        print("system fuel burn limit balance")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_system_fuel_burn_limits",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "fuel_burn_limits.csv"), "r"
    ) as energy_target_file:
        reader = csv.reader(energy_target_file)

        next(reader)  # skip header
        for row in reader:
            [
                balancing_type,
                horizon,
                number_years_represented,
                discount_factor,
                fuel,
                fuel_burn_limit_ba,
                fuel_burn_limit_unit,
                total_fuel_burn_unit,
                fuel_burn_overage_unit,
            ] = row

            results.append(
                (
                    scenario_id,
                    subproblem,
                    stage,
                    balancing_type,
                    horizon,
                    number_years_represented,
                    discount_factor,
                    fuel,
                    fuel_burn_limit_ba,
                    fuel_burn_limit_unit,
                    total_fuel_burn_unit,
                    fuel_burn_overage_unit,
                )
            )

    insert_temp_sql = """
        INSERT INTO temp_results_system_fuel_burn_limits{scenario_id} (
            scenario_id,
            subproblem_id,
            stage_id,
            balancing_type_horizon,
            horizon,
            number_years_represented,
            discount_factor,
            fuel,
            fuel_burn_limit_ba,
            fuel_burn_limit_unit,
            total_fuel_burn_unit,
            fuel_burn_overage_unit
        )
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(
        scenario_id=scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_fuel_burn_limits (
            scenario_id,
            subproblem_id,
            stage_id,
            balancing_type_horizon,
            horizon,
            number_years_represented,
            discount_factor,
            fuel,
            fuel_burn_limit_ba,
            fuel_burn_limit_unit,
            total_fuel_burn_unit,
            fuel_burn_overage_unit
        )
        SELECT scenario_id,
            subproblem_id,
            stage_id,
            balancing_type_horizon,
            horizon,
            number_years_represented,
            discount_factor,
            fuel,
            fuel_burn_limit_ba,
            fuel_burn_limit_unit,
            total_fuel_burn_unit,
            fuel_burn_overage_unit
        FROM temp_results_system_fuel_burn_limits{scenario_id}
        ORDER BY scenario_id, fuel, fuel_burn_limit_ba, balancing_type_horizon,
        horizon, subproblem_id, stage_id;
        """.format(
        scenario_id=scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)

    # Update duals
    duals_results = []
    with open(
        os.path.join(results_directory, "Meet_Fuel_Burn_Limit_Constraint.csv"), "r"
    ) as duals_file:
        reader = csv.reader(duals_file)

        next(reader)  # skip header

        for row in reader:
            [fuel, fuel_burn_limit_ba, balancing_type, horizon, dual] = row
            duals_results.append(
                (
                    dual,
                    scenario_id,
                    subproblem,
                    stage,
                    balancing_type,
                    horizon,
                    fuel,
                    fuel_burn_limit_ba,
                )
            )

    duals_sql = """
        UPDATE results_system_fuel_burn_limits
        SET dual = ?
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?
        AND balancing_type_horizon = ?
        AND horizon = ?
        AND fuel = ?
        AND fuel_burn_limit_ba = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal energy-target cost per MWh
    mc_sql = """
        UPDATE results_system_fuel_burn_limits
        SET fuel_burn_limit_marginal_cost_per_unit =
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        and stage_id = ?;
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=mc_sql, data=(scenario_id, subproblem, stage), many=False
    )
