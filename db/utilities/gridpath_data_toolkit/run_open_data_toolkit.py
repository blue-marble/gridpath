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

"""
Raw data
load.csv -- currently downloaded manually from RA Toolkit Google Drive and 
merged into a single CSV

load_zone_units.csv -- manually created

eia860_generators.csv -- download from PUDL

Auxiliary data, manually created
aux_baa_key.csv
aux_eia_energy_source_key.csv
aux_eia_prime_mover_key.csv
"""


import os.path
from argparse import ArgumentParser

import pandas as pd
import sys

# GridPath modules
from db import create_database
from db.utilities.gridpath_data_toolkit.raw_data import load_raw_data
from db.utilities.gridpath_data_toolkit.weather import (
    create_sync_load_input_csvs,
)
from db.utilities.gridpath_data_toolkit.project.opchar.var_profiles import (
    create_sync_var_gen_input_csvs,
)
from db.utilities.gridpath_data_toolkit.project.opchar.hydro import (
    create_hydro_iteration_inputs,
)


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument(
        "-s", "--settings_csv", default="open_data_toolkit_settings.csv"
    )
    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    # Run only a single RA Toolkit step
    parser.add_argument(
        "-step",
        "--single_step_only",
        choices=[
            "create_database",
            "load_raw_data",
            "create_sync_load_input_csvs",
            "create_project_csvs",
            "create_sync_var_gen_input_csvs",
            "create_hydro_iteration_inputs",
            "create_transmission_csvs",
        ],
        help="Run only the specified step. All others will be skipped. If not "
        "specified, the entire Toolkit will be run.",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_setting(settings_df, script, setting):
    return settings_df[
        (settings_df["script"] == script) & (settings_df["setting"] == setting)
    ]["value"].values[0]


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    # Get the settings
    settings_df = pd.read_csv(parsed_args.settings_csv)
    settings_df.set_index(["script", "setting"])

    # Arguments used by multiple scripts
    db_path = os.path.join(
        os.getcwd(),
        get_setting(settings_df, "multi", "database"),
    )

    stage_id = get_setting(settings_df, "multi", "stage_id")

    # Figure out which steps, if any, we are skipping
    skip_create_database = True
    skip_load_raw_data = True
    skip_create_sync_load_input_csvs = True
    skip_create_project_input_csvs = True
    skip_create_sync_var_gen_input_csvs = True
    skip_create_hydro_iteration_inputs = True
    skip_create_transmission_input_csvs = True

    if parsed_args.single_step_only == "create_database":
        skip_create_database = False
    elif parsed_args.single_step_only == "load_raw_data":
        skip_load_raw_data = False
    elif parsed_args.single_step_only == "create_sync_load_input_csvs":
        skip_create_sync_load_input_csvs = False
    elif parsed_args.single_step_only == "create_project_input_csvs":
        skip_create_project_input_csvs = False
    elif parsed_args.single_step_only == "create_sync_var_gen_input_csvs":
        skip_create_sync_var_gen_input_csvs = False
    elif parsed_args.single_step_only == "create_hydro_iteration_inputs":
        skip_create_hydro_iteration_inputs = False
    elif parsed_args.single_step_only == "create_transmission_input_csvs":
        skip_create_transmission_input_csvs = False
    else:
        skip_create_database = False
        skip_load_raw_data = False
        skip_create_sync_load_input_csvs = False
        skip_create_project_input_csvs = False
        skip_create_sync_var_gen_input_csvs = False
        skip_create_hydro_iteration_inputs = False
        skip_create_transmission_input_csvs = False

    # ### Create the database ### #
    if not skip_create_database:
        create_database.main(["--database", db_path])

    # ### Load raw data ### #
    if not skip_load_raw_data:
        load_raw_data_csv = os.path.join(
            os.getcwd(), get_setting(settings_df, "load_raw_data", "csv_location")
        )
        load_raw_data.main(
            [
                "--database",
                db_path,
                "--csv_location",
                load_raw_data_csv,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Load
    if not skip_create_sync_load_input_csvs:
        sync_load_scenario_id = get_setting(
            settings_df, "create_sync_load_input_csvs", "load_scenario_id"
        )
        sync_load_scenario_name = get_setting(
            settings_df, "create_sync_load_input_csvs", "load_scenario_name"
        )
        sync_load_output_directory = os.path.join(
            os.getcwd(),
            get_setting(settings_df, "create_sync_load_input_csvs", "output_directory"),
        )
        sync_load_csv_overwrite = get_setting(
            settings_df, "create_sync_load_input_csvs", "overwrite"
        )

        create_sync_load_input_csvs.main(
            [
                "--database",
                db_path,
                "--load_scenario_id",
                sync_load_scenario_id,
                "--load_scenario_name",
                sync_load_scenario_name,
                "--stage_id",
                stage_id,
                "--output_directory",
                sync_load_output_directory,
                "--overwrite" if int(sync_load_csv_overwrite) else "",
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Project inputs
    # TODO: need to split this up
    if not skip_create_project_input_csvs:
        # TODO: add settings
        create_projects.main(args=None)

    # Variable generation profiles
    if not skip_create_sync_var_gen_input_csvs:
        sync_variable_generator_profile_scenario_id = get_setting(
            settings_df,
            "create_sync_var_gen_input_csvs",
            "variable_generator_profile_scenario_id",
        )

        sync_variable_generator_profile_scenario_name = get_setting(
            settings_df,
            "create_sync_var_gen_input_csvs",
            "variable_generator_profile_scenario_name",
        )
        sync_var_gen_output_directory = get_setting(
            settings_df, "create_sync_var_gen_input_csvs", "output_directory"
        )
        sync_var_gen_csv_overwrite = get_setting(
            settings_df, "create_sync_var_gen_input_csvs", "overwrite"
        )

        n_parallel_projects_sync_var_gen = get_setting(
            settings_df, "create_sync_var_gen_input_csvs", "n_parallel_projects"
        )

        create_sync_var_gen_input_csvs.main(
            [
                "--database",
                db_path,
                "--variable_generator_profile_scenario_id",
                sync_variable_generator_profile_scenario_id,
                "--variable_generator_profile_scenario_name",
                sync_variable_generator_profile_scenario_name,
                "--stage_id",
                stage_id,
                "--output_directory",
                sync_var_gen_output_directory,
                "--overwrite" if int(sync_var_gen_csv_overwrite) else "",
                "--n_parallel_projects",
                n_parallel_projects_sync_var_gen,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Fuels
    # TODO: add overwrite or not option
    if not skip_create_sync_var_gen_input_csvs:
        fuel_price_csv_location = get_setting(
            settings_df,
            "create_fuels",
            "fuel_price_csv_location",
        )

        fuel_price_scenario_id = get_setting(
            settings_df,
            "create_fuels",
            "fuel_price_scenario_id",
        )

        model_case = get_setting(
            settings_df,
            "create_fuels",
            "model_case",
        )

        report_year = get_setting(
            settings_df,
            "create_fuels",
            "report_year",
        )

        create_fuels.main(
            [
                "--database",
                db_path,
                "--fuel_price_csv_location",
                fuel_price_csv_location,
                "--fuel_price_scenario_id",
                fuel_price_scenario_id,
                "--model_case",
                model_case,
                "--report_year",
                report_year,
            ]
        )

    # ### Hydro ### #
    if not skip_create_hydro_iteration_inputs:
        hydro_operational_chars_scenario_id = get_setting(
            settings_df,
            "create_hydro_iteration_inputs",
            "hydro_operational_chars_scenario_id",
        )
        hydro_operational_chars_scenario_name = get_setting(
            settings_df,
            "create_hydro_iteration_inputs",
            "hydro_operational_chars_scenario_name",
        )
        output_directory = get_setting(
            settings_df, "create_hydro_iteration_inputs", "output_directory"
        )
        hy_overwrite = get_setting(
            settings_df, "create_hydro_iteration_inputs", "overwrite"
        )

        n_parallel_projects_hy = get_setting(
            settings_df, "create_hydro_iteration_inputs", "n_parallel_projects"
        )

        create_hydro_iteration_inputs.main(
            [
                "--database",
                db_path,
                "--stage_id",
                stage_id,
                "--hydro_operational_chars_scenario_id",
                hydro_operational_chars_scenario_id,
                "--hydro_operational_chars_scenario_name",
                hydro_operational_chars_scenario_name,
                "--output_directory",
                output_directory,
                "--overwrite" if int(hy_overwrite) else "",
                "--n_parallel_projects",
                n_parallel_projects_hy,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Transmission inputs
    if not skip_create_transmission_input_csvs:
        # TODO: add settings
        create_transmission.main(args=None)


if __name__ == "__main__":
    main()
