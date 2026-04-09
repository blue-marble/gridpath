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

import os.path
from argparse import Namespace
from multiprocessing import get_context
from sqlite3 import Connection

import pandas as pd

from data_toolkit.project.common_methods import create_iterations_csv
from db.common_functions import connect_to_database


def get_sync_project_pool_and_make_profile_csvs(
    db_path,
    profile_scenario_id,
    profile_scenario_name,
    stage_id,
    output_directory,
    overwrite,
    n_parallel_projects,
):

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    projects = [
        prj[0]
        for prj in c.execute(
            "SELECT DISTINCT project FROM raw_data_var_project_units;"
        ).fetchall()
    ]

    pool_data = tuple(
        [
            [
                db_path,
                prj,
                profile_scenario_id,
                profile_scenario_name,
                stage_id,
                output_directory,
                overwrite,
            ]
            for prj in projects
        ]
    )

    # Pool must use spawn to work properly on Linux
    pool = get_context("spawn").Pool(int(n_parallel_projects))

    pool.map(create_project_profile_csv_pool, pool_data)
    pool.close()

    conn.close()


def create_project_profile_csv(
    db_path,
    project,
    profile_scenario_id,
    profile_scenario_name,
    stage_id,
    output_directory,
    overwrite,
    param_name,
    raw_data_table_name,
    raw_data_units_table_name,
    no_hydro_iteration=False,
):
    conn = connect_to_database(db_path=db_path)

    # Get the weighted cap factor for each of the project's constituent units,
    # get the UNION of these tables, and then find the project cap factor
    # with SUM and GROUP BY
    hydro_iter_sql = "" if no_hydro_iteration else "0 AS hydro_iteration,"
    query = f"""
        SELECT year AS weather_iteration, 
        {hydro_iter_sql}
        {stage_id} AS stage_id, 
        hour_of_year as timepoint, sum(weighted_{param_name}) as {param_name}
            FROM (
            SELECT year, month, day_of_month, hour_of_day, unit, 
            project, unit_weight, value, unit_weight * value as 
            weighted_{param_name},
                (CAST(
                    strftime('%j',
                        year || '-' || 
                        CASE
                        WHEN month > 9 THEN month
                        ELSE '0' || month END
                        || '-' || 
                        CASE
                        WHEN day_of_month > 9 THEN day_of_month
                        ELSE '0' || day_of_month END
                        ) AS DECIMAL
                    ) - 1) * 24 + hour_of_day AS hour_of_year
            FROM {raw_data_table_name}
            JOIN {raw_data_units_table_name}
            USING (unit)
            WHERE project = '{project}'
            )
        GROUP BY year, hour_of_year
        ORDER BY year, hour_of_year
    """

    # Put into a dataframe and add to file
    df = pd.read_sql(query, con=conn)

    filename = os.path.join(
        output_directory,
        f"{project}-{profile_scenario_id}-" f"{profile_scenario_name}.csv",
    )

    if overwrite:
        mode = "w"
    else:
        mode = "a"

    write_header = not os.path.exists(filename)

    df.to_csv(
        filename,
        mode=mode,
        header=True if mode == "w" or write_header else False,
        index=False,
    )

    # Create iterations CSV
    iterations_directory = os.path.join(output_directory, "iterations")
    os.makedirs(iterations_directory, exist_ok=True)
    create_iterations_csv(
        iterations_directory=iterations_directory,
        project=project,
        profile_id=profile_scenario_id,
        profile_name=profile_scenario_name,
        varies_by_weather=1,
        varies_by_hydro=0,
        overwrite=True,
    )

    conn.close()


def create_project_profile_csv_pool(pool_datum):
    [
        db_path,
        project,
        variable_generator_profile_scenario_id,
        variable_generator_profile_scenario_name,
        stage_id,
        output_directory,
        overwrite,
    ] = pool_datum

    create_project_profile_csv(
        db_path=db_path,
        project=project,
        profile_scenario_id=variable_generator_profile_scenario_id,
        profile_scenario_name=variable_generator_profile_scenario_name,
        stage_id=stage_id,
        output_directory=output_directory,
        overwrite=overwrite,
        param_name="cap_factor",
        raw_data_table_name="raw_data_var_profiles",
        raw_data_units_table_name="raw_data_var_project_units",
    )
