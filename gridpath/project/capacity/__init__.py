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
This package contains modules to describe the available capacity and the
capacity-associated costs of generation, storage, and demand-side
infrastructure 'projects' in the optimization problem.
"""

import os.path
import pandas as pd

from db.common_functions import spin_on_database_lock_generic
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
        table="results_project_period",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    df = pd.read_csv(os.path.join(results_directory, "project_period.csv"))
    df["scenario_id"] = scenario_id
    df["subproblem_id"] = subproblem
    df["stage_id"] = stage

    spin_on_database_lock_generic(
        command=df.to_sql(
            name="results_project_period", con=db, if_exists="append", index=False
        )
    )
