# Copyright 2016-2025 Blue Marble Analytics LLC.
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
Monte Carlo Loads
*****************

Create GridPath Monte Carlo load profile inputs. Before running this module,
you will need to create weather draws with the ``create_monte_carlo_draws``
module (see :ref:`monte-carlo-draws-section-ref`).

=====
Usage
=====

>>> gridpath_run_data_toolkit --single_step create_monte_carlo_load_input_csvs --settings_csv PATH/TO/SETTINGS/CSV

===================
Input prerequisites
===================

This module assumes the following raw input database tables have been populated:
    * raw_data_system_load
    * user_defined_load_zone_units
    * aux_weather_iterations (see the ``create_monte_carlo_draws`` step for how to create synthetic weather years and populate this table)

=========
Settings
=========
    * database
    * output_directory
    * load_scenario_id
    * load_scenario_name
    * stage_id
    * overwrite
    * weather_bins_id
    * weather_draws_id

"""

import sys
from argparse import ArgumentParser
import os.path
import pandas as pd

from data_toolkit.system.common_methods import (
    create_load_scenario_csv,
    create_load_components_scenario_csv,
)
from db.common_functions import connect_to_database

BINS_ID_DEFAULT = 1
DRAWS_ID_DEFAULT = 1
LOAD_SCENARIO_ID_DEFAULT = 1  # it's 6 in the test examples
LOAD_SCENARIO_NAME_DEFAULT = "ra_toolkit"
LOAD_COMPONENTS_SCENARIO_ID_DEFAULT = 1  # it's 6 in the test examples
LOAD_COMPONENTS_SCENARIO_NAME_DEFAULT = "ra_toolkit"
LOAD_LEVELS_SCENARIO_ID_DEFAULT = 1  # it's 6 in the test examples
LOAD_LEVELS_SCENARIO_NAME_DEFAULT = "ra_toolkit"
STAGE_ID_DEFAULT = 1
LOAD_COMPONENT_NAME_DEFAULT = "all"


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
        "-lc_id",
        "--load_components_scenario_id",
        default=LOAD_COMPONENTS_SCENARIO_ID_DEFAULT,
        help=f"Defaults to {LOAD_COMPONENTS_SCENARIO_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-lc_name",
        "--load_components_scenario_name",
        default=LOAD_COMPONENTS_SCENARIO_NAME_DEFAULT,
        help=f"Defaults to '{LOAD_COMPONENTS_SCENARIO_NAME_DEFAULT}'.",
    )
    parser.add_argument(
        "-ll_id",
        "--load_levels_scenario_id",
        default=LOAD_LEVELS_SCENARIO_ID_DEFAULT,
        help=f"Defaults to {LOAD_LEVELS_SCENARIO_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-ll_name",
        "--load_levels_scenario_name",
        default=LOAD_LEVELS_SCENARIO_NAME_DEFAULT,
        help=f"Defaults to '{LOAD_LEVELS_SCENARIO_NAME_DEFAULT}'.",
    )
    parser.add_argument(
        "-stage",
        "--stage_id",
        default=STAGE_ID_DEFAULT,
        help=f"Defaults to '{STAGE_ID_DEFAULT}",
    )

    parser.add_argument(
        "-comp",
        "--load_component",
        default=LOAD_COMPONENT_NAME_DEFAULT,
        help=f"Defaults to '{LOAD_COMPONENT_NAME_DEFAULT}",
    )

    parser.add_argument(
        "-l_o",
        "--load_scenario_overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing CSV files.",
    )
    parser.add_argument(
        "-lc_o",
        "--load_components_overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing CSV files.",
    )
    parser.add_argument(
        "-ll_o",
        "--load_levels_overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing CSV files.",
    )

    parser.add_argument(
        "-skip_l",
        "--skip_load_scenario",
        default=False,
        action="store_true",
        help="Don't create load_scenario file.",
    )
    parser.add_argument(
        "-skip_lc",
        "--skip_load_components",
        default=False,
        action="store_true",
        help="Don't create load components file.",
    )
    parser.add_argument(
        "-skip_ll",
        "--skip_load_levels",
        default=False,
        action="store_true",
        help="Don't create load levels file.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_load_levels_csv(
    conn,
    weather_bins_id,
    weather_draws_id,
    output_directory,
    load_levels_scenario_id,
    load_levels_scenario_name,
    stage_id,
    load_component_name,
    overwrite_load_levels_csv,
):
    """
    This module will create load profiles for each synthetic weather
    iteration created with the ``create_monte_carlo_draws`` GridPath Data
    Toolkit module (based on the weather_bins_id and weather_draws_id).
    """
    c = conn.cursor()

    # Get load zone units
    df = pd.read_sql("""SELECT * FROM user_defined_load_zone_units;""", conn)

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
                FROM aux_weather_iterations
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
                        '{load_component_name}' AS load_component,
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
                "load_levels",
                f"{load_levels_scenario_id}_{load_levels_scenario_name}.csv",
            )
            if not os.path.exists(filename) or (
                overwrite_load_levels_csv and draw_n == 0
            ):
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

    os.makedirs(parsed_args.output_directory, exist_ok=True)
    os.makedirs(
        os.path.join(parsed_args.output_directory, "load_components"), exist_ok=True
    )
    os.makedirs(
        os.path.join(parsed_args.output_directory, "load_levels"), exist_ok=True
    )

    conn = connect_to_database(db_path=parsed_args.database)

    if not parsed_args.skip_load_scenario:
        create_load_scenario_csv(
            output_directory=parsed_args.output_directory,
            load_scenario_id=parsed_args.load_scenario_id,
            load_scenario_name=parsed_args.load_scenario_name,
            load_components_scenario_id=parsed_args.load_components_scenario_id,
            load_levels_scenario_id=parsed_args.load_levels_scenario_id,
            overwrite_load_scenario_csv=parsed_args.load_scenario_overwrite,
        )

    if not parsed_args.skip_load_components:
        create_load_components_scenario_csv(
            conn=conn,
            output_directory=parsed_args.output_directory,
            load_component_name=parsed_args.load_component,
            load_components_scenario_id=parsed_args.load_components_scenario_id,
            load_components_scenario_name=parsed_args.load_components_scenario_name,
            overwrite_load_components_csv=parsed_args.load_components_overwrite,
        )

    if not parsed_args.skip_load_levels:
        create_load_levels_csv(
            conn=conn,
            weather_bins_id=parsed_args.weather_bins_id,
            weather_draws_id=parsed_args.weather_draws_id,
            output_directory=parsed_args.output_directory,
            load_levels_scenario_id=parsed_args.load_levels_scenario_id,
            load_levels_scenario_name=parsed_args.load_levels_scenario_name,
            stage_id=parsed_args.stage_id,
            load_component_name=parsed_args.load_component,
            overwrite_load_levels_csv=parsed_args.load_levels_overwrite,
        )


if __name__ == "__main__":
    main()
