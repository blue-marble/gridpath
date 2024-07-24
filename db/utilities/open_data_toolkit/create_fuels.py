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
    parser.add_argument(
        "-fuel_price_id", "--fuel_price_scenario_id", default=1
    )
    parser.add_argument(
        "-fuel_price_name",
        "--fuel_price_scenario_name",
        default="aeo",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments



def get_fuel_prices():
    pass
