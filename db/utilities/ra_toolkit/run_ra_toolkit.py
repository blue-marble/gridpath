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

import os.path
from argparse import ArgumentParser

import pandas as pd
import sys

# GridPath modules
from db import create_database
from db.utilities.ra_toolkit import load_raw_data
from db.utilities.ra_toolkit.availability import (
    create_availability_iteration_inputs,
    create_sync_gen_weather_derate_input_csvs,
    create_monte_carlo_gen_weather_derate_input_csvs,
)
from db.utilities.ra_toolkit.hydro import create_hydro_iteration_inputs
from db.utilities.ra_toolkit.temporal import create_temporal_scenarios
from db.utilities.ra_toolkit.weather import (
    create_sync_load_input_csvs,
    create_sync_var_gen_input_csvs,
    create_monte_carlo_weather_draws,
    create_monte_carlo_var_gen_input_csvs,
    create_monte_carlo_load_input_csvs,
)

# TODO: add checks if files exists, tell user to delete before running


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-s", "--settings_csv", default="./ra_toolkit_settings.csv")
    parser.add_argument("-q", "--quiet", default=False, action="store_true")
    # Run only a single RA Toolkit step
    parser.add_argument(
        "-step",
        "--single_step_only",
        choices=[
            "create_database",
            "load_raw_data",
            "create_sync_load_input_csvs",
            "create_sync_var_gen_input_csvs",
            "create_monte_carlo_weather_draws",
            "create_monte_carlo_load_input_csvs",
            "create_monte_carlo_var_gen_input_csvs",
            "create_hydro_iteration_inputs",
            "create_availability_iteration_inputs",
            "create_sync_gen_weather_derate_input_csvs",
            "create_monte_carlo_gen_weather_derate_input_csvs",
            "create_temporal_scenarios",
        ],
        help="Run only the specified RA Toolkit step. All others will be "
        "skipped. If not specified, the entire Toolkit will be run.",
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

    weather_bins_id = get_setting(settings_df, "multi", "weather_bins_id")

    weather_draws_id = get_setting(settings_df, "multi", "weather_draws_id")

    # Figure out which steps, if any, we are skipping
    skip_create_database = True
    skip_load_raw_data = True
    skip_create_sync_load_input_csvs = True
    skip_create_sync_var_gen_input_csvs = True
    skip_create_monte_carlo_weather_draws = True
    skip_create_monte_carlo_load_input_csvs = True
    skip_create_monte_carlo_var_gen_input_csvs = True
    skip_create_hydro_iteration_inputs = True
    skip_create_availability_iteration_inputs = True
    skip_create_sync_gen_weather_derate_input_csvs = True
    skip_create_monte_carlo_gen_weather_derate_input_csvs = True
    skip_create_temporal_scenarios = True

    if parsed_args.single_step_only == "create_database":
        skip_create_database = False
    elif parsed_args.single_step_only == "load_raw_data":
        skip_load_raw_data = False
    elif parsed_args.single_step_only == "create_sync_load_input_csvs":
        skip_create_sync_load_input_csvs = False
    elif parsed_args.single_step_only == "create_sync_var_gen_input_csvs":
        skip_create_sync_var_gen_input_csvs = False
    elif parsed_args.single_step_only == "create_monte_carlo_weather_draws":
        skip_create_monte_carlo_weather_draws = False
    elif parsed_args.single_step_only == "create_monte_carlo_load_input_csvs":
        skip_create_monte_carlo_load_input_csvs = False
    elif parsed_args.single_step_only == "create_monte_carlo_var_gen_input_csvs":
        skip_create_monte_carlo_var_gen_input_csvs = False
    elif parsed_args.single_step_only == "create_hydro_iteration_inputs":
        skip_create_hydro_iteration_inputs = False
    elif parsed_args.single_step_only == "create_availability_iteration_inputs":
        skip_create_availability_iteration_inputs = False
    elif parsed_args.single_step_only == "create_sync_gen_weather_derate_input_csvs":
        skip_create_sync_gen_weather_derate_input_csvs = False
    elif (
        parsed_args.single_step_only
        == "create_monte_carlo_gen_weather_derate_input_csvs"
    ):
        skip_create_monte_carlo_gen_weather_derate_input_csvs = False
    elif parsed_args.single_step_only == "create_temporal_scenarios":
        skip_create_temporal_scenarios = False
    else:
        skip_create_database = False
        skip_load_raw_data = False
        skip_create_sync_load_input_csvs = False
        skip_create_sync_var_gen_input_csvs = False
        skip_create_monte_carlo_weather_draws = False
        skip_create_monte_carlo_load_input_csvs = False
        skip_create_monte_carlo_var_gen_input_csvs = False
        skip_create_hydro_iteration_inputs = False
        skip_create_availability_iteration_inputs = False
        skip_create_sync_gen_weather_derate_input_csvs = False
        skip_create_monte_carlo_gen_weather_derate_input_csvs = False
        skip_create_temporal_scenarios = False

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

    # ### Create weather iterations ### #
    # Sync load
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

    # Sync variable gen
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

    # Monte Carlo draws
    if not skip_create_monte_carlo_weather_draws:
        weather_draws_seed = get_setting(
            settings_df, "create_monte_carlo_draws", "weather_draws_seed"
        )
        n_iterations = get_setting(
            settings_df, "create_monte_carlo_draws", "n_iterations"
        )
        study_year = get_setting(settings_df, "create_monte_carlo_draws", "study_year")
        iterations_seed = get_setting(
            settings_df, "create_monte_carlo_draws", "iterations_seed"
        )
        create_monte_carlo_weather_draws.main(
            [
                "--database",
                db_path,
                "--weather_bins_id",
                weather_bins_id,
                "--weather_draws_seed",
                weather_draws_seed,
                "--weather_draws_id",
                weather_draws_id,
                "--n_iterations",
                n_iterations,
                "--study_year",
                study_year,
                "--iterations_seed",
                iterations_seed,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Monte Carlo load
    if not skip_create_monte_carlo_load_input_csvs:
        mc_load_scenario_id = get_setting(
            settings_df, "create_monte_carlo_load_input_csvs", "load_scenario_id"
        )
        mc_load_scenario_name = get_setting(
            settings_df, "create_monte_carlo_load_input_csvs", "load_scenario_name"
        )
        mc_load_output_directory = os.path.join(
            os.getcwd(),
            get_setting(
                settings_df, "create_monte_carlo_load_input_csvs", "output_directory"
            ),
        )
        mc_load_csv_overwrite = get_setting(
            settings_df, "create_monte_carlo_load_input_csvs", "overwrite"
        )

        create_monte_carlo_load_input_csvs.main(
            [
                "--database",
                db_path,
                "--load_scenario_id",
                mc_load_scenario_id,
                "--load_scenario_name",
                mc_load_scenario_name,
                "--stage_id",
                stage_id,
                "--output_directory",
                mc_load_output_directory,
                "--overwrite" if int(mc_load_csv_overwrite) else "",
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Monte Carlo variable gen CSVs
    if not skip_create_monte_carlo_var_gen_input_csvs:
        mc_variable_generator_profile_scenario_id = get_setting(
            settings_df,
            "create_monte_carlo_var_gen_input_csvs",
            "variable_generator_profile_scenario_id",
        )

        mc_variable_generator_profile_scenario_name = get_setting(
            settings_df,
            "create_monte_carlo_var_gen_input_csvs",
            "variable_generator_profile_scenario_name",
        )
        mc_var_gen_output_directory = get_setting(
            settings_df, "create_monte_carlo_var_gen_input_csvs", "output_directory"
        )
        mc_var_gen_csv_overwrite = get_setting(
            settings_df, "create_monte_carlo_var_gen_input_csvs", "overwrite"
        )

        n_parallel_projects_mc_var_gen = get_setting(
            settings_df, "create_monte_carlo_var_gen_input_csvs", "n_parallel_projects"
        )

        create_monte_carlo_var_gen_input_csvs.main(
            [
                "--database",
                db_path,
                "--weather_bins_id",
                weather_bins_id,
                "--weather_draws_id",
                weather_draws_id,
                "--output_directory",
                mc_var_gen_output_directory,
                "--variable_generator_profile_scenario_id",
                mc_variable_generator_profile_scenario_id,
                "--variable_generator_profile_scenario_name",
                mc_variable_generator_profile_scenario_name,
                "--stage_id",
                stage_id,
                "--overwrite" if int(mc_var_gen_csv_overwrite) else "",
                "--n_parallel_projects",
                n_parallel_projects_mc_var_gen,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # ### Hydro Iterations ### #
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

    # ### Availability Iterations ### #

    if not skip_create_availability_iteration_inputs:
        n_iterations = get_setting(
            settings_df, "create_availability_iteration_inputs", "n_iterations"
        )
        project_availability_scenario_id = get_setting(
            settings_df,
            "create_availability_iteration_inputs",
            "project_availability_scenario_id",
        )
        project_availability_scenario_name = get_setting(
            settings_df,
            "create_availability_iteration_inputs",
            "project_availability_scenario_name",
        )
        output_directory = get_setting(
            settings_df, "create_availability_iteration_inputs", "output_directory"
        )
        ind_av_overwrite = get_setting(
            settings_df, "create_availability_iteration_inputs", "overwrite"
        )
        n_parallel_projects_av = get_setting(
            settings_df, "create_availability_iteration_inputs", "n_parallel_projects"
        )

        create_availability_iteration_inputs.main(
            [
                "--database",
                db_path,
                "--stage_id",
                stage_id,
                "--n_iterations",
                n_iterations,
                "--project_availability_scenario_id",
                project_availability_scenario_id,
                "--project_availability_scenario_name",
                project_availability_scenario_name,
                "--output_directory",
                output_directory,
                "--overwrite" if int(ind_av_overwrite) else "",
                "--n_parallel_projects",
                n_parallel_projects_av,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Sync weather derates
    if not skip_create_sync_gen_weather_derate_input_csvs:
        sync_exogenous_availability_weather_scenario_id = get_setting(
            settings_df,
            "create_sync_gen_weather_derate_input_csvs",
            "exogenous_availability_weather_scenario_id",
        )

        sync_exogenous_availability_weather_scenario_name = get_setting(
            settings_df,
            "create_sync_gen_weather_derate_input_csvs",
            "exogenous_availability_weather_scenario_name",
        )
        sync_exogenous_availability_weather_output_directory = get_setting(
            settings_df, "create_sync_gen_weather_derate_input_csvs", "output_directory"
        )
        sync_exogenous_availability_weather_overwrite = get_setting(
            settings_df, "create_sync_gen_weather_derate_input_csvs", "overwrite"
        )

        n_parallel_projects_sync_exogenous_availability_weather = get_setting(
            settings_df,
            "create_sync_gen_weather_derate_input_csvs",
            "n_parallel_projects",
        )

        create_sync_gen_weather_derate_input_csvs.main(
            [
                "--database",
                db_path,
                "--exogenous_availability_weather_scenario_id",
                sync_exogenous_availability_weather_scenario_id,
                "--exogenous_availability_weather_scenario_name",
                sync_exogenous_availability_weather_scenario_name,
                "--stage_id",
                stage_id,
                "--output_directory",
                sync_exogenous_availability_weather_output_directory,
                (
                    "--overwrite"
                    if int(sync_exogenous_availability_weather_overwrite)
                    else ""
                ),
                "--n_parallel_projects",
                n_parallel_projects_sync_exogenous_availability_weather,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # Monte Carlo weather derates
    if not skip_create_monte_carlo_gen_weather_derate_input_csvs:
        mc_weather_derates_scenario_id = get_setting(
            settings_df,
            "create_monte_carlo_gen_weather_derate_input_csvs",
            "exogenous_availability_weather_scenario_id",
        )

        mc_weather_derates_scenario_name = get_setting(
            settings_df,
            "create_monte_carlo_gen_weather_derate_input_csvs",
            "exogenous_availability_weather_scenario_name",
        )
        mc_weather_derates_output_directory = get_setting(
            settings_df,
            "create_monte_carlo_gen_weather_derate_input_csvs",
            "output_directory",
        )
        mc_weather_derates_csv_overwrite = get_setting(
            settings_df, "create_monte_carlo_gen_weather_derate_input_csvs", "overwrite"
        )

        n_parallel_projects_mc_weather_derates = get_setting(
            settings_df,
            "create_monte_carlo_gen_weather_derate_input_csvs",
            "n_parallel_projects",
        )

        create_monte_carlo_gen_weather_derate_input_csvs.main(
            [
                "--database",
                db_path,
                "--weather_bins_id",
                weather_bins_id,
                "--weather_draws_id",
                weather_draws_id,
                "--output_directory",
                mc_weather_derates_output_directory,
                "--exogenous_availability_weather_scenario_id",
                mc_weather_derates_scenario_id,
                "--exogenous_availability_weather_scenario_name",
                mc_weather_derates_scenario_name,
                "--stage_id",
                stage_id,
                "--overwrite" if int(mc_weather_derates_csv_overwrite) else "",
                "--n_parallel_projects",
                n_parallel_projects_mc_weather_derates,
                "--quiet" if parsed_args.quiet else "",
            ]
        )

    # ### Temporal scenarios ### #

    if not skip_create_temporal_scenarios:
        temporal_scenarios_csv = get_setting(
            settings_df, "create_temporal_scenarios", "csv_path"
        )
        create_temporal_scenarios.main(
            [
                "--csv_path",
                temporal_scenarios_csv,
                "--quiet" if parsed_args.quiet else "",
            ]
        )


if __name__ == "__main__":
    main()
