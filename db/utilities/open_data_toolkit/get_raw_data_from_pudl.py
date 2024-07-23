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
import gzip
import io
import os.path
import pandas as pd
import requests
import shutil
import sys
import zipfile

from db.common_functions import connect_to_database

"""
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
WHERE report_date = '2023-01-01' -- get latest
AND (
    unixepoch(core_eia860__scd_generators.current_planned_generator_operating_date) 
    >= unixepoch('2026-01-01')
    OR core_eia860__scd_generators.current_planned_generator_operating_date IS NULL
    )
AND (
    unixepoch(core_eia860__scd_generators.generator_retirement_date) > 
    unixepoch('2026-12-31')
    OR core_eia860__scd_generators.generator_retirement_date IS NULL
    )
AND core_eia860__scd_generators.operational_status != 'retired'
"""


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument(
        "-skip", "--skip_pudl_sqlite_download", default=False, action="store_true"
    )
    parser.add_argument(
        "-d",
        "--raw_data_directory",
        default="../../csvs_open_data/raw_data",
    )

    parser.add_argument("-rdate", "--eia860_report_date", default="2023-01-01")

    # TODO: probably move this to downstream queries
    parser.add_argument(
        "-er",
        "--eia860_include_retired",
        default=False,
        action="store_true",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_pudl_sqlite(zenodo_record, pudl_sqlite_directory):
    URL = f"https://sandbox.zenodo.org/records/{str(zenodo_record)}/files/pudl.sqlite.zip?download=1"
    print("Downloading compressed pudl.sqlite...")
    pudl_request_content = requests.get(URL, stream=True).content

    print("Extracting database")
    # with gzip.open(io.BytesIO(pudl_request_content), "rb") as f_in:
    #     with open(pudl_sqlite_path, "wb") as f_out:
    #         shutil.copyfileobj(f_in, f_out)

    z = zipfile.ZipFile(io.BytesIO(pudl_request_content))
    z.extractall(pudl_sqlite_directory)


def get_eia_generator_data_from_local_db(
    out_dir, pudl_sqlite_directory, report_date, exclude_retired
):

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

    pudl_conn = connect_to_database(
        db_path=os.path.join(pudl_sqlite_directory, "pudl.sqlite")
    )

    eia_gens = pd.read_sql(query, pudl_conn)

    eia_gens.to_csv(
        os.path.join(out_dir, "eia860_generators.csv"),
        index=False,
    )


def get_eia_generator_data_from_pudl_datasette():
    """
    DEPRECATED
    """
    count = pd.read_csv(
        "https://data.catalyst.coop/pudl.csv?sql=SELECT%0D%0A++++count%28*%29%0D%0AFROM+core_eia860__scd_generators%0D%0AJOIN+core_eia860__scd_plants%0D%0AUSING+%28plant_id_eia%2C+report_date%29%2C%0D%0Aalembic_version%0D%0AWHERE+report_date+%3D+%272023-01-01%27+--+get+latest%0D%0AAND+core_eia860__scd_generators.operational_status+%21%3D+%27retired%27&_size=max"
    )["count(*)"][0]

    df_list = []

    page_size = 1000
    current_offset = 0
    while current_offset < count:
        df = pd.read_csv(
            f"https://data.catalyst.coop/pudl.csv?sql=SELECT%0D%0A++++version_num"
            f"%2C%0D%0A++++report_date%2C%0D%0A++++"
            f"plant_id_eia%2C%0D%0A++++generator_id%2C%0D%0A"
            f"++++balancing_authority_code_eia%2C%0D%0A++++capacity_mw%2C%0D%0A"
            f"++++summer_capacity_mw%2C%0D%0A++++winter_capacity_mw%2C%0D%0A"
            f"++++energy_storage_capacity_mwh%2C%0D%0A++++prime_mover_code%2C%0D"
            f"%0A++++energy_source_code_1%2C%0D%0A"
            f"++++current_planned_generator_operating_date%2C%0D%0A"
            f"++++generator_retirement_date%0D%0AFROM+core_eia860__scd_generators"
            f"%0D%0AJOIN+core_eia860__scd_plants%0D%0AUSING+%28plant_id_eia%2C+"
            f"report_date%29%2C%0D%0Aalembic_version%0D%0AWHERE+"
            f"report_date+%3D+%272023-01-01%27+--+get+latest%0D%0AAND+"
            f"core_eia860__scd_generators.operational_status+%21%3D+"
            f"%27retired%27%0D%0ALIMIT+{current_offset}%2C+"
            f"{page_size}&_size=max"
        )

        df_list.append(df)
        current_offset += 1000

    data = pd.concat(df_list)

    return data


# TODO: change to getting from pudl.sqlite once the data are in
def get_eiaaeo_fuel_data_from_pudl_datasette():
    """ """
    print("Getting fuel prices...")
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

    return df_final


# TODO: what will be the stable version of this?
def get_ra_toolkit_cap_factor_data_from_pudl_nightly():
    url = "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_gridpathratoolkit__hourly_available_capacity_factor.parquet"
    data = requests.get(url, stream=True).content

    return data


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    pudl_sqlite_directory = os.path.join(parsed_args.raw_data_directory)

    # # Download the database
    # if not parsed_args.skip_pudl_sqlite_download:
    #     get_pudl_sqlite(
    #         pudl_sqlite_directory=pudl_sqlite_directory, zenodo_record=90548
    #     )
    #
    # # Get the data we need from the database
    # get_eia_generator_data_from_local_db(
    #     out_dir=parsed_args.raw_data_directory,
    #     pudl_sqlite_directory=pudl_sqlite_directory,
    #     report_date=parsed_args.eia860_report_date,
    #     exclude_retired=not parsed_args.eia860_include_retired,
    # )
    #
    # ra_toolkit_gen_profiles = get_ra_toolkit_cap_factor_data_from_pudl_nightly()
    # with open(
    #     os.path.join(parsed_args.raw_data_directory, "ra_toolkit_gen_profiles.parquet"),
    #     "wb",
    # ) as f:
    #     f.write(ra_toolkit_gen_profiles)

    # Get fuel prices from datasette (needs to be updated to get this from
    # pudl.sqlite when available)
    aeo_fuel_prices = get_eiaaeo_fuel_data_from_pudl_datasette()
    aeo_fuel_prices.to_csv(
        os.path.join(parsed_args.raw_data_directory, "eiaaeo_fuel_prices.csv"),
        index=False,
    )


if __name__ == "__main__":
    main()
