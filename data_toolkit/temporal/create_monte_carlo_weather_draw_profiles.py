# Copyright 2016-2025 Blue Marble Analytics LLC.
# Copyright 2026 Sylvan Energy Analytics LLC.
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
=====
Usage
=====

>>> gridpath_run_data_toolkit --single_step create_monte_carlo_weather_draw_profiles --settings_csv PATH/TO/SETTINGS/CSV

===================
Input prerequisites
===================

This module assumes that the **create_monte_carlo_weather_draws** step has
been run and the following raw input database tables have been populated:
    * user_defined_monte_carlo_timeseries

=========
Settings
=========
    * database
    * weather_bins_id
    * weather_draws_id
    * study_year
    * timeseries_iteration_draw_initial_seed

"""

import sys
import warnings
from argparse import ArgumentParser

import numpy as np

from data_toolkit.load_raw_data import read_and_import_csv
from db.common_functions import spin_on_database_lock_generic, connect_to_database

TIMESERIES_TYPE = {
    "load": {
        "profiles_table": "raw_data_system_load",
        "units_table": "user_defined_load_zone_units",
    },
    "var_profiles": {
        "profiles_table": "raw_data_var_profiles",
        "units_table": "raw_data_var_project_units",
    },
    "availability": {
        "profiles_table": "raw_data_availability_profiles",
        "units_table": "raw_data_unit_availability_params",
    },
}


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
        "-rd_csv",
        "--raw_data_input_csv",
        default=None,
        help="""Path to the CSV file to load into the 
        raw data table for the timeseries. If not specified, data will be 
        assumed to 
        have been already loaded into the database.""",
    )
    parser.add_argument(
        "-u_csv",
        "--units_input_csv",
        default=None,
        help="""Path to the unit CSV file to load into the 
        units table for the timeseries. If not specified, data will be 
        assumed to have been already loaded into the database.""",
    )
    parser.add_argument(
        "-ts_csv",
        "--timeseries_input_csv",
        default=None,
        help="""Path to the timeseries CSV file to load. If not specified, 
        data will be assumed to have been already loaded into the database.""",
    )
    parser.add_argument(
        "-t",
        "--timeseries_name",
        default=None,
        help="Timeseries names to draw from. If not specified, a list of "
        "timeseries will be loaded from the database.",
    )
    parser.add_argument(
        "-d",
        "--consider_day_types",
        default=None,
        help="Required boolean if timeseries_name is specified. Use 1 for "
        "'yes' and 0 for 'no'.",
    )
    parser.add_argument(
        "-ts_type",
        "--timeseries_type",
        default=None,
        choices=list(TIMESERIES_TYPE.keys()),
        help="Required boolean if timeseries_name is specified or to load "
        "data intputs.",
    )

    parser.add_argument(
        "-bins_id", "--weather_bins_id", default=1, help="Defaults to 1."
    )
    parser.add_argument(
        "-draws_id",
        "--weather_draws_id",
        default=1,
        help="Defaults to 1.",
    )
    parser.add_argument("-yr", "--study_year")
    parser.add_argument(
        "-it_seed",
        "--timeseries_iteration_draw_initial_seed",
        default=None,
        help="Defaults to None (no seeding). WARNING: Proceed with caution if "
        "you set a seed and make sure you understand what this script "
        "does with it.",
    )
    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def make_timeseries_draw_profiles(
    conn,
    timeseries_name,
    consider_day_types,
    timeseries_type,
    timeseries_iteration_draw_initial_seed,
    weather_bins_id,
    weather_draws_id,
    quiet,
):
    """
    Draw from the timeseries raw data to create synthetic weather iteration
    profiles based on particular weather draws.
    """

    if not quiet:
        print("   ...creating synthetic iterations...")

    # Get the timeseries
    if timeseries_name is None:
        c = conn.cursor()
        timeseries = [
            (timeseries_name, consider_day_types, timeseries_type, initial_seed)
            for (
                timeseries_name,
                consider_day_types,
                timeseries_type,
                initial_seed,
            ) in c.execute(
                f"""SELECT timeseries_name, consider_day_types,
                timeseries_type, initial_seed
                FROM user_defined_monte_carlo_timeseries
                ;"""
            ).fetchall()
        ]
    else:
        timeseries = [
            (
                timeseries_name,
                consider_day_types,
                timeseries_type,
                timeseries_iteration_draw_initial_seed,
            )
        ]

    # Get the weather draws
    weather_draws = get_weather_draws(
        conn=conn,
        weather_bins_id=weather_bins_id,
        weather_draws_id=weather_draws_id,
    )

    # Iterate over timeseries
    for (
        timeseries_name,
        consider_day_types,
        timeseries_type,
        timeseries_iteration_draw_initial_seed,
    ) in timeseries:
        if not timeseries_type in TIMESERIES_TYPE.keys():
            raise ValueError(
                f"Invalid draw profile type: {timeseries_type}. "
                f"Valid options are:"
                f" {list(TIMESERIES_TYPE.keys())}."
            )

        if not quiet:
            print(f"      ...processing timeseries: {timeseries_name}")

        # Set a starting seed if requested
        timeseries_iteration_draw_seed = (
            int(timeseries_iteration_draw_initial_seed)
            if timeseries_iteration_draw_initial_seed is not None
            else None
        )

        # Base availability on the data in the raw_data_var_profiles table
        # rather than exogenously defined by user
        # TODO: add option to exogenously define
        # WHERE
        # year in (
        #     SELECT year
        # FROM user_defined_data_availability
        # WHERE timeseries_name = '{timeseries_name}'
        # )

        data_av_c = conn.cursor()
        data_availability_list = [str(i[0]) for i in data_av_c.execute(f"""
                    SELECT DISTINCT year
                    FROM {TIMESERIES_TYPE[timeseries_type]["profiles_table"]}
                    WHERE unit in (
                    SELECT unit
                    FROM {TIMESERIES_TYPE[timeseries_type]["units_table"]}
                    WHERE timeseries_name = '{timeseries_name}'
                    );""")]
        data_availability_string = ", ".join(data_availability_list)
        data_av_c.close()

        # Add the necessary columns
        columns_to_add = [
            f"{timeseries_name}_year",
            f"{timeseries_name}_month",
            f"{timeseries_name}_day_of_month",
        ]

        c = conn.cursor()
        for column in columns_to_add:
            sql = f"""
                    ALTER TABLE aux_weather_iterations
                    ADD COLUMN {column} INTEGER
                    ;
                """
            spin_on_database_lock_generic(c.execute(sql))

        # Build cache of options by (month, day_type, weather_bin)
        if not quiet:
            print(f"         ...building options cache...")

        options_cache = build_options_cache(
            conn=conn,
            weather_draws=weather_draws,
            consider_day_types=consider_day_types,
            weather_bins_id=weather_bins_id,
            data_availability_string=data_availability_string,
        )

        # Collect all updates in batch
        if not quiet:
            print(f"         ...generating draws...")

        batch_updates = []
        prev_weather_iteration = None

        for (
            weather_iteration,
            draw_number,
            month,
            day_type,
            weather_bin,
        ) in weather_draws:
            if (
                prev_weather_iteration is not None
                and prev_weather_iteration != weather_iteration
                and weather_iteration % 10 == 0
            ):
                if not quiet:
                    print(f"         ...weather iteration {weather_iteration}")
            prev_weather_iteration = weather_iteration

            # Get cached options
            cache_key = (month, day_type if consider_day_types else None, weather_bin)
            options_list = options_cache.get(cache_key, [])

            if not options_list:
                continue

            # Draw the conditions
            year, month_out, day_of_month = draw_conditions_batch(
                options_list=options_list,
                timeseries_iteration_draw_seed=timeseries_iteration_draw_seed,
            )

            # Add to batch
            batch_updates.append(
                (
                    year,
                    month_out,
                    day_of_month,
                    weather_draws_id,
                    weather_iteration,
                    draw_number,
                )
            )

            if timeseries_iteration_draw_seed is not None:
                # TODO: instead of incrementing seed, possibly set seeds via CSV
                #  data input for easier reproducibility
                timeseries_iteration_draw_seed += 1

        # Execute batch update
        if not quiet:
            print(f"         ...executing batch update ({len(batch_updates)} rows)...")

        execute_batch_update(
            conn=conn,
            timeseries_name=timeseries_name,
            batch_updates=batch_updates,
            weather_draws_id=weather_draws_id,
        )


def get_weather_draws(conn, weather_bins_id, weather_draws_id):
    c = conn.cursor()
    draws = c.execute(f"""
        SELECT weather_iteration, draw_number, month, day_type, weather_day_bin
        FROM aux_weather_iterations
        WHERE weather_bins_id = {weather_bins_id}
        AND weather_draws_id = {weather_draws_id}
    """).fetchall()

    return draws


def build_options_cache(
    conn,
    weather_draws,
    consider_day_types,
    weather_bins_id,
    data_availability_string,
):
    """
    Build a cache of options for each unique (month, day_type, weather_bin) combination.
    This eliminates redundant database queries.
    """
    cache = {}
    unique_keys = set()

    # Collect unique combinations
    for _, _, month, day_type, weather_bin in weather_draws:
        cache_key = (month, day_type if consider_day_types else None, weather_bin)
        unique_keys.add(cache_key)

    # Query database once per unique combination
    c = conn.cursor()
    for cache_key in unique_keys:
        month, day_type, weather_bin = cache_key

        consider_day_types_str = (
            f"AND day_type = {day_type}"
            if consider_day_types and day_type is not None
            else ""
        )

        get_options_sql = f"""
            SELECT year, month, day_of_month
            FROM user_defined_weather_bins
            WHERE month = {month}
            {consider_day_types_str}
            AND weather_bin = {weather_bin}
            AND weather_bins_id = {weather_bins_id}
            AND year in ({data_availability_string})
            ORDER BY year, month, day_of_month
        ;
        """

        options_list = c.execute(get_options_sql).fetchall()
        cache[cache_key] = options_list

    c.close()
    return cache


def draw_conditions_batch(
    options_list,
    timeseries_iteration_draw_seed,
):
    """
    Draw random conditions from the options list.
    Returns (year, month, day_of_month) tuple.
    """
    np.random.seed(seed=timeseries_iteration_draw_seed)

    # Randomly select from list
    year, month, day_of_month = options_list[np.random.randint(len(options_list))]

    return year, month, day_of_month


def execute_batch_update(
    conn,
    timeseries_name,
    batch_updates,
    weather_draws_id,
):
    """
    Execute batch update using executemany for better performance.
    """
    if not batch_updates:
        return

    c = conn.cursor()

    # Use executemany for bulk updates
    update_sql = f"""
        UPDATE aux_weather_iterations
        SET {timeseries_name}_year = ?,
            {timeseries_name}_month = ?,
            {timeseries_name}_day_of_month = ?
        WHERE weather_draws_id = ?
        AND weather_iteration = ?
        AND draw_number = ?
    """

    spin_on_database_lock_generic(c.executemany(update_sql, batch_updates))
    conn.commit()
    c.close()


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating Monte Carlo weather draw profiles...")

    conn = connect_to_database(db_path=parsed_args.database)

    # ##### Load raw data if requested #####
    # ### Load data from CSVs
    if parsed_args.timeseries_input_csv is not None:
        read_and_import_csv(
            conn=conn,
            f_path=parsed_args.timeseries_input_csv,
            table="user_defined_monte_carlo_timeseries",
        )

    if (
        parsed_args.raw_data_input_csv is not None
        or parsed_args.units_input_csv is not None
    ):
        if parsed_args.timeseries_type is None:
            raise ValueError(
                "Timeseries type must be specified to load "
                "data into the correct table."
            )
        read_and_import_csv(
            conn=conn,
            f_path=parsed_args.raw_data_input_csv,
            table=TIMESERIES_TYPE[parsed_args.timeseries_type]["profiles_table"],
        )
        read_and_import_csv(
            conn=conn,
            f_path=parsed_args.units_input_csv,
            table=TIMESERIES_TYPE[parsed_args.timeseries_type]["units_table"],
        )

    # #### Check if specific timeseries is requested #### #
    if parsed_args.timeseries_name is not None:
        if parsed_args.consider_day_types is None:
            raise ValueError(
                "The consider_day_types must be specified if "
                "timeseries_name is specified."
            )
        if parsed_args.timeseries_type is None:
            raise ValueError(
                "The timeseries_type must be specified if "
                "timeseries_name is specified."
            )

        if parsed_args.timeseries_iteration_draw_initial_seed is None:
            warnings.warn(
                "Timeseries iteration draw initial seed is not "
                "specified. The draws will not be reproducible."
            )
        else:
            if not parsed_args.quiet:
                print(
                    f"Timeseries iteration draw initial seed is {parsed_args.timeseries_iteration_draw_initial_seed}."
                )

    # ####### Based on the weather draws, create timeseries profiles ###########
    make_timeseries_draw_profiles(
        conn=conn,
        timeseries_name=parsed_args.timeseries_name,
        consider_day_types=parsed_args.consider_day_types,
        timeseries_type=parsed_args.timeseries_type,
        timeseries_iteration_draw_initial_seed=parsed_args.timeseries_iteration_draw_initial_seed,
        weather_bins_id=parsed_args.weather_bins_id,
        weather_draws_id=parsed_args.weather_draws_id,
        quiet=parsed_args.quiet,
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
