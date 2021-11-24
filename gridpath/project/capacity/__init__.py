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
This package contains modules to describe the available capacity and the
capacity-associated costs of generation, storage, and demand-side
infrastructure 'projects' in the optimization problem.
"""

import csv
import os.path

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import


# Database
###############################################################################


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
    # First import the capacity_all results; the capacity type modules will
    # then update the database tables rather than insert (all projects
    # should have been inserted here)
    # Delete prior results and create temporary import table for ordering
    if not quiet:
        print("project capacity")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_capacity",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "capacity_all.csv"), "r"
    ) as capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            capacity_type = row[2]
            technology = row[3]
            load_zone = row[4]
            capacity_mw = row[5]
            hyb_gen_capacity_mw = None if row[6] == "" else row[6]
            hyb_stor_capacity_mw = None if row[7] == "" else row[7]
            energy_capacity_mwh = None if row[8] == "" else row[8]

            results.append(
                (
                    scenario_id,
                    project,
                    period,
                    subproblem,
                    stage,
                    capacity_type,
                    technology,
                    load_zone,
                    capacity_mw,
                    hyb_gen_capacity_mw,
                    hyb_stor_capacity_mw,
                    energy_capacity_mwh,
                )
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, hyb_gen_capacity_mw, 
        hyb_stor_capacity_mw, energy_capacity_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_capacity
        (scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, hyb_gen_capacity_mw, 
        hyb_stor_capacity_mw, energy_capacity_mwh)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, hyb_gen_capacity_mw, 
        hyb_stor_capacity_mw, energy_capacity_mwh
        FROM temp_results_project_capacity{}
        ORDER BY scenario_id, project, period, subproblem_id, 
        stage_id;""".format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
