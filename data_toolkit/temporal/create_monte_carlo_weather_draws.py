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
#
# create_weather_draws() function
# Copyright 2023 Moment Energy Insights LLC. Licensed under the Apache
# License, Version 2.0.
# Modifications Copyright 2024 Blue Marble Analytics LLC. Licensed under the
# Apache License, Version 2.0.

"""
.. _monte-carlo-draws-section-ref:
Monte Carlo Weather Iteration Draws
***********************************

The Monte Carlo approach employed in the GridPath RA Toolkit study synthesizes
multiple years of plausible hourly load, wind availability, solar availability,
and temperature-driven thermal derate data over which the system operations can
be simulated. Synthetic days are built by combining load, wind, solar, and
temperature derate shapes from different but similar days in the historical
record. For a detailed description of the methodology, see Appendix B of the
report available at
https://gridlab.org/wp-content/uploads/2022/10/GridLab_RA-Toolkit-Report-10-12-22.pdf.

=====
Usage
=====

>>> gridpath_run_data_toolkit --single_step create_monte_carlo_weather_draws --settings_csv PATH/TO/SETTINGS/CSV

===================
Input prerequisites
===================

This module assumes the following raw input database tables have been populated:
    * user_defined_weather_bins

=========
Settings
=========
    * database
    * weather_bins_id
    * weather_draws_id
    * weather_draws_seed
    * n_iterations
    * study_year
    * timeseries_iteration_draw_initial_seed

"""

import sys
from argparse import ArgumentParser
import calendar
import datetime


import numpy as np
import pandas as pd

from db.common_functions import spin_on_database_lock_generic, connect_to_database
from data_toolkit.load_raw_data import read_and_import_csv


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
        "-csv",
        "--input_csv",
        default=None,
        help="""This is the path to the CSV file containing the 
                        weather bins. If not specified, the weather bins will be 
                        assumed to have been already loaded into the 
                        database.""",
    ),
    parser.add_argument(
        "-bins_id", "--weather_bins_id", default=1, help="Defaults to 1."
    )
    parser.add_argument(
        "-wd_seed",
        "--weather_draws_seed",
        default=None,
        help="Defaults to None (no seeding). WARNING: Proceed with caution if "
        "you set a seed and make sure you understand what this script "
        "does with it.",
    )
    parser.add_argument(
        "-draws_id",
        "--weather_draws_id",
        default=1,
        help="Defaults to 1.",
    )
    parser.add_argument("-n_iter", "--n_iterations")
    parser.add_argument("-yr", "--study_year")
    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_weather_draws(
    conn,
    weather_bins_id,
    weather_draws_seed,
    n_iterations,
    weather_draws_id,
    study_year,
    quiet,
):
    """
    Load in weather bin info
    Create synthetic weather years for the study year
    """
    if not quiet:
        print("...drawing weather...")
    # Get the weather bins
    weather_bins_sql = f"""
        SELECT year, month, day_of_month, day_type, weather_bin
        FROM user_defined_weather_bins
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
        INSERT INTO aux_weather_draws_info ( 
            weather_bins_id,
            weather_draws_id,
            seed,
            n_iterations
        ) VALUES (
            {weather_bins_id}, 
            {weather_draws_id}, 
            {weather_draws_seed if weather_draws_seed is not None else 'NULL'}, 
            {n_iterations}
        );
    """

    spin_on_database_lock_generic(command=c.execute(sql_info))

    sql = """
        INSERT INTO aux_weather_iterations (
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


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating Monte Carlo weather draws...")

    conn = connect_to_database(db_path=parsed_args.database)

    # ### Load data from CSV
    if parsed_args.input_csv is not None:
        read_and_import_csv(
            conn=conn, f_path=parsed_args.input_csv, table="user_defined_weather_bins"
        )

    # ###################### Create the weather draws # ########################
    create_weather_draws(
        conn=conn,
        weather_bins_id=int(parsed_args.weather_bins_id),
        weather_draws_seed=(
            int(parsed_args.weather_draws_seed)
            if parsed_args.weather_draws_seed is not None
            else None
        ),
        n_iterations=int(parsed_args.n_iterations),
        weather_draws_id=int(parsed_args.weather_draws_id),
        study_year=int(parsed_args.study_year),
        quiet=parsed_args.quiet,
    )

    conn.close()


if __name__ == "__main__":
    main()
