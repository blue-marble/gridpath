# Copyright 2016-2023 Blue Marble Analytics LLC.
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
import os.path
import pandas as pd

from db.common_functions import spin_on_database_lock_generic, connect_to_database


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database")
    parser.add_argument("-csv", "--csv_location")
    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Importing raw data...")

    conn = connect_to_database(db_path=parsed_args.database)

    files_to_import_df = pd.read_csv(
        os.path.join(parsed_args.csv_location, "files_to_import.csv")
    )
    for index, row in files_to_import_df.iterrows():
        import_bool, f, table = row

        if import_bool:
            if not parsed_args.quiet:
                print(f"... {f}...")
            f_path = os.path.join(parsed_args.csv_location, f)
            df = pd.read_csv(f_path, delimiter=",")

            spin_on_database_lock_generic(
                command=df.to_sql(
                    name=table,
                    con=conn,
                    if_exists="append",
                    index=False,
                )
            )


if __name__ == "__main__":
    main()
