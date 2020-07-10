#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The *port_csvs_to_gridpath.py* script ports the input data provided through
CSVS to the SQLite database, which is created using the create_database.py
script. The csv_data_master.csv has the list of all the subscenarios and
associated tables in the GridPath database. CSV data is imported if a path is
specified for each table.

The script will look for CSV files in each subscenario's subfolder. It is
expecting that the CSV filenames will conform to a certain structure
indicating the ID and name for the subscenarios, and contain the data for
the subscenarios. See csvs_to_db_utilities.csvs_read for the  specific
requirements depending on the function called from that module.

The scenario.csv under the scenario folder holds the input data for the
subscenario, which indicates which subscenarios should be included in a
particular scenario by providing the subscenario_id. Each scenario has a
separate column. The user-defined name of the scenario should be entered as
the name of the scenario column.

The input params for this script include database file path (database),
and csvs folder path (csv_location). The defaults are the
"../db/io.db" database and "csvs" folder located under the "db" folder.

"""

import numpy as np
import os
import pandas as pd
import sqlite3
import sys
from argparse import ArgumentParser

# Data-import modules
from db.common_functions import connect_to_database
from db.utilities import scenario
from db.utilities.common_functions import \
    load_all_subscenario_ids_from_dir_to_subscenario_table, \
    load_single_subscenario_id_from_dir_to_subscenario_table


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    # Database name and location options
    parser.add_argument("--database", default="../db/test_examples.db",
                        help="The database file path relative to the current "
                             "working directory. Defaults to ../db/io.db ")
    parser.add_argument("--csv_location", default="../db/csvs_test_examples",
                        help="Path to the csvs folder including folder name "
                             "relative to the current working directory.")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print output.")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def load_all_from_master_csv(conn, csv_path, csv_data_master, quiet):
    """
    The 'main' method parses the database name along with path as
    script arguments, reads the data from csvs, and loads the data
    in the database.

    """
    #### LOAD ALL SUBSCENARIOS WITH NON-CUSTOM INPUTS ####
    for index, row in csv_data_master.iterrows():
        # Load data if a directory is specified for this table
        if isinstance(row["path"], str):
            subscenario = row["subscenario"]
            table = row["table"]
            inputs_dir = os.path.join(csv_path, row["path"])
            project_flag = True if int(row["project_input"]) else False
            cols_to_exclude_str = str(row["cols_to_exclude_str"])
            custom_method = str(row["custom_method"])
            subscenario_type = row["subscenario_type"]
            filename = row["filename"]
            load_all_subscenario_ids_from_dir_to_subscenario_table(
                conn, subscenario, table, subscenario_type, project_flag,
                cols_to_exclude_str, custom_method, inputs_dir, filename,
                quiet
            )
        else:
            pass

    #### LOAD SCENARIOS DATA ####
    # A scenarios.csv file is expected in the csv_path directory
    # TODO: maybe allow this to be skipped
    scenarios_df = pd.read_csv(
        os.path.join(csv_path, "scenarios.csv")
    )

    c = conn.cursor()
    for sc in scenarios_df.columns.to_list()[1:]:
        scenario_info = scenarios_df.set_index(
            'optional_feature_or_subscenarios'
        )[sc].to_dict()
        scenario_info["scenario_name"] = sc

        scenario.create_scenario(
            io=conn, c=c, column_values_dict=scenario_info
        )


def load_all_subscenario_ids_from_directory(
        conn, csv_path, csv_data_master, subscenario, quiet
):
    for index, row in csv_data_master.iterrows():
        # Load data if a directory is specified for this table
        if isinstance(row["path"], str) and row["subscenario"] == subscenario:
            table = row["table"]
            inputs_dir = os.path.join(csv_path, row["path"])
            project_flag = True if int(row["project_input"]) else False
            cols_to_exclude_str = str(row["cols_to_exclude_str"])
            custom_method = str(row["custom_method"])
            subscenario_type = row["subscenario_type"]
            filename = row["filename"]
            load_all_subscenario_ids_from_dir_to_subscenario_table(
                conn, subscenario, table, subscenario_type, project_flag,
                cols_to_exclude_str, custom_method, inputs_dir, filename,
                quiet
            )
        else:
            pass


def load_single_subscenario_id_from_directory(
        conn, csv_path, csv_data_master, subscenario,
        subscenario_id_to_load, quiet
):
    for index, row in csv_data_master.iterrows():
        # Load data if a directory is specified for this table
        if isinstance(row["path"], str) and row["subscenario"] == subscenario:
            table = row["table"]
            inputs_dir = os.path.join(csv_path, row["path"])
            project_flag = True if int(row["project_input"]) else False
            cols_to_exclude_str = str(row["cols_to_exclude_str"])
            custom_method = str(row["custom_method"])
            subscenario_type = row["subscenario_type"]
            filename = row["filename"]
            load_single_subscenario_id_from_dir_to_subscenario_table(
                conn, subscenario, table, subscenario_type, project_flag,
                cols_to_exclude_str, custom_method, inputs_dir, filename,
                quiet,
                subscenario_id_to_load
            )
        else:
            pass


def main(args=None):
    """
    The 'main' method parses the database name along with path as
    script arguments and loads the data in the database.
    """
    # Parse the arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(args=args)

    # Get the database path
    db_path = parsed_args.database
    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database?".format(
                os.path.abspath(db_path)
            )
        )

    # Get the CSV directory
    csv_path = parsed_args.csv_location
    if not os.path.isdir(csv_path):
        raise OSError(
            "The csv folder {} was not found. Did you mean to "
            "specify a different csv folder?".format(
                os.path.abspath(csv_path)
            )
        )

    #### MASTER CSV DATA ####
    csv_data_master = pd.read_csv(
        os.path.join(csv_path, 'csv_data_master.csv')
    )

    # Register numpy types with sqlite, so that they are properly inserted
    # from pandas dataframes
    # https://stackoverflow.com/questions/38753737/inserting-numpy-integer-types-into-sqlite-with-python3
    sqlite3.register_adapter(np.int64, lambda val: int(val))
    sqlite3.register_adapter(np.float64, lambda val: float(val))

    # connect to database
    conn = connect_to_database(db_path=db_path)

    # Load all data in directory
    load_all_from_master_csv(
        conn=conn, csv_path=csv_path, csv_data_master=csv_data_master,
        quiet=parsed_args.quiet
    )

    # Load all IDs for a subscenario-table
    load_all_subscenario_ids_from_directory(
        conn, csv_path, csv_data_master, parsed_args.subscenario,
        parsed_args.quiet
    )

    # Load single subscenario ID

    # Close connection
    conn.close()


if __name__ == "__main__":
    main()
