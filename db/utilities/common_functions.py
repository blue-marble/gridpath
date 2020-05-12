#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Common functions for data-loading utilities and port script.
"""

import os
import pandas as pd
import warnings


def get_inputs_dir(csvs_main_dir, csv_data_master, table):
    """
    :param csvs_main_dir:
    :param csv_data_master:
    :param table:
    :return:

    Get the inputs directory listed in the CSV master file for a particular
    subscenario (for now, "table").
    """
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
    """
    :param csvs_main_dir:
    :param csv_data_master:
    :param table:
    :param quiet:
    :param use_project_method:
    :return:

    Check if subscenario is included in the CSV master file and read the
    data from the specified directory. If not included, return False, False.
    """
    data_folder_path = get_inputs_dir(
        csvs_main_dir=csvs_main_dir, csv_data_master=csv_data_master,
        table=table
    )
    if data_folder_path is not None:
        if not use_project_method:
            (csv_subscenario_input, csv_data_input) = \
                csv_read_data(
                    folder_path=data_folder_path, quiet=quiet
                )
        else:
            (csv_subscenario_input, csv_data_input) = \
                csv_read_project_data(
                    folder_path=data_folder_path, quiet=quiet
                )

        return csv_subscenario_input, csv_data_input
    else:
        return False, False


# TODO: can we consolidate the csv_read_data and csv_read_project_data
#  functions, as they are very similar?

# TODO: add a check that subscenario IDs are unique
def csv_read_data(folder_path, quiet):
    """
    :param folder_path: Path to folder with input csv files
    :param quiet: boolean
    :return subscenario_df: Pandas dataframe with subscenario id, name,
        description
    :return data_df: Pandas dataframe with data for the subscenario

    A generic file scanner function for subscenarios, which will scan the
    folder_path and look for CSVs. The file name should start with an
    integer (the subscenario ID), followed by an underscore, and then the
    subscenario name. Subscenario description can be provided in a .txt file
    with the same name as the subscenario CSV file; if such a .txt file does
    not exist, the description of the subscenario is an empty string.

    """

    # Create the dataframes with the subscenario info and data
    subscenario_df = pd.DataFrame(columns=["id", "name", "description"])
    data_df = pd.DataFrame()

    # We'll increment this in the loop below to insert the next subscenario
    # in the csv_subscenario_dataframe
    row_number = 0

    # List all files in directory and look for CSVs
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    # Check that IDs are unique
    check_ids_are_unique(
        folder_path=folder_path, csv_files=csv_files, project_bool=False
    )

    # Get the data for the subscenarios
    for f in csv_files:
        if not quiet:
            print(f)
        # Get the subscenario ID and subscenario name from the file name
        # We're expecting the file name to start with an integer (the
        # subscenario ID), followed by an underscore, and then the
        # subscenario name
        subscenario_id = int(f.split("_", 1)[0])
        subscenario_name = f.split("_", 1)[1].split(".csv")[0]

        # Description of the subscenario can be provided in file with same
        # name as the CSV subscenario file but extension .txt
        subscenario_description = get_subscenario_description(
            folder_path=folder_path, csv_filename=f
        )

        # Insert the subscenario ID, name, and description into the
        # subscenario dataframe
        subscenario_df.loc[row_number] = [
            subscenario_id, subscenario_name, subscenario_description
        ]

        # Insert the subscenario data into the data dataframe
        # Read in the data for the current subscenario from the CSV
        subscenario_data_df = pd.read_csv(os.path.join(folder_path, f))
        # Add the subscenario ID to the dataframe
        subscenario_data_df["id"] = subscenario_id

        # Make the "id" the first column
        cols = subscenario_data_df.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        subscenario_data_df = subscenario_data_df[cols]

        # Append data to the all-scenarios dataframe
        data_df = data_df.append(subscenario_data_df, sort=False)

        # Increment the row for the subscenario_df
        row_number += 1

    return subscenario_df, data_df


def csv_read_project_data(folder_path, quiet):
    """
    :param folder_path: Path to folder with input csv files
    :param quiet: boolean
    :return subscenario_df: Pandas dataframe with subscenario id, name,
        description
    :return data_df: Pandas dataframe with data for the subscenario

    A generic file scanner function for project-level subscenarios (e.g.
    operating characteristics such as heat rates, startup characteristics,
    variable profiles, and hydro characteristics), which will scan the
    folder_path and look for CSVs. The file name should start with the
    project name, followed by a dash, and integer (the subscenario ID), a dash,
    and then the subscenario name. Underscores are allowed in the
    project name but dashes are not -- this needs to be made more
    robust. Subscenario description can be provided in a .txt file with the
    same name as the subscenario CSV file; if such a .txt file does not
    exist, the description of the subscenario is an empty string.

    """

    # Create the dataframes with the subscenario info and data
    subscenario_df = pd.DataFrame(
        columns=["project", "id", "name", "description"]
    )
    data_df = pd.DataFrame()

    # We'll increment this in the loop below to insert the next subscenario
    # in the csv_subscenario_dataframe
    row_number = 0

    # List all files in directory and look for CSVs
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    # Check that IDs are unique
    check_ids_are_unique(
        folder_path=folder_path, csv_files=csv_files, project_bool=True
    )

    # Get the data for the subscenarios
    for f in csv_files:
        if not quiet:
            print(f)
        # Get the subscenario ID and subscenario name from the file name
        # We're expecting the file name to start with the project name,
        # followed by a dash, an integer (the subscenario ID), followed
        # by a dash, and then the subscenario name
        # TODO: need a robust method for splitting the filename in case
        #  the same character as used to delineate (currently a dash)
        #  exists in the project name
        #  Split on dash instead of underscore for now to allow for
        #  underscores in project name
        project = f.split("-", 1)[0]
        subscenario_id = int(f.split("-", 2)[1])
        subscenario_name = f.split("-", 2)[2].split(".csv")[0]

        # Description of the subscenario can be provided in file with same
        # name as the CSV subscenario file but extension .txt
        subscenario_description = get_subscenario_description(
            folder_path=folder_path, csv_filename=f
        )

        # Insert the project name, subscenario ID, subscenario name,
        # and description into the subscenario dataframe
        subscenario_df.loc[row_number] = [
            project, subscenario_id, subscenario_name,
            subscenario_description
        ]

        # Insert the subscenario data into the data dataframe
        # Read in the data for the current subscenario from the CSV
        subscenario_data_df = pd.read_csv(os.path.join(folder_path, f))
        #  Add the subscenario ID to the dataframe
        subscenario_data_df["project"] = project
        subscenario_data_df["id"] = subscenario_id

        # Make the project and id the first two columns
        cols = subscenario_data_df.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        subscenario_data_df = subscenario_data_df[cols]

        # Append dat to the all-scenarios dataframe
        data_df = data_df.append(subscenario_data_df)

        # Increment the row for the subscenario_df
        row_number += 1

    return subscenario_df, data_df


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
    Read data from CSVs, convert to tuples, and insert into database.
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
                csv_read_data(inputs_dir, quiet)
        else:
            (csv_subscenario_input, csv_data_input) = \
                csv_read_project_data(
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


# Functions for subscenarios with multiple files

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


def get_subscenario_description(folder_path, csv_filename):
    """
    :param folder_path:
    :param csv_filename:
    :return:

    Get the description for the subscenario from a .txt file with the same
    name as the CSV file for the subscenario if the .txt file exists.

    """
    # Description of the subscenario can be provided in file with same
    # name as the CSV subscenario file but extension .txt
    description_filename = csv_filename.split(".csv")[0] + ".txt"
    description_file = os.path.join(folder_path, description_filename)
    if os.path.isfile(description_file):
        with open(description_file, "r") as desc_f:
            subscenario_description = desc_f.read()
    else:
        subscenario_description = ""

    return subscenario_description


def check_ids_are_unique(folder_path, csv_files, project_bool):
    """
    :param folder_path: the folder path; just used for the error message
    :param csv_files: a list of the CSV files in the folder
    :param project_bool: boolean; changes behavior depending on whether we're
        checking in csv_read_data or csv_read_project_data, as subscenario
        filename structure is different
    :return:
    """
    all_ids = list()
    for f in csv_files:
        # Get subscenario ID (differs between csv_read_data and
        # csv_read_project_data)
        if project_bool:
            project_bool = f.split("-", 1)[0]
            subscenario_id = int(f.split("-", 2)[1])
            all_ids.append((project_bool, subscenario_id))
        else:
            subscenario_id = int(f.split("_", 1)[0])
            all_ids.append(subscenario_id)

    if len(all_ids) > len(set(all_ids)):
        warnings.warn(
            "You have duplicate {}subscenario IDs in {}.".format(
                "project-" if project_bool else "", folder_path
            )
        )
