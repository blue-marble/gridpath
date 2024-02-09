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
import sys

from db.utilities.ra_toolkit.weather.create_monte_carlo_gen_input_csvs_common import (
    create_variable_profile_csvs,
)

BINS_ID_DEFAULT = 1
DRAWS_ID_DEFAULT = 1
VAR_ID_DEFAULT = 1
VAR_NAME_DEFAULT = "ra_toolkit"
STAGE_ID_DEFAULT = 1


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

    parser.add_argument("-out_dir", "--output_directory")
    parser.add_argument(
        "-id",
        "--variable_generator_profile_scenario_id",
        default=VAR_ID_DEFAULT,
        help=f"Defaults to {VAR_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-name",
        "--variable_generator_profile_scenario_name",
        default=VAR_NAME_DEFAULT,
        help=f"Defaults to '{VAR_NAME_DEFAULT}'.",
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
        help="Overwrite existing CSV files. Defaults to False.",
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


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating Monte Carlo variable gen CSVs...")

    create_variable_profile_csvs(
        db_path=parsed_args.database,
        weather_bins_id=parsed_args.weather_bins_id,
        weather_draws_id=parsed_args.weather_draws_id,
        output_directory=parsed_args.output_directory,
        profile_scenario_id=parsed_args.variable_generator_profile_scenario_id,
        profile_scenario_name=parsed_args.variable_generator_profile_scenario_name,
        stage_id=parsed_args.stage_id,
        overwrite=parsed_args.overwrite,
        n_parallel_projects=parsed_args.n_parallel_projects,
        units_table="raw_data_var_project_units",
        param_name="cap_factor",
        raw_data_table="raw_data_project_variable_profiles",
    )


if __name__ == "__main__":
    main()
