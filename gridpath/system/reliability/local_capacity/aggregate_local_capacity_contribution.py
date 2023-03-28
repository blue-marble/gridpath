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
Aggregate simple local capacity contribution from the project level to the
local-capacity-zone level for each period.
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import (
    local_capacity_balance_provision_components,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    def total_local_capacity_provision_rule(mod, z, p):
        """

        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Local_Capacity_Contribution_MW[g, p]
            for g in mod.LOCAL_CAPACITY_PROJECTS_BY_LOCAL_CAPACITY_ZONE[z]
            if (g, p) in mod.LOCAL_CAPACITY_PRJ_OPR_PRDS
        )

    m.Total_Local_Capacity_Contribution_MW = Expression(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=total_local_capacity_provision_rule,
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds contribution to local capacity provision components
    """

    getattr(dynamic_components, local_capacity_balance_provision_components).append(
        "Total_Local_Capacity_Contribution_MW"
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
            "local_capacity_contribution.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["local_capacity_zone", "period", "contribution_mw"])
        for z, p in m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([z, p, value(m.Total_Local_Capacity_Contribution_MW[z, p])])


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
        print("system local capacity")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_system_local_capacity",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "local_capacity_contribution.csv"), "r"
    ) as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            local_capacity_zone = row[0]
            period = row[1]
            elcc = row[2]

            results.append(
                (scenario_id, local_capacity_zone, period, subproblem, stage, elcc)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_local_capacity{}
         (scenario_id, local_capacity_zone, 
         period, subproblem_id, stage_id, local_capacity_provision_mw)
         VALUES (?, ?, ?, ?, ?, ?);""".format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_local_capacity
        (scenario_id, local_capacity_zone, 
        period, subproblem_id, stage_id, local_capacity_provision_mw)
        SELECT scenario_id, local_capacity_zone, period, 
        subproblem_id, stage_id, local_capacity_provision_mw
        FROM temp_results_system_local_capacity{}
        ORDER BY scenario_id, local_capacity_zone, period, subproblem_id, 
        stage_id;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
