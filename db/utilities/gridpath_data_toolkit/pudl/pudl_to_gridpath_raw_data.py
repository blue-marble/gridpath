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
Get a subset of the PUDL data and convert to GridPath raw format.
"""

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

    parser.add_argument(
        "-pudl",
        "--pudl_download_directory",
        default="../../../csvs_open_data/pudl_download",
    )
    parser.add_argument(
        "-d",
        "--raw_data_directory",
        default="../../../csvs_open_data/raw_data",
    )

    parser.add_argument("-rdate", "--eia860_report_date", default="2023-01-01")

    parser.add_argument(
        "-er",
        "--eia860_include_retired",
        default=False,
        action="store_true",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_eia_generator_data_from_pudl_sqlite(
    raw_data_directory, pudl_download_directory, report_date, exclude_retired
):
    """
    Generator list from EIA860.
    """
    print("Getting generator list for pudl.sqlite")
    # Connect to pudl.sqlite
    pudl_conn = connect_to_database(
        db_path=os.path.join(pudl_download_directory, "pudl.sqlite")
    )

    # Build the generator query
    exclude_retired_str = (
        "AND core_eia860__scd_generators.operational_status != 'retired'"
        if exclude_retired
        else ""
    )

    query = f"""
        SELECT
            version_num,
            plant_id_eia,
            generator_id,
            balancing_authority_code_eia,
            capacity_mw,
            summer_capacity_mw,
            winter_capacity_mw,
            energy_storage_capacity_mwh,
            prime_mover_code,
            energy_source_code_1,
            current_planned_generator_operating_date,
            generator_retirement_date
        FROM core_eia860__scd_generators
        JOIN core_eia860__scd_plants
        USING (plant_id_eia, report_date),
        alembic_version
        WHERE report_date = '{report_date}'
        {exclude_retired_str}
    """

    # Query pudl.sqlite and save to CSV
    eia_gens = pd.read_sql(query, pudl_conn)
    eia_gens.to_csv(
        os.path.join(raw_data_directory, "eia860_generators.csv"),
        index=False,
    )


# TODO: change to getting from pudl.sqlite once the data are in the main
#  database
def get_eiaaeo_fuel_data_from_pudl_datasette(raw_data_directory):
    """ """
    print("Getting fuel prices (currently from datasette)...")
    total_count = pd.read_csv(
        "https://data.catalyst.coop/pudl.csv?sql=SELECT%0D%0A++COUNT%28*%29%0D%0AFROM%0D%0A++core_eiaaeo__yearly_projected_fuel_cost_in_electric_sector_by_type%0D%0AWHERE%0D%0A++electricity_market_module_region_eiaaeo+like+%27%25western_electricity_coordinating_council%25%27+--ORDER+BY+report_year%2C+electricity_market_module_region_eiaaeo%2C+model_case_eiaaeo%2C+fuel_type_eiaaeo%2C+projection_year+LIMIT+1001&_size=max"
    )["COUNT(*)"][0]

    df_list = []

    page_size = 1000
    current_offset = 0
    while current_offset < total_count:
        df = pd.read_csv(
            f"""https://data.catalyst.coop/pudl.csv?sql=SELECT+*%0D%0AFROM+core_eiaaeo__yearly_projected_fuel_cost_in_electric_sector_by_type%0D%0AWHERE+electricity_market_module_region_eiaaeo+like+%27%25western_electricity_coordinating_council%25%27%0D%0AORDER+BY+report_year%2C+electricity_market_module_region_eiaaeo%2C+model_case_eiaaeo%2C+fuel_type_eiaaeo%2C+projection_year+LIMIT%0D%0A++{current_offset}%2C+{page_size}&_size=max
        """
        )

        df_list.append(df)
        current_offset += page_size

    df_final = pd.concat(df_list)

    df_final.to_csv(
        os.path.join(raw_data_directory, "eiaaeo_fuel_prices.csv"),
        index=False,
    )


def convert_ra_toolkit_profiles_to_csv(raw_data_directory, pudl_download_directory):
    """ """
    print("Converting RA Toolkit profiles to CSV...")
    # TODO: NEVP, PGE, SRP, and WAUW have wind plants in EIA, but we don't have
    #  wind profiles for them in the RA toolkit; I have added those profiles
    #  manually for now
    df = pd.read_parquet(
        os.path.join(
            pudl_download_directory,
            "out_gridpathratoolkit__hourly_available_capacity_factor.parquet",
        ),
        engine="fastparquet",
    )

    df["datetime_pst"] = df["datetime_utc"] - pd.Timedelta(hours=8)
    df["year"] = pd.DatetimeIndex(df["datetime_pst"]).year
    df["month"] = pd.DatetimeIndex(df["datetime_pst"]).month
    df["day_of_month"] = pd.DatetimeIndex(df["datetime_pst"]).day
    df["hour_of_day"] = pd.DatetimeIndex(df["datetime_pst"]).hour

    df = df.rename(
        columns={"aggregation_group": "unit", "capacity_factor": "cap_factor"}
    )
    cols = df.columns.tolist()
    cols = cols[4:8] + cols[1:3]
    df = df[cols]

    df.to_csv(
        os.path.join(raw_data_directory, "var_profiles.csv"),
        sep=",",
        index=False,
    )


def convert_eia930_hourly_interchange_to_csv(
    raw_data_directory, pudl_download_directory
):
    df = pd.read_parquet(
        os.path.join(
            pudl_download_directory, "core_eia930__hourly_interchange.parquet"
        ),
        engine="fastparquet",
    )

    df["datetime_pst"] = df["datetime_utc"] - pd.Timedelta(hours=8)
    df["year"] = pd.DatetimeIndex(df["datetime_pst"]).year
    df["month"] = pd.DatetimeIndex(df["datetime_pst"]).month
    df["day_of_month"] = pd.DatetimeIndex(df["datetime_pst"]).day
    df["hour_of_day"] = pd.DatetimeIndex(df["datetime_pst"]).hour

    # df = df.rename(
    #     columns={"aggregation_group": "unit", "capacity_factor": "cap_factor"}
    # )
    # cols = df.columns.tolist()
    # cols = cols[4:8] + cols[1:3]
    # df = df[cols]

    df.to_csv(
        os.path.join(raw_data_directory, "eia930_hourly_interchange.csv"),
        sep=",",
        index=False,
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    # ### Get only the data we need from pudl.sqlite ### #
    # Generator list
    get_eia_generator_data_from_pudl_sqlite(
        raw_data_directory=parsed_args.raw_data_directory,
        pudl_download_directory=parsed_args.pudl_download_directory,
        report_date=parsed_args.eia860_report_date,
        exclude_retired=not parsed_args.eia860_include_retired,
    )

    # Fuel costs
    get_eiaaeo_fuel_data_from_pudl_datasette(
        raw_data_directory=parsed_args.raw_data_directory
    )

    # ### RA Toolkit profiles ### #
    convert_ra_toolkit_profiles_to_csv(
        raw_data_directory=parsed_args.raw_data_directory,
        pudl_download_directory=parsed_args.pudl_download_directory,
    )

    # ### EIA930 hourly interchange ### #
    convert_eia930_hourly_interchange_to_csv(
        raw_data_directory=parsed_args.raw_data_directory,
        pudl_download_directory=parsed_args.pudl_download_directory,
    )


if __name__ == "__main__":
    main()