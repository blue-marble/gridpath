#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The *port_csvs_to_gridpath.py* script ports the input data provided through
csvs to the sql database, which is created using the create_database.py
script. The csv_data_master.csv has the list of all the subscenarios in the
gridpath database. The 'required' column in this csv indicates whether the
subscenario is required [1] or optional [0]. The 'include' column indicates
whether the user would like to include this subscenario and import the csv data
into this subscenario [1] or omit the subscenario [0]. The paths to the csv data
subfolders that house the csv scenario data for each subscenario are also proided
in this master csv.

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

The input params for this script include database name (db_name_, database
path (db_location), and csvs folder path (csv_location. The defaults are the
"io.db" database and "csvs" folder located under the "db" folder.

"""

import numpy as np
import os
import pandas as pd
import sqlite3
import sys
from argparse import ArgumentParser

# Data-import modules
from db.common_functions import connect_to_database
from db.create_database import get_database_file_path
import db.utilities.common_functions as db_util
from db.utilities import temporal, scenario, solver_options

# Reserves list


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    # Database name and location options
    # Adding defaults here even though the connect_to_database function has its own defaults
    # because parser passes a text string of None and not a python None
    parser.add_argument("--db_name", default="io",
                        help="Name of the database without the db extension.")
    parser.add_argument("--db_location", default=".",
                        help="Path to the database (relative to "
                             "port_csvs_to_db.py).")
    parser.add_argument("--csv_location", default="csvs",
                        help="Path to the csvs folder including folder name (relative to "
                             "port_csvs_to_db.py).")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print output.")
    #TODO: Using this argument for using the get_database_file_path function in create_database
    # but not sure if we need it.
    parser.add_argument("--in_memory", default=False, action="store_true",
                        help="Create in-memory database. The db_name and "
                             "db_location argument will be inactive.")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_csv_folder_path(parsed_arguments, relative_path=".."):
    """
    :param parsed_arguments: the parsed script arguments
    :return: the path to the csv folder

    Get the csv folder path from the script arguments.
    If no csv folder is specified, assume that the folder is
    called 'csvs' and it is located under the 'db' folder.
    """

    csv_path = str(parsed_arguments.csv_location)

    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__),
                                relative_path, "db", "csvs")

    if not os.path.isdir(csv_path):
        raise OSError(
            "The csv folder {} was not found. Did you mean to "
            "specify a different csv folder?".format(
                os.path.abspath(csv_path)
            )
        )

    return csv_path


def load_csv_data(conn, csv_path, quiet):
    """
    The 'main' method parses the database name along with path as
    script arguments, reads the data from csvs, and loads the data
    in the database.

    """

    c = conn.cursor()

    #### MASTER CSV DATA ####
    # If include flag is 1, then read the feature, subscenario_id, and
    # path into a dictionary and call the specific function for the feature
    csv_data_master = pd.read_csv(
        os.path.join(csv_path, 'csv_data_master.csv')
    )

    #### LOAD ALL SUBSCENARIOS WITH NON-CUSTOM INPUTS ####
    csv_subscenarios_simple = csv_data_master.loc[
        csv_data_master["subscenario_type"] != "custom"
    ]
    for index, row in csv_subscenarios_simple.iterrows():
        if row["include"] == 1:
            subscenario = row["subscenario"]
            table = row["table"]
            inputs_dir = os.path.join(csv_path, row["path"])
            project_flag = True if int(row["project_input"]) else False
            cols_to_exclude_str = str(row["cols_to_exclude_str"])
            if row["subscenario_type"] == "simple":
                db_util.read_all_csv_subscenarios_from_dir_and_insert_into_db(
                    conn=conn,
                    quiet=quiet,
                    subscenario=subscenario,
                    table=table,
                    inputs_dir=inputs_dir,
                    use_project_method=project_flag,
                    cols_to_exclude_str=cols_to_exclude_str
                )
            elif row["subscenario_type"] in ["dir_main", "dir_aux"]:
                filename = row["filename"]
                if row["subscenario_type"] == "dir_main":
                    skip_subscenario_info = False
                else:
                    skip_subscenario_info = True
                db_util.read_all_dir_subscenarios_from_dir_and_insert_into_db(
                    conn=conn,
                    quiet=quiet,
                    inputs_dir=inputs_dir,
                    subscenario=subscenario,
                    table=table,
                    filename=filename,
                    skip_subscenario_info=skip_subscenario_info,
                    cols_to_exclude_str=cols_to_exclude_str
                )

        else:
            pass

    ### CUSTOM LOADING ###
    #### LOAD TEMPORAL DATA ####
    # Handled differently, as a temporal_scenario_id involves multiple files
    temporal_directory = db_util.get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
        subscenario="temporal_scenario_id"
    )
    if temporal_directory is not None:
        temporal_subscenario_directories = \
            db_util.get_directory_subscenarios(
                main_directory=temporal_directory,
                quiet=quiet
            )
        for subscenario_directory in temporal_subscenario_directories:
            temporal.load_from_csvs(
                conn=conn, subscenario_directory=subscenario_directory
            )
    else:
        print("ERROR: temporal_scenario_id is required")
        sys.exit()


    #### LOAD SCENARIOS DATA ####
    scenarios_dir = db_util.get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
        subscenario="scenarios"
    )
    if scenarios_dir is not None:
        f_number = 0
        for f in os.listdir(scenarios_dir):
            if f.endswith(".csv") and 'template' not in f and 'scenario' in f \
                    and 'ignore' not in f:
                if not quiet:
                    print(f)
                f_number = f_number + 1
                opchar_data_input = pd.read_csv(os.path.join(scenarios_dir, f))
                if f_number > 1:
                    print('Error: More than one scenario csv input files')

        scenario.load_scenarios_from_csv(conn, c, opchar_data_input)
    else:
        print("ERROR: scenarios table is required")


    #### LOAD SOLVER OPTIONS ####
    solver_dir = db_util.get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
        subscenario="solver_options_id"
    )
    if solver_dir is not None:
        for f in os.listdir(solver_dir):
            if f.endswith(".csv") and 'template' not in f and 'options' in f:
                if not quiet:
                    print(f)
                csv_solver_options = pd.read_csv(os.path.join(solver_dir, f))
            if f.endswith(".csv") and 'template' not in f \
                    and 'descriptions' in f:
                if not quiet:
                    print(f)
                csv_solver_descriptions = \
                    pd.read_csv(os.path.join(solver_dir, f))

        solver_options.load_solver_options(
            conn, c, csv_solver_options, csv_solver_descriptions
        )


def main(args=None):
    """
    The 'main' method parses the database name along with path as
    script arguments and loads the data in the database.
    """
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(args=args)

    db_path = get_database_file_path(parsed_arguments=parsed_args)
    csv_path = get_csv_folder_path(parsed_arguments=parsed_args)

    # Register numpy types with sqlite, so that they are properly inserted
    # from pandas dataframes
    # https://stackoverflow.com/questions/38753737/inserting-numpy-integer-types-into-sqlite-with-python3
    sqlite3.register_adapter(np.int64, lambda val: int(val))
    sqlite3.register_adapter(np.float64, lambda val: float(val))

    # connect to database
    conn = connect_to_database(db_path=db_path)

    # Load data
    load_csv_data(conn=conn, csv_path=csv_path, quiet=parsed_args.quiet)

    # Close connection
    conn.close()


if __name__ == "__main__":
    main()
