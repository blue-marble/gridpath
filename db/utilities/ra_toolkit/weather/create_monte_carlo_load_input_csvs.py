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

import sys
from argparse import ArgumentParser
import os.path
import pandas as pd
import sqlite3

from db.common_functions import connect_to_database

BINS_ID_DEFAULT = 1
DRAWS_ID_DEFAULT = 1
LOAD_SCENARIO_ID_DEFAULT = 1  # it's 5 in the test examples
LOAD_SCENARIO_NAME_DEFAULT = "ra_toolkit"
STAGE_ID_DEFAULT = 1


# TODO: parallelize
# TODO: make sure hybrids are properly incorporated


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database")

    parser.add_argument(
        "-bins_id",
        "--weather_bins_id",
        default=BINS_ID_DEFAULT,
        help=f"Defaults to {BINS_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-draws_id",
        "--weather_draws_id",
        default=DRAWS_ID_DEFAULT,
        help=f"Defaults to {DRAWS_ID_DEFAULT}.",
    )
    parser.add_argument("-csv", "--input_csv")

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
    weather_bins_id,
    weather_draws_id,
    input_csv,
    output_directory,
    load_scenario_id,
    load_scenario_name,
    stage_id,
    overwrite,
):
    c = conn.cursor()

    # Get load zone units
    df = pd.read_sql("""SELECT * FROM raw_data_load_zone_units;""", conn)

    # Create a dictionary of the form {timeseries: project: [units]}
    load_zone_unit_dict = {}

    for index, row in df.iterrows():
        if row["load_zone"] not in load_zone_unit_dict.keys():
            load_zone_unit_dict[row["load_zone"]] = [
                (row["load_zone_unit"], row["unit_weight"])
            ]
        else:
            load_zone_unit_dict[row["project"]].append(
                (row["load_zone_unit"], row["unit_weight"])
            )

    draws = c.execute(
        f"""
                SELECT weather_iteration, draw_number,
                load_year, load_month,
                load_day_of_month
                FROM inputs_aux_weather_iterations
                WHERE weather_bins_id = {weather_bins_id}
                AND weather_draws_id = {weather_draws_id}
                ;
                """
    ).fetchall()

    draw_n = 0
    for d in draws:
        (weather_iteration, draw_number, year, month, day_of_month) = d

        for load_zone in load_zone_unit_dict.keys():
            unit_queries = [
                f"""
                SELECT year, month, day_of_month, hour_of_day, load_zone_unit, 
                load_mw * {weight} as weighted_load
                FROM raw_data_system_load
                WHERE year = {year}
                AND month = {month}
                AND day_of_month = {day_of_month}
                AND load_zone_unit = '{unit}'
                """
                for (unit, weight) in load_zone_unit_dict[load_zone]
            ]

            union_query = " UNION ".join(unit_queries)

            load_zone_query = (
                f"""
                        SELECT 
                        '{load_zone}' AS load_zone,
                        {weather_iteration} AS weather_iteration, 
                        {stage_id} AS stage_id,
                        ({draw_number}-1)*24+hour_of_day AS timepoint, 
                        sum(weighted_load) AS load_mw
                        FROM (
                    """
                + union_query
                + f""")
                    GROUP BY year, month, day_of_month, hour_of_day
                    ;
                    """
            )

            # Put into a dataframe and add to file
            df = pd.read_sql(load_zone_query, con=conn)

            filename = os.path.join(
                output_directory,
                f"{load_scenario_id}_{load_scenario_name}.csv",
            )
            if not os.path.exists(filename) or (overwrite and draw_n == 0):
                mode = "w"
                write_header = True
            else:
                mode = "a"
                write_header = False
            df.to_csv(
                filename,
                mode=mode,
                header=write_header,
                index=False,
            )

            draw_n += 1


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating Monte Carlo load profile CSVs...")

    conn = connect_to_database(db_path=parsed_args.database)

    create_load_profile_csv(
        conn=conn,
        weather_bins_id=parsed_args.weather_bins_id,
        weather_draws_id=parsed_args.weather_draws_id,
        input_csv=parsed_args.input_csv,
        output_directory=parsed_args.output_directory,
        load_scenario_id=parsed_args.load_scenario_id,
        load_scenario_name=parsed_args.load_scenario_name,
        stage_id=parsed_args.stage_id,
        overwrite=parsed_args.overwrite,
    )


if __name__ == "__main__":
    main()
