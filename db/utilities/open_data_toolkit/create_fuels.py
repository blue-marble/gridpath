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

import csv
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

    parser.add_argument(
        "-fuel_price_csv",
        "--fuel_price_csv_location",
        default="../../csvs_open_data/fuels/fuel_prices",
    )
    parser.add_argument("-fuel_price_id", "--fuel_price_scenario_id", default=1)
    parser.add_argument(
        "-case",
        "--model_case",
        default="aeo2022",
    )
    parser.add_argument("-r_yr", "--report_year", default=2023)

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_fuel_prices(
    conn, csv_location, subscenario_id, subscenario_name, report_year, model_case
):
    """ """

    sql = f"""
    SELECT gridpath_generic_fuel || '_' || fuel_region as fuel, projection_year as period, 
    fuel_cost_real_per_mmbtu_eiaaeo as fuel_price_per_mmbtu
    FROM raw_data_fuel_prices
    JOIN (SELECT DISTINCT gridpath_generic_fuel, fuel_type_eiaaeo FROM raw_data_aux_eia_gridpath_key) USING (fuel_type_eiaaeo)
    JOIN raw_data_aux_eiaaeo_region_key using (
    electricity_market_module_region_eiaaeo)
    WHERE report_year = {report_year}
    AND model_case_eiaaeo = '{model_case}'
    ORDER BY fuel, period
    """

    print(sql)

    df = pd.read_sql(sql, conn)
    month_df_list = []
    for month in range(1, 13):
        month_df = df
        month_df["month"] = month
        cols = month_df.columns.tolist()
        cols = cols[:2] + [cols[3]] + [cols[2]]
        month_df = month_df[cols]

        month_df_list.append(month_df)

    final_df = pd.concat(month_df_list)

    final_df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def main(args=None):
    print("Creating fuel prices")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    conn = connect_to_database(db_path=parsed_args.database)

    get_fuel_prices(
        conn=conn,
        csv_location=parsed_args.fuel_price_csv_location,
        subscenario_id=parsed_args.fuel_price_scenario_id,
        subscenario_name=parsed_args.model_case,
        report_year=parsed_args.report_year,
        model_case=parsed_args.model_case,
    )


if __name__ == "__main__":
    main()
