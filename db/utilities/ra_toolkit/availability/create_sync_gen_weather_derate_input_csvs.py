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


from argparse import ArgumentParser
from multiprocessing import get_context
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database
from db.utilities.ra_toolkit.weather.create_sync_gen_input_csvs_common import (
    create_profile_csvs,
)

WEATHER_AV_ID_DEFAULT = 1
WEATHER_AV_NAME_DEFAULT = "ra_toolkit"
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
        "--exogenous_availability_weather_scenario_id",
        default=WEATHER_AV_ID_DEFAULT,
        help=f"Defaults to {WEATHER_AV_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-name",
        "--exogenous_availability_weather_scenario_name",
        default=WEATHER_AV_NAME_DEFAULT,
        help=f"Defaults to '{WEATHER_AV_NAME_DEFAULT}'.",
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

    parser.add_argument(
        "-parallel",
        "--n_parallel_projects",
        default=1,
        help="The number of projects to simulate in parallel. Defaults to 1.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_weather_availability_profile_csvs_pool(pool_datum):
    [
        db_path,
        project,
        exogenous_availability_weather_scenario_id,
        exogenous_availability_weather_scenario_name,
        stage_id,
        output_directory,
        overwrite,
    ] = pool_datum

    create_profile_csvs(
        db_path=db_path,
        project=project,
        profile_scenario_id=exogenous_availability_weather_scenario_id,
        profile_scenario_name=exogenous_availability_weather_scenario_name,
        stage_id=stage_id,
        output_directory=output_directory,
        overwrite=overwrite,
        param_name="availability_derate_weather",
        raw_data_table_name="raw_data_unit_availability_weather_derates",
        raw_data_units_table_name="raw_data_unit_availability_params",
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)
    if not parsed_args.quiet:
        print("Creating sync gen weather-dependent derates CSVs...")

    conn = connect_to_database(db_path=parsed_args.database)

    c = conn.cursor()
    projects = [
        prj[0]
        for prj in c.execute(
            "SELECT DISTINCT project FROM raw_data_unit_availability_params;"
        ).fetchall()
    ]

    pool_data = tuple(
        [
            [
                parsed_args.database,
                prj,
                parsed_args.exogenous_availability_weather_scenario_id,
                parsed_args.exogenous_availability_weather_scenario_name,
                parsed_args.stage_id,
                parsed_args.output_directory,
                parsed_args.overwrite,
            ]
            for prj in projects
        ]
    )

    # Pool must use spawn to work properly on Linux
    pool = get_context("spawn").Pool(int(parsed_args.n_parallel_projects))

    pool.map(create_weather_availability_profile_csvs_pool, pool_data)
    pool.close()


if __name__ == "__main__":
    main()
