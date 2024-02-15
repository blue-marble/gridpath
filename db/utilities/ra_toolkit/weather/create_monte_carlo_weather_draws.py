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
#
# create_weather_draws() function
# Copyright 2023 Moment Energy Insights LLC. Licensed under the Apache
# License, Version 2.0.
# Modifications Copyright 2024 Blue Marble Analytics LLC. Licensed under the
# Apache License, Version 2.0.


import sys
from argparse import ArgumentParser
import calendar
import datetime


import numpy as np
import pandas as pd

from db.common_functions import spin_on_database_lock_generic, connect_to_database


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
        "-bins_id", "--weather_bins_id", default=1, help="Defaults to 1."
    )
    parser.add_argument(
        "-wd_seed", "--weather_draws_seed", default=0, help="Defaults to 0."
    )
    parser.add_argument(
        "-draws_id", "--weather_draws_id", default=1, help="Defaults to 1."
    )
    parser.add_argument("-n_iter", "--n_iterations")
    parser.add_argument("-yr", "--study_year")
    parser.add_argument(
        "-it_seed", "--iterations_seed", default=0, help="Defaults to 0."
    )
    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


# Load in weather bin info
# Create synthetic weather years for the study year
def create_weather_draws(
    conn,
    weather_bins_id,
    weather_draws_seed,
    n_iterations,
    weather_draws_id,
    study_year,
    quiet,
):
    if not quiet:
        print("...drawing weather...")
    # Get the weather bins
    weather_bins_sql = f"""
        SELECT year, month, day_of_month, day_type, weather_bin
        FROM raw_data_weather_bins
        WHERE weather_bins_id = {weather_bins_id}
        """
    weather_bins = pd.read_sql(sql=weather_bins_sql, con=conn)

    # Study-year-based params
    starting_date = np.datetime64(str(study_year) + "-01-01")  # Jan 1
    days_per_iteration = 365 + calendar.isleap(study_year)

    # Create the list for the data, seed, and start the iterations
    data = []
    np.random.seed(seed=weather_draws_seed)
    for iteration in range(1, n_iterations + 1):
        # ### Starting conditions ### #
        # Start on January 1; note this can be made flexible
        draw_number = 1
        current_date = starting_date
        # Find the weather conditions on all January weather days
        starting_weather_bin_options = weather_bins[weather_bins["month"] == 1][
            "weather_bin"
        ].to_numpy()
        # Randomly draw from those weather conditions for the first day of the
        # year
        starting_weather_bin = starting_weather_bin_options[
            np.random.randint(len(starting_weather_bin_options))
        ]

        data.append(
            (
                weather_bins_id,
                weather_draws_id,
                iteration,
                draw_number,
                str(current_date),
                current_date.astype(object).month,
                (current_date.astype(datetime.datetime).isoweekday() > 5) * 1,
                int(starting_weather_bin),
            )
        )

        # ### Loop through the rest of the study year days ### #
        prior_weather_bin = starting_weather_bin
        total_days_in_iteration = days_per_iteration

        for day_of_iteration in range(2, total_days_in_iteration + 1):
            draw_number += 1
            current_date += np.timedelta64(1, "D")

            # Determine the month and day_type/weekday type
            current_month = current_date.astype(object).month
            # determine the day type (1 if day_type, 0 if weekday, must match
            # day-type bin convention)
            current_day_type_bool = (
                current_date.astype(datetime.datetime).isoweekday() > 5
            ) * 1

            # Get the weather bins across all days in the month
            weather_bins_in_current_month = weather_bins[
                weather_bins["month"] == current_month
            ]["weather_bin"].to_numpy()

            # Find the indices where the weather bin matches the prior weather
            # bin, and add 1 to those indices to get the (index) options for the
            # current weather bin
            current_weather_bin_index_options = (
                np.array(np.where(weather_bins_in_current_month == prior_weather_bin))
                + 1
            )
            # Randomly select from the above list of indices and get the
            # corresponding weather bin to assign to the current day
            current_weather_bin = weather_bins_in_current_month[
                np.random.randint(len(current_weather_bin_index_options))
            ]

            data.append(
                (
                    weather_bins_id,
                    weather_draws_id,
                    iteration,
                    draw_number,
                    str(current_date),
                    current_month,
                    current_day_type_bool,
                    int(current_weather_bin),
                )
            )

            # Change the prior_weather_bin for the next day
            prior_weather_bin = current_weather_bin

    c = conn.cursor()

    sql_info = f"""
        INSERT INTO inputs_aux_weather_draws_info ( 
            weather_bins_id,
            weather_draws_id,
            seed,
            n_iterations
        ) VALUES (
            {weather_bins_id}, 
            {weather_draws_id}, 
            {weather_draws_seed}, 
            {n_iterations}
        );
    """

    spin_on_database_lock_generic(command=c.execute(sql_info))

    sql = """
        INSERT INTO inputs_aux_weather_iterations (
            weather_bins_id,
            weather_draws_id,
            weather_iteration,
            draw_number,
            study_date,
            month,
            day_type,
            weather_day_bin
        ) VALUES (
        ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
    """
    spin_on_database_lock_generic(command=c.executemany(sql, data))

    conn.commit()


def get_weather_draws(conn, weather_bins_id, weather_draws_id):
    c = conn.cursor()
    draws = c.execute(
        f"""
        SELECT weather_iteration, draw_number, month, day_type, weather_day_bin
        FROM inputs_aux_weather_iterations
        WHERE weather_bins_id = {weather_bins_id}
        AND weather_draws_id = {weather_draws_id}
    """
    ).fetchall()

    return draws


def make_synthetic_iterations(
    conn,
    weather_bins_id,
    weather_draws_id,
    timeseries,
    iterations_seed,
    quiet,
):
    """ """
    if not quiet:
        print("   ...creating synthetic iterations...")
    # Get the weather draws
    weather_draws = get_weather_draws(
        conn=conn, weather_bins_id=weather_bins_id, weather_draws_id=weather_draws_id
    )

    np.random.seed(seed=iterations_seed)
    prev_weather_iteration = None
    for weather_iteration, draw_number, month, day_type, weather_bin in weather_draws:
        if (
            prev_weather_iteration is not None
            and prev_weather_iteration != weather_iteration
            and weather_iteration % 10 == 0
        ):
            if not quiet:
                print(f"      ...weather iteration {weather_iteration}")
        prev_weather_iteration = weather_iteration

        c = conn.cursor()

        sql_set_string = ""
        for timeseries_name, consider_day_types in timeseries:
            consider_day_types_str = (
                f"AND day_type = {day_type}" if consider_day_types else ""
            )

            get_options_sql = f"""
                SELECT year, month, day_of_month, 
                day_type, weather_bin
                FROM (
                    SELECT year, month, day_of_month, day_type, weather_bin
                    FROM raw_data_weather_bins
                    WHERE month = {month}
                    {consider_day_types_str}
                    AND weather_bin = {weather_bin}
                    AND weather_bins_id = {weather_bins_id}
                )
                WHERE year in (
                    SELECT year
                    FROM raw_data_availability
                    WHERE timeseries_name = '{timeseries_name}'
                    )
                ORDER BY year, month, day_of_month
            ;
            """

            get_options = c.execute(get_options_sql).fetchall()

            # Make into a list
            options_list = [o for o in get_options]

            # Randomly select from list
            (
                year,
                month,
                day_of_month,
                day_type,
                weather_bin,
            ) = options_list[np.random.randint(len(options_list))]

            # Add to dictionary
            sql_set_string += f"""{timeseries_name}_year = {year},
                {timeseries_name}_month = {month},
                {timeseries_name}_day_of_month = {day_of_month},"""

        # Remove the trailing comma
        sql_set_string = sql_set_string.rstrip(",")

        # Load the selection into the database
        update_sql = f"""
            UPDATE inputs_aux_weather_iterations
            SET {sql_set_string}
            WHERE weather_draws_id = {weather_draws_id}
            AND weather_iteration = {weather_iteration}
            AND draw_number = {draw_number}
            ;
        """

        spin_on_database_lock_generic(c.execute(update_sql))

    conn.commit()


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating Monte Carlo weather draws...")

    conn = connect_to_database(db_path=parsed_args.database)

    # ###################### Create the weather draws # ########################
    create_weather_draws(
        conn=conn,
        weather_bins_id=int(parsed_args.weather_bins_id),
        weather_draws_seed=int(parsed_args.weather_draws_seed),
        n_iterations=int(parsed_args.n_iterations),
        weather_draws_id=int(parsed_args.weather_draws_id),
        study_year=int(parsed_args.study_year),
        quiet=parsed_args.quiet,
    )

    # ### Draw from each timeseries to create synthetic weather iterations # ###
    # Get the timeseries
    c = conn.cursor()
    timeseries = [
        (timeseries_name, consider_day_types)
        for (timeseries_name, consider_day_types) in c.execute(
            f"""SELECT timeseries_name, consider_day_types
        FROM raw_data_monte_carlo_timeseries
        ;"""
        ).fetchall()
    ]

    # Update the iterations seed
    # It is currently the same for all timeseries
    it_seed_sql = f"""
        UPDATE inputs_aux_weather_draws_info
        SET iterations_seed = {parsed_args.iterations_seed}
        ;
    """

    spin_on_database_lock_generic(c.execute(it_seed_sql))

    # Get the needed timeseries, draw the conditions, and load into the database
    for timeseries_name, consider_day_types in timeseries:
        if not parsed_args.quiet:
            print(f"...processing timeseries: {timeseries_name}")

        # Add the necessary columns
        columns_to_add = [
            f"{timeseries_name}_year",
            f"{timeseries_name}_month",
            f"{timeseries_name}_day_of_month",
        ]

        for column in columns_to_add:
            sql = f"""
                ALTER TABLE inputs_aux_weather_iterations
                ADD COLUMN {column} INTEGER
                ;
            """
            spin_on_database_lock_generic(c.execute(sql))
        conn.commit()

    # Draw the conditions
    make_synthetic_iterations(
        conn=conn,
        weather_bins_id=int(parsed_args.weather_bins_id),
        weather_draws_id=int(parsed_args.weather_draws_id),
        timeseries=timeseries,
        iterations_seed=int(parsed_args.iterations_seed),
        quiet=parsed_args.quiet,
    )


if __name__ == "__main__":
    main()
