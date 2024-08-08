# Copyright 2016-2024 Blue Marble Analytics LLC.
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

import sys
from argparse import ArgumentParser
import os.path
import pandas as pd
import sqlite3

from db.common_functions import connect_to_database

LOAD_SCENARIO_ID_DEFAULT = 1
LOAD_SCENARIO_NAME_DEFAULT = "ra_toolkit"
STAGE_ID_DEFAULT = 1


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database")

    parser.add_argument("-out_dir", "--output_directory")
    parser.add_argument(
        "-id",
        "--load_scenario_id",
        default=LOAD_SCENARIO_ID_DEFAULT,
        help=f"Defaults to {LOAD_SCENARIO_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-name",
        "--load_scenario_name",
        default=LOAD_SCENARIO_NAME_DEFAULT,
        help=f"Defaults to '{LOAD_SCENARIO_NAME_DEFAULT}'.",
    )

    parser.add_argument(
        "-stage",
        "--stage_id",
        default=STAGE_ID_DEFAULT,
        help=f"Defaults to '{STAGE_ID_DEFAULT}",
    )

    parser.add_argument(
        "-o",
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing CSV files.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_load_profile_csv(
    conn,
    output_directory,
    load_scenario_id,
    load_scenario_name,
    stage_id,
    overwrite,
):
    """
    Create load profile CSVs from the raw data
    Assumes timepoints will be 1 through 8760 for each year
    """

    query = f"""
        SELECT load_zone, year AS weather_iteration, {stage_id} as stage_id, 
        hour_of_year as timepoint, sum(weighted_load_mw) as load_mw
        FROM (
        SELECT year, month, day_of_month, hour_of_day, load_zone_unit, load_zone, unit_weight, load_mw, unit_weight * load_mw as weighted_load_mw,
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
        FROM raw_data_system_load
        JOIN raw_data_load_zone_units
        USING (load_zone_unit)
        )
    GROUP BY load_zone, year, hour_of_year
    """

    # Put into a dataframe and add to file
    df = pd.read_sql(query, con=conn)

    filename = os.path.join(
        output_directory,
        f"{load_scenario_id}_{load_scenario_name}.csv",
    )
    if overwrite:
        mode = "w"
        write_header = True
    else:
        mode = "a"
        write_header = not os.path.exists(filename)

    df.to_csv(
        filename,
        mode=mode,
        header=write_header,
        index=False,
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating sync load profile CSVs...")

    conn = connect_to_database(db_path=parsed_args.database)

    create_load_profile_csv(
        conn=conn,
        output_directory=parsed_args.output_directory,
        load_scenario_id=parsed_args.load_scenario_id,
        load_scenario_name=parsed_args.load_scenario_name,
        stage_id=parsed_args.stage_id,
        overwrite=parsed_args.overwrite,
    )


if __name__ == "__main__":
    main()
