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
Aggregate fuel burn from the project-timepoint level to fuel / fuel balancing area -
period level.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import fuel_burn_balance_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    m.PRJ_FUEL_BAS = Set(dimen=3)

    m.PRJS_BY_FUEL_BA = Set(
        m.FUEL_BAS,
        within=m.FUEL_PRJS,
        initialize=lambda mod, f, ba: [
            prj for (prj, fuel, bln_a) in mod.PRJ_FUEL_BAS if f == fuel and ba == bln_a
        ],
    )

    def total_period_fuel_burn_by_fuel_ba_rule(mod, ba, p):
        """
        Calculate total fuel burn from all projects in a fuel / fuel balancing area.

        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Total_Fuel_Burn_by_Fuel_MMBtu[prj, f, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (prj, f, tmp) in mod.FUEL_PRJS_FUEL_OPR_TMPS
            if prj in mod.PRJS_BY_FUEL_BA[f, ba]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Period_Fuel_Burn_By_Fuel_and_Fuel_BA_Unit = Expression(
        m.FUEL_FUEL_BA_PERIODS_WITH_FUEL_BURN_LIMIT,
        rule=total_period_fuel_burn_by_fuel_ba_rule,
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds project emissions to carbon balance
    """

    getattr(dynamic_components, fuel_burn_balance_components).append(
        "Total_Period_Fuel_Burn_By_Fuel_and_Fuel_BA_Unit"
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
            "fuel_burn_by_fuel_and_fuel_ba.csv",
        ),
        "w",
        newline="",
    ) as carbon_results_file:
        writer = csv.writer(carbon_results_file)
        writer.writerow(
            [
                "fuel",
                "fuel_ba",
                "period",
                "discount_factor",
                "number_years_represented",
                "fuel_burn_limit_unit",
                "fuel_burn_unit",
            ]
        )
        for (f, ba, p) in m.FUEL_FUEL_BA_PERIODS_WITH_FUEL_BURN_LIMIT:
            writer.writerow(
                [
                    f,
                    ba,
                    p,
                    m.discount_factor[p],
                    m.number_years_represented[p],
                    float(m.fuel_burn_limit[f, ba, p]),
                    value(m.Total_Period_Fuel_Burn_By_Fuel_and_Fuel_BA_Unit[f, ba, p]),
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
    # Carbon emissions by in-zone projects
    if not quiet:
        print("system fuel burn")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_system_fuel_burn",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # # Load results into the temporary table
    # results = []
    # with open(
    #     os.path.join(results_directory, "carbon_cap_total_project.csv"), "r"
    # ) as emissions_file:
    #     reader = csv.reader(emissions_file)
    #
    #     next(reader)  # skip header
    #     for row in reader:
    #         carbon_cap_zone = row[0]
    #         period = row[1]
    #         carbon_cap = row[4]
    #         project_carbon_emissions = row[5]
    #
    #         results.append(
    #             (
    #                 scenario_id,
    #                 carbon_cap_zone,
    #                 period,
    #                 subproblem,
    #                 stage,
    #                 carbon_cap,
    #                 project_carbon_emissions,
    #             )
    #         )
    #
    # insert_temp_sql = """
    #     INSERT INTO
    #     temp_results_system_carbon_emissions{}
    #      (scenario_id, carbon_cap_zone, period, subproblem_id, stage_id,
    #      carbon_cap, in_zone_project_emissions)
    #      VALUES (?, ?, ?, ?, ?, ?, ?);
    #      """.format(
    #     scenario_id
    # )
    # spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)
    #
    # # Insert sorted results into permanent results table
    # insert_sql = """
    #     INSERT INTO results_system_carbon_emissions
    #     (scenario_id, carbon_cap_zone, period, subproblem_id, stage_id,
    #     carbon_cap, in_zone_project_emissions)
    #     SELECT
    #     scenario_id, carbon_cap_zone, period, subproblem_id, stage_id,
    #     carbon_cap, in_zone_project_emissions
    #     FROM temp_results_system_carbon_emissions{}
    #      ORDER BY scenario_id, carbon_cap_zone, period, subproblem_id,
    #     stage_id;
    #     """.format(
    #     scenario_id
    # )
    # spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
