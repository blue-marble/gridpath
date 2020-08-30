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
from db.common_functions import connect_to_database, spin_on_database_lock
from db.utilities import scenario
from db.utilities.common_functions import \
    load_all_subscenario_ids_from_dir_to_subscenario_table, \
    load_single_subscenario_id_from_dir_to_subscenario_table, \
    generic_delete_subscenario, determine_tables_to_delete_from, \
    confirm_and_temp_update_affected_tables, repopulate_tables, \
    verify_project_flag_project_alignment


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    # Database name and location options
    parser.add_argument("--database", default="./io.db",
                        help="The database file path relative to the current "
                             "working directory. Defaults to ../db/io.db ")
    parser.add_argument("--csv_location", default="./csvs_test_examples",
                        help="Path to the csvs folder including folder name "
                             "relative to the current working directory.")
    parser.add_argument("--subscenario",
                        default=None,
                        help="The subscenario to load. The script will look "
                             "for the directory where data for the "
                             "subscenario are located based on the "
                             "csv_master file and will load all subscenario "
                             "IDs located there.")
    parser.add_argument("--subscenario_id", default=None,
                        help="The subscenario ID to load. The "
                             "'--subscenario' argument must also be "
                             "specified. The script will look for the "
                             "directory where data for the subscenario are "
                             "located based on the csv_master file and will "
                             "load the data for this subscenario ID.")
    parser.add_argument("--project", default=None,
                        help="The project for which to load data. The "
                             "'--subscenario' and '--subscenario_id' "
                             "arguments must also be specified, and this "
                             "must be a project-level subscenario. The script "
                             "will look for the directory where data for the "
                             "subscenario are located based on the "
                             "csv_master file and will load the data for "
                             "this project and subscenario ID.")
    parser.add_argument("--delete", default=False, action="store_true",
                        help="Delete prior data. Defaults to False.")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print output. Defaults to False.")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def load_all_from_master_csv(conn, csv_path, csv_data_master, quiet):
    """
    :param conn: the database connection
    :param csv_path: str, the directory where the CSV files are located
    :param csv_data_master: Pandas dataframe of the CSV master file
    :param quiet: boolean for whether to print output
    :return:

    Read and load all data specified in the CSV master file.
    """
    # LOAD ALL SUBSCENARIOS WITH NON-CUSTOM INPUTS #
    for index, row in csv_data_master.iterrows():
        # Load data if a directory is specified for this table
        if isinstance(row["path"], str):
            subscenario = row["subscenario"]
            table, inputs_dir, project_flag, cols_to_exclude_str, \
                custom_method, subscenario_type, filename = \
                parse_row(row=row, csv_path=csv_path)
            print("Importing data for subscenario {}, table {} from {}"
                  "...".format(subscenario, table, inputs_dir))
            load_all_subscenario_ids_from_dir_to_subscenario_table(
                conn, subscenario, table, subscenario_type, project_flag,
                cols_to_exclude_str, custom_method, inputs_dir, filename, quiet
            )
        else:
            pass

    # LOAD SCENARIOS DATA #
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
    """
    :param conn: the database connection
    :param csv_path: str, the directory where the CSV files are located
    :param csv_data_master: Pandas dataframe of the CSV master file
    :param subscenario: str; the subscenario for which to load data (e.g.
        temporal_scenario_id or project_portfolio_scenario_id)
    :param quiet: boolean for whether to print output
    :return:

    Read and load all data for a particular subscenario (e.g. for the
    subscenario temporal_scenario_id).
    """
    for index, row in csv_data_master.iterrows():
        # Load data if a directory is specified for this table
        if isinstance(row["path"], str) and row["subscenario"] == subscenario:
            table, inputs_dir, project_flag, cols_to_exclude_str, \
                custom_method, subscenario_type, filename = \
                parse_row(row=row, csv_path=csv_path)
            load_all_subscenario_ids_from_dir_to_subscenario_table(
                conn=conn, subscenario=subscenario, table=table,
                subscenario_type=subscenario_type, project_flag=project_flag,
                cols_to_exclude_str=cols_to_exclude_str,
                custom_method=custom_method, inputs_dir=inputs_dir,
                filename=filename, quiet=quiet
            )
        else:
            pass


def load_single_subscenario_id_from_directory(
    conn, csv_path, csv_data_master, subscenario, subscenario_id_to_load,
    project, delete_flag, quiet
):
    """
    :param conn: the database connection
    :param csv_path: str, the directory where the CSV files are located
    :param csv_data_master: Pandas dataframe of the CSV master file
    :param subscenario: str; the subscenario for which to load data (e.g.
        temporal_scenario_id or project_portfolio_scenario_id)
    :param subscenario_id_to_load: int; the subscenario ID for which to load
        data
    :param project: str; the project for which to load data
    :param delete_flag: boolean for whether to delete prior data
    :param quiet: boolean for whether to print output
    :return:

    Read and load all data for a particular subscenario ID (e.g. for
    temporal_scenario_id=5) or project-subscenario ID (e.g. for project
    'Solar' and variable_generator_scenario_id=1).

    If the delete_flag is turned on, we will first delete prior data for the
    (project-)subscenario_id specified.
    """

    # Delete prior data if instructed to
    if delete_flag:
        # Determine the relevant tables we'll need to delete prior data from
        # If we're dealing with project-level data, we'll also get the
        # base_table and base_subscenario (e.g. the opchar table for
        # variable generator profiles); otherwise, these will be None
        subscenario_table, input_tables, project_flag, base_table, \
            base_subscenario = determine_tables_to_delete_from(
                csv_data_master=csv_data_master, subscenario=subscenario
            )

        # Verify project-project_flag aligmnet
        verify_project_flag_project_alignment(
            project=project, project_flag=project_flag, subscenario=subscenario
        )

        # If this subscenario ID (or the base subscenario ID if
        # project-level data) is used in the scenarios table, we'll confirm
        # with the user that they want to update the inputs
        # We'll also need to temporarily NULLify this ID in the scenarios
        # table to avoid FOREIGN KEY errors when deleting the data
        scenario_reupdate_tuples, base_subscenario_ids_str, \
            base_subscenario_ids_data = \
            confirm_and_temp_update_affected_tables(
                conn=conn, project_flag=project_flag,
                subscenario=subscenario,
                subscenario_id=subscenario_id_to_load, project=project,
                base_table=base_table, base_subscenario=base_subscenario
            )

        # Delete prior data
        generic_delete_subscenario(
            conn=conn, subscenario=subscenario,
            subscenario_id=subscenario_id_to_load, project=project,
            subscenario_table=subscenario_table, input_tables=input_tables,
            project_flag=project_flag
        )

    # Import the data
    for index, row in csv_data_master.iterrows():
        # Load data if a directory is specified for this table
        if isinstance(row["path"], str) and row["subscenario"] == subscenario:

            # Parse the row
            table, inputs_dir, project_flag, cols_to_exclude_str, \
                custom_method, subscenario_type, filename = \
                parse_row(row=row, csv_path=csv_path)

            # Verify project-project_flag alignment
            verify_project_flag_project_alignment(
                project=project, project_flag=project_flag,
                subscenario=subscenario
            )

            # Load the data for this (project-)subscenario_id
            load_single_subscenario_id_from_dir_to_subscenario_table(
                conn=conn, subscenario=subscenario, table=table,
                subscenario_type=subscenario_type, project_flag=project_flag,
                cols_to_exclude_str=cols_to_exclude_str,
                custom_method=custom_method, inputs_dir=inputs_dir,
                filename=filename, quiet=quiet,
                subscenario_id_to_load=subscenario_id_to_load,
                project=project
            )
        else:
            pass

    # If data were deleted, repopulate the affected scenarios with the data
    # we NULLified above
    if delete_flag:
        repopulate_tables(
            conn=conn, project_flag=project_flag, subscenario=subscenario,
            subscenario_id=subscenario_id_to_load, project=project,
            base_table=base_table, base_subscenario=base_subscenario,
            scenario_reupdate_tuples=scenario_reupdate_tuples,
            base_subscenario_ids_str=base_subscenario_ids_str,
            base_subscenario_ids_data=base_subscenario_ids_data
        )


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
    if parsed_args.subscenario is None and parsed_args.subscenario_id is \
            None and parsed_args.project is None:
        load_all_from_master_csv(
            conn=conn, csv_path=csv_path, csv_data_master=csv_data_master,
            quiet=parsed_args.quiet
        )
    elif parsed_args.subscenario is not None and parsed_args.subscenario_id \
            is None:
        # Load all IDs for a subscenario-table
        load_all_subscenario_ids_from_directory(
            conn, csv_path, csv_data_master, parsed_args.subscenario,
            parsed_args.delete,
            parsed_args.quiet
        )
    else:
        # Load single subscenario ID (or project-subscenario ID)
        load_single_subscenario_id_from_directory(
            conn=conn, csv_path=csv_path, csv_data_master=csv_data_master,
            subscenario=parsed_args.subscenario,
            subscenario_id_to_load=parsed_args.subscenario_id,
            project=parsed_args.project,
            delete_flag=parsed_args.delete,
            quiet=parsed_args.quiet
        )

    # Close connection
    conn.close()


def parse_row(row, csv_path):
    """
    :param row:
    :param csv_path:
    :return:

    Parse a row of the CSV master file.
    """
    table = row["table"]
    inputs_dir = os.path.join(csv_path, row["path"])
    project_flag = True if int(row["project_input"]) else False
    cols_to_exclude_str = str(row["cols_to_exclude_str"])
    custom_method = str(row["custom_method"])
    subscenario_type = row["subscenario_type"]
    filename = row["filename"]

    return table, inputs_dir, project_flag, cols_to_exclude_str, \
        custom_method, subscenario_type, filename


if __name__ == "__main__":
    main()
