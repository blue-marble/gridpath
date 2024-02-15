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
Create hydro iteration input CSVs for year/month data.
"""
from argparse import ArgumentParser
from multiprocessing import get_context
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database


# TODO: leap years
# TODO: hydro bins -- pick bin at random, pick year from bin at random; match
#  month


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)
    parser.add_argument("-db", "--database", default="../../io.db")
    parser.add_argument("-stage", "--stage_id", default=1, help="Defaults to 1.")
    parser.add_argument(
        "-id",
        "--hydro_operational_chars_scenario_id",
        default=1,
        help="Defaults to 1.",
    )
    parser.add_argument(
        "-name",
        "--hydro_operational_chars_scenario_name",
        default="ra_toolkit",
        help="Defaults to ra_toolkit.",
    )
    parser.add_argument("-out_dir", "--output_directory")
    parser.add_argument(
        "-o",
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing files.",
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


def calculate_from_project_year_month_data(
    db_path,
    prj,
    stage_id,
    hydro_operational_chars_scenario_id,
    hydro_operational_chars_scenario_name,
    output_directory,
    overwrite,
):
    """
    Create hydro project CSVs for a temporal subscenario and a balancing
    type from year/month data.
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    hydro_years = [
        y[0]
        for y in c.execute(
            """
            SELECT DISTINCT year FROM raw_data_hydro_years;
    """
        ).fetchall()
    ]

    bt_horizons = [
        bt_h
        for bt_h in c.execute(
            """
            SELECT DISTINCT balancing_type, horizon 
            FROM raw_data_balancing_type_horizons;
            """
        ).fetchall()
    ]

    if overwrite:
        filename = get_filename(
            output_directory,
            prj,
            hydro_operational_chars_scenario_id,
            hydro_operational_chars_scenario_name,
        )
        try:
            os.remove(filename)
        except OSError:
            pass

    # Create hydro inputs for each year and balancing type
    for yr in hydro_years:
        for bt, h in bt_horizons:
            hr_start, hr_end = c.execute(
                f"""
                    SELECT hour_ending_of_year_start, hour_ending_of_year_end
                    FROM raw_data_balancing_type_horizons
                    WHERE balancing_type = '{bt}'
                    AND horizon = {h}
                    ;
                """
            ).fetchone()

            month_weights = {}
            total = 0
            for hr_of_year in range(hr_start - 1, hr_end):
                timestamp = pd.Timestamp(f"{yr}-01-01") + pd.to_timedelta(
                    hr_of_year, unit="h"
                )
                hr_month = timestamp.month
                if hr_month in month_weights.keys():
                    month_weights[hr_month] += 1
                else:
                    month_weights[hr_month] = 1

                total += 1

            df = pd.DataFrame(
                columns=[
                    "hydro_iteration",
                    "stage_id",
                    "balancing_type_project",
                    "horizon",
                    "average_power_fraction",
                    "min_power_fraction",
                    "max_power_fraction",
                ]
            )
            weighted_avg, weighted_min, weighted_max = 0, 0, 0
            for month in month_weights.keys():
                weight = month_weights[month]
                avg, min, max = c.execute(
                    f"""
                    SELECT average_power_fraction, min_power_fraction, 
                    max_power_fraction
                    FROM raw_data_project_hydro_opchars_by_year_month
                    WHERE project = '{prj}'
                    AND hydro_year = {yr}
                    AND month = {month}
                    ;
                """
                ).fetchone()

                weighted_avg += weight * avg
                weighted_min += weight * min
                weighted_max += weight * max

            weighted_avg = weighted_avg / total
            weighted_min = weighted_min / total
            weighted_max = weighted_max / total

            df.loc[len(df)] = [
                yr,
                stage_id,
                bt,
                h,
                weighted_avg,
                weighted_min,
                weighted_max,
            ]

            filename = get_filename(
                output_directory,
                prj,
                hydro_operational_chars_scenario_id,
                hydro_operational_chars_scenario_name,
            )

            df.to_csv(
                filename,
                mode="a",
                header=not os.path.exists(filename),
                index=False,
            )


def calculate_from_project_year_month_data_pool(pool_datum):
    (
        db_path,
        prj,
        hydro_operational_chars_scenario_id,
        hydro_operational_chars_scenario_name,
        output_directory,
        overwrite,
        stage_id,
    ) = pool_datum

    calculate_from_project_year_month_data(
        db_path=db_path,
        prj=prj,
        hydro_operational_chars_scenario_id=hydro_operational_chars_scenario_id,
        hydro_operational_chars_scenario_name=hydro_operational_chars_scenario_name,
        output_directory=output_directory,
        overwrite=overwrite,
        stage_id=stage_id,
    )


def get_filename(
    output_directory,
    prj,
    hydro_operational_chars_scenario_id,
    hydro_operational_chars_scenario_name,
):
    return os.path.join(
        output_directory,
        f"{prj}-{hydro_operational_chars_scenario_id}-{hydro_operational_chars_scenario_name}.csv",
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating hydro CSVs...")

    db = connect_to_database(parsed_args.database)

    c = db.cursor()
    projects = [
        prj[0]
        for prj in c.execute(
            """
                SELECT DISTINCT project
                FROM raw_data_project_hydro_opchars_by_year_month;
            """
        ).fetchall()
    ]
    pool_data = tuple(
        [
            [
                parsed_args.database,
                prj,
                parsed_args.hydro_operational_chars_scenario_id,
                parsed_args.hydro_operational_chars_scenario_name,
                parsed_args.output_directory,
                parsed_args.overwrite,
                parsed_args.stage_id,
            ]
            for prj in projects
        ]
    )

    # Pool must use spawn to work properly on Linux
    pool = get_context("spawn").Pool(int(parsed_args.n_parallel_projects))

    pool.map(calculate_from_project_year_month_data_pool, pool_data)
    pool.close()


if __name__ == "__main__":
    main()
