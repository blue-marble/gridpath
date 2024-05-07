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
        "-d",
        "--raw_data_directory",
        default="../../csvs_open_data/raw_data",
        action="store_true",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_data_from_catalyst():
    count = pd.read_csv(
        "https://data.catalyst.coop/pudl.csv?sql=SELECT%0D%0A++++count%28*%29%0D%0AFROM+core_eia860__scd_generators%0D%0AJOIN+core_eia860__scd_plants%0D%0AUSING+%28plant_id_eia%2C+report_date%29%2C%0D%0Aalembic_version%0D%0AWHERE+report_date+%3D+%272023-01-01%27+--+get+latest%0D%0AAND+core_eia860__scd_generators.operational_status+%21%3D+%27retired%27&_size=max"
    )["count(*)"][0]

    df_list = []

    current_count = 0
    while current_count < count:
        df = pd.read_csv(
            f"https://data.catalyst.coop/pudl.csv?sql=SELECT%0D%0A++++version_num"
            f"%2C%0D%0A++++report_date%2C%0D%0A++++"
            f"plant_id_eia%2C%0D%0A++++generator_id%2C%0D%0A"
            f"++++balancing_authority_code_eia%2C%0D%0A++++capacity_mw%2C%0D%0A"
            f"++++summer_capacity_mw%2C%0D%0A++++winter_capacity_mw%2C%0D%0A"
            f"++++energy_storage_capacity_mwh%2C%0D%0A++++prime_mover_code%2C%0D"
            f"%0A++++current_planned_generator_operating_date%2C%0D%0A"
            f"++++generator_retirement_date%0D%0AFROM+core_eia860__scd_generators"
            f"%0D%0AJOIN+core_eia860__scd_plants%0D%0AUSING+%28plant_id_eia%2C+"
            f"report_date%29%2C%0D%0Aalembic_version%0D%0AWHERE+"
            f"report_date+%3D+%272023-01-01%27+--+get+latest%0D%0AAND+"
            f"core_eia860__scd_generators.operational_status+%21%3D+"
            f"%27retired%27%0D%0ALIMIT+{current_count}%2C+1000&_size=max"
        )

        df_list.append(df)
        current_count += 1000

    data = pd.concat(df_list)

    return data


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    data = get_data_from_catalyst()

    data.to_csv(
        os.path.join(parsed_args.raw_data_directory, "eia860_generators.csv"),
        index=False,
    )


if __name__ == "__main__":
    main()
