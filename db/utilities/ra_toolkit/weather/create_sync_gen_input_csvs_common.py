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
import pandas as pd

from db.common_functions import connect_to_database


def create_profile_csvs(
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
):
    conn = connect_to_database(db_path=db_path)

    # Get the weighted cap factor for each of the project's constituent units,
    # get the UNION of these tables, and then find the project cap factor
    # with SUM and GROUP BY
    query = f"""
        SELECT year AS weather_iteration,
        {stage_id} AS stage_id, 
        hour_of_year as timepoint, sum(weighted_{param_name}) as {param_name}
            FROM (
            SELECT year, month, day_of_month, hour_of_day, unit, 
            project, unit_weight, {param_name}, unit_weight * {param_name} as weighted_{param_name},
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
