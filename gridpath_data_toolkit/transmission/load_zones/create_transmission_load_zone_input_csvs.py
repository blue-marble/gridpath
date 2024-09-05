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
import numpy as np
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database
from gridpath_data_toolkit.transmission.transmission_data_filters_common import (
    get_all_links_sql,
)


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
        "-o",
        "--output_directory",
        default="../../csvs_open_data/transmission/load_zones",
    )
    parser.add_argument("-lz_id", "--transmission_load_zone_scenario_id", default=1)
    parser.add_argument(
        "-lz_name", "--transmission_load_zone_scenario_name", default="wecc_baas"
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_tx_load_zones(
    all_links,
    output_directory,
    subscenario_id,
    subscenario_name,
):
    """ """
    lz_dict = {
        "transmission_line": [f"{link[0]}_{link[1]}" for link in all_links],
        "load_zone_from": [link[0] for link in all_links],
        "load_zone_to": [link[1] for link in all_links],
    }

    df = pd.DataFrame(lz_dict)

    df.to_csv(
        os.path.join(output_directory, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def main(args=None):
    print("Creating transmission load zone inputs")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    os.makedirs(parsed_args.output_directory, exist_ok=True)

    conn = connect_to_database(db_path=parsed_args.database)

    c = conn.cursor()

    all_links = c.execute(get_all_links_sql(region="WECC")).fetchall()

    get_tx_load_zones(
        all_links=all_links,
        output_directory=parsed_args.output_directory,
        subscenario_id=parsed_args.transmission_load_zone_scenario_id,
        subscenario_name=parsed_args.transmission_load_zone_scenario_name,
    )


if __name__ == "__main__":
    main()
