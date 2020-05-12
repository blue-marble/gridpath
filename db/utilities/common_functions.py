#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Common functions for data-loading utilities and port script.
"""

import os
import pandas as pd
import warnings

from db.utilities import csvs_read


def get_directory_subscenarios(main_directory, quiet):
    # Get list of subdirectories (which are the names of our subscenarios)
    # Each temporal subscenario is a directory, with the scenario ID,
    # underscore, and the scenario name as the name of the directory (already
    # passed here).

    # Make a list to which we'll append the full paths of the subscenario
    # directories
    subscenario_directories = list()

    # First we'll get the directory names (not full paths) and check that
    # they conform to the requirements
    subscenario_dir_names = sorted(next(os.walk(main_directory))[1])
    for subscenario in subscenario_dir_names:
        if not quiet:
            print(subscenario)
        if not subscenario.split("_")[0].isdigit():
            warnings.warn(
                "Subfolder `{}` does not start with an integer to "
                "indicate the subscenario ID and CSV import script will fail. "
                "Please follow the required folder naming structure "
                "<subscenarioID_subscenarioName>, e.g. "
                "'1_default4periods'.".format(subscenario)
            )

        # Get the full path of the subscenario directory and append to the
        # directory list
        subscenario_directory = os.path.join(main_directory, subscenario)
        subscenario_directories.append(subscenario_directory)

    return subscenario_directories


def parse_subscenario_directory_contents(
        subscenario_directory, csv_file_names
):
    # Get the paths for the required input files
    csv_file_paths = [
        os.path.join(subscenario_directory, csv_file_name)
        for csv_file_name in csv_file_names
    ]

    # Get subscenario ID, name, and description
    # The subscenario directory must start with an integer for the
    # subscenario_id followed by "_" and then the subscenario name
    # The subscenario description must be in the description.txt file under
    # the subscenario directory
    directory_basename = os.path.basename(subscenario_directory)
    subscenario_id = int(directory_basename.split("_", 1)[0])
    subscenario_name = directory_basename.split("_", 1)[1]

    # Check if there's a description file, otherwise the description will be
    # an empty string
    description_file = os.path.join(subscenario_directory, "description.txt")
    if os.path.exists(description_file):
        with open(description_file, "r") as f:
            subscenario_description = f.read()
    else:
        subscenario_description = ""

    # Make the tuple for insertion into the subscenario table
    subscenario_tuple = \
        (subscenario_id, subscenario_name, subscenario_description)

    return subscenario_tuple, csv_file_paths


def csv_to_tuples(subscenario_id, csv_file):
    """
    :param subscenario_id: int
    :param csv_file: str, path to CSV file
    :return: list of tuples

    Convert the data from a CSV into a list of tuples for insertion into an
    input table.
    """
    df = pd.read_csv(csv_file, delimiter=",")
    tuples_for_import = [
        (subscenario_id,) + tuple(x)
        for x in df.to_records(index=False)
    ]

    return tuples_for_import


def read_data_and_insert_into_db(
        conn, csv_data_master, csvs_main_dir, quiet, table, insert_method,
        none_message, use_project_method=False, **kwargs
):
    """
    Read data, convert to tuples, and insert into database.
    """
    # Check if we should include the table
    inputs_dir = get_inputs_dir(
        csvs_main_dir=csvs_main_dir, csv_data_master=csv_data_master,
        table=table
    )

    # Get the subscenario info and data; this will return False, False if
    # the subscenario is not included
    csv_subscenario_input, csv_data_input = read_inputs(
        csvs_main_dir=csvs_main_dir,
        csv_data_master=csv_data_master,
        table=table,
        quiet=quiet,
        use_project_method=use_project_method
    )

    # If the subscenario is included, make a list of tuples for the subscenario
    # and inputs, and insert into the database via the relevant method
    if csv_subscenario_input is not False and csv_data_input is not False:
        if not use_project_method:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_data(inputs_dir, quiet)
        else:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_project_data(
                    inputs_dir, quiet
                )

        subscenario_tuples = [
            tuple(x) for x in csv_subscenario_input.to_records(index=False)
        ]
        inputs_tuples = [
            tuple(x) for x in csv_data_input.to_records(index=False)
         ]

        # Insertion method
        insert_method(
            conn=conn,
            subscenario_data=subscenario_tuples,
            inputs_data=inputs_tuples,
            **kwargs
        )
    # If not included, print the none_message
    else:
        print(none_message)


def get_inputs_dir(csvs_main_dir, csv_data_master, table):
    if csv_data_master.loc[
        csv_data_master['table'] == table, 'include'
    ].iloc[0] == 1:
        inputs_dir = os.path.join(
            csvs_main_dir,
            csv_data_master.loc[
                csv_data_master['table'] == table,
                'path'
            ].iloc[0]
        )
    else:
        inputs_dir = None

    return inputs_dir


def read_inputs(
    csvs_main_dir, csv_data_master, table, quiet, use_project_method=False
):
    data_folder_path = get_inputs_dir(
        csvs_main_dir=csvs_main_dir, csv_data_master=csv_data_master, table=table
    )
    if data_folder_path is not None:
        if not use_project_method:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_data(
                    folder_path=data_folder_path, quiet=quiet
                )
        else:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_project_data(
                    folder_path=data_folder_path, quiet=quiet
                )

        return csv_subscenario_input, csv_data_input
    else:
        return False, False
