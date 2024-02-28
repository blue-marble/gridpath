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

import sys
from argparse import ArgumentParser
import csv
import os.path
import pandas as pd

from db.utilities.ra_toolkit.temporal import create_temporal_iteration_csv


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """

    parser = ArgumentParser(add_help=True)

    parser.add_argument("-csv", "--csv_path")

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating temporal scenarios...")

    df = pd.read_csv(parsed_args.csv_path, delimiter=",")

    for index, row in df.iterrows():
        (
            output_directory,
            temporal_scenario_id,
            temporal_scenario_name,
            n_passes,
            iterations_csv,
        ) = row

        if not parsed_args.quiet:
            print(f"...{temporal_scenario_id}_{temporal_scenario_name}...")
        subscenario_directory = os.path.join(
            os.getcwd(),
            output_directory,
            f"{str(temporal_scenario_id)}" f"_{temporal_scenario_name}",
        )

        create_temporal_iteration_csv.main(
            [
                "--n_passes",
                str(n_passes),
                "--csv_path",
                iterations_csv,
                "--output_directory",
                subscenario_directory,
            ]
        )


if __name__ == "__main__":
    main()
