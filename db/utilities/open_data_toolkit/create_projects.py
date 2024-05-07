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
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database", default="../../open_data.db")
    parser.add_argument("-rep", "--report_date", default="2023-01-01")
    parser.add_argument("-y", "--study_year", default=2026)
    parser.add_argument("-r", "--region", default="WECC")
    parser.add_argument(
        "-csv", "--csv_location", default="../../csvs_open_data/project/portfolios"
    )
    parser.add_argument("-id", "--project_portfolio_scenario_id", default=1)
    parser.add_argument(
        "-name", "--project_portfolio_scenario_name", default="wecc_generator_units"
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_disaggregated_project_portfolio_for_region(
    conn, report_date, study_year, region, csv_location, portfolio_id, portfolio_name
):
    sql = f"""
    SELECT plant_id_eia || '-' || generator_id as project, NULL as specified, NULL as new_build, capacity_type
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_prime_mover_key
    USING (prime_mover_code)
    WHERE report_date = '{report_date}' -- get latest
    AND (unixepoch(current_planned_generator_operating_date) >= unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{portfolio_id}_" f"{portfolio_name}.csv"),
        index=False,
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    conn = connect_to_database(db_path=parsed_args.database)

    get_disaggregated_project_portfolio_for_region(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.csv_location,
        portfolio_id=parsed_args.project_portfolio_scenario_id,
        portfolio_name=parsed_args.project_portfolio_scenario_name
    )


if __name__ == "__main__":
    main()
