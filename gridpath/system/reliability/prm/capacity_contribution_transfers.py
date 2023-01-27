# Copyright 2016-2023 Blue Marble Analytics LLC.
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

"""

import csv
import os.path
from pyomo.environ import Var, NonNegativeReals, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import prm_balance_provision_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    m.Transfer_Capacity_Contribution = Var(
        m.PRM_ZONES_CAPACITY_TRANSFER_ZONES,
        m.PERIODS,
        within=NonNegativeReals,
        initialize=0,
    )

    def total_transfers_from_init(mod, z, prd):
        return -sum(
            mod.Transfer_Capacity_Contribution[z, t_z, prd]
            for (zone, t_z) in mod.PRM_ZONES_CAPACITY_TRANSFER_ZONES
            if zone == z
        )

    m.Total_Transfers_from_PRM_Zone = Expression(
        m.PRM_ZONES, m.PERIODS, initialize=total_transfers_from_init
    )

    def total_transfers_to_init(mod, t_z, prd):
        return sum(
            mod.Transfer_Capacity_Contribution[z, t_z, prd]
            for (z, to_zone) in mod.PRM_ZONES_CAPACITY_TRANSFER_ZONES
            if to_zone == t_z
        )

    m.Total_Transfers_to_PRM_Zone = Expression(
        m.PRM_ZONES, m.PERIODS, initialize=total_transfers_to_init
    )

    # Add to balance constraint
    getattr(d, prm_balance_provision_components).append("Total_Transfers_from_PRM_Zone")
    getattr(d, prm_balance_provision_components).append("Total_Transfers_to_PRM_Zone")


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
            "capacity_contribution_transfers.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "prm_zone",
                "period",
                "capacity_contribution_transferred_from_mw",
                "capacity_contribution_transferred_to_mw",
            ]
        )
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow(
                [
                    z,
                    p,
                    value(m.Total_Transfers_from_PRM_Zone[z, p]),
                    value(m.Total_Transfers_to_PRM_Zone[z, p]),
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
        print("system prm capacity contribution transfers")
    # PRM contributions transferred from the PRM zone
    # Prior results should have already been cleared by
    # system.prm.aggregate_project_simple_prm_contribution,
    # then elcc_simple_mw imported
    # Update results_system_prm with NULL for surface contribution just in
    # case (instead of clearing prior results)
    nullify_sql = """
        UPDATE results_system_prm
        SET capacity_contribution_transferred_from_mw = NULL, 
        capacity_contribution_transferred_from_mw = NULL
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
        os.path.join(results_directory, "capacity_contribution_transfers.csv"),
        "r",
    ) as surface_file:
        reader = csv.reader(surface_file)

        next(reader)  # skip header
        for row in reader:
            prm_zone = row[0]
            period = row[1]
            transfers_from = row[2]
            transfers_to = row[3]

            results.append(
                (transfers_from, transfers_to, scenario_id, prm_zone, period,
                 subproblem, stage)
            )

    update_sql = """
        UPDATE results_system_prm
        SET capacity_contribution_transferred_from_mw = ?, 
        capacity_contribution_transferred_to_mw = ?
        WHERE scenario_id = ?
        AND prm_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?
        """
    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)
