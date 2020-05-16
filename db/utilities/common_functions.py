#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Common functions for data-loading utilities and port script.
"""

import os
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock


def get_inputs_dir(csvs_main_dir, csv_data_master, subscenario):
    """
    :param csvs_main_dir:
    :param csv_data_master:
    :param subscenario:
    :return:

    Get the inputs directory listed in the CSV master file for a particular
    subscenario (for now, "table").
    """
    if csv_data_master.loc[
        csv_data_master["subscenario"] == subscenario, 'include'
    ].iloc[0] == 1:
        inputs_dir = os.path.join(
            csvs_main_dir,
            csv_data_master.loc[
                csv_data_master["subscenario"] == subscenario,
                "path"
            ].iloc[0]
        )
    else:
        inputs_dir = None

    return inputs_dir


def read_inputs(
    inputs_dir, quiet, use_project_method=False
):
    """
    :param inputs_dir:
    :param quiet:
    :param use_project_method:
    :return:

    Read the subscenario info and inputs data from the specified directory.
    """
    if not use_project_method:
        (csv_subscenario_input, csv_data_input) = \
            csv_read_data(folder_path=inputs_dir, quiet=quiet)
    else:
        (csv_subscenario_input, csv_data_input) = \
            csv_read_project_data(folder_path=inputs_dir, quiet=quiet)

    return csv_subscenario_input, csv_data_input


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
    :return: list of tuples, list of header strings

    Convert the data from a CSV into a list of tuples for insertion into an
    input table.
    """
    df = pd.read_csv(csv_file, delimiter=",")
    tuples_for_import = [
        (subscenario_id,) + tuple(x)
        for x in df.to_records(index=False)
    ]

    return tuples_for_import, df.columns.tolist()


def read_simple_csvs_and_insert_into_db(
    conn, quiet, subscenario, table, inputs_dir, use_project_method,
):
    """
    Read data from CSVs, convert to tuples, and insert into database.
    """
    # Get the subscenario info and data
    csv_subscenario_input, csv_data_input = read_inputs(
        inputs_dir=inputs_dir,
        quiet=quiet,
        use_project_method=use_project_method
    )

    csv_headers_for_validation = [
        subscenario if x == "id" else x
        for x in csv_data_input.columns.tolist()
    ]

    # If the subscenario is included, make a list of tuples for the subscenario
    # and inputs, and insert into the database via the relevant method
    if csv_subscenario_input is not False and csv_data_input is not False:
        subscenario_tuples = [
            tuple(x) for x in csv_subscenario_input.to_records(index=False)
        ]
        inputs_tuples = [
            tuple(x) for x in csv_data_input.to_records(index=False)
         ]

        generic_insert_subscenario(
            conn=conn,
            subscenario=subscenario,
            table=table,
            subscenario_data=subscenario_tuples,
            inputs_data=inputs_tuples,
            project_flag=use_project_method,
            headers_for_validation=csv_headers_for_validation
        )


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


def read_dir_data_and_insert_into_db(
    conn, quiet, subscenario, table, subscenario_directory, filename, main_flag
):
    """
    :param conn:
    :param quiet:
    :param subscenario:
    :param table:
    :param subscenario_directory:
    :param filename:
    :param main_flag:

    Read subscenario info from a directory, with the subscenario ID,
    underscore, and the subscenario name as the name of the directory.

    A file containing the subscenario description (description.txt) is
    optional. Each directory also contains CSV files with expected structure
    based on the table they are loaded into. This function loads the 'main'
    csv file into the input table that matches with subscenario table. See
    also the read_dir_aux_data_and_insert_into_db() for loading of auxiliary
    data for this subscenario.
    """
    # Get the paths for the required input files
    filepath = os.path.join(subscenario_directory, filename)

    # Get subscenario ID, name, and description
    # The subscenario directory must start with an integer for the
    # subscenario_id followed by "_" and then the subscenario name
    # The subscenario description must be in the description.txt file under
    # the subscenario directory
    directory_basename = os.path.basename(subscenario_directory)
    subscenario_id = int(directory_basename.split("_", 1)[0])
    subscenario_name = directory_basename.split("_", 1)[1]

    # If we're loading the 'main_dir' files, also load in the subscenario info
    if main_flag:
        # Check if there's a description file, otherwise the description will be
        # an empty string
        description_file = os.path.join(subscenario_directory, "description.txt")
        if os.path.exists(description_file):
            with open(description_file, "r") as f:
                subscenario_description = f.read()
        else:
            subscenario_description = ""

        # Make the tuple for insertion into the subscenario table
        subscenario_tuple_list = [
            (subscenario_id, subscenario_name, subscenario_description)
        ]
    else:
        subscenario_tuple_list = None

    # Inputs
    inputs_tuple_list, csv_headers = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=filepath
    )
    headers_for_validation = [subscenario] + csv_headers

    generic_insert_subscenario(
        conn=conn,
        subscenario=subscenario,
        table=table,
        subscenario_data=subscenario_tuple_list,
        inputs_data=inputs_tuple_list,
        project_flag=False,
        main_flag=main_flag,
        headers_for_validation=headers_for_validation
    )


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


def generic_insert_subscenario(
    conn, subscenario, table, subscenario_data, inputs_data, project_flag,
    main_flag=True, headers_for_validation=None
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param subscenario_data: list of tuples
    :param inputs_data: list of tuples
    :param project_flag: boolean
    :param main_flag: boolean; True by default; when loading inputs from a
        directory, we pass True when we want to load the subscenario info
        with the 'main' inputs and False if we're loading auxiliary inputs only
    :param headers_for_validation: list of strings

    Generic function that loads subscenario info and inputs data for a
    particular subscenario. The subscenario_data and inputs_data are given
    as lists of tuples.
    """
    c = conn.cursor()

    # Load in the subscenario name and description
    if main_flag:
        if not project_flag:
            subs_sql = """
                INSERT OR IGNORE INTO subscenarios_{}
                ({}, name, description)
                VALUES (?, ?, ?);
                """.format(table, subscenario)
        else:
            subs_sql = """
                INSERT OR IGNORE INTO subscenarios_{}
                (project, {}, name, description)
                VALUES (?, ?, ?, ?);
                """.format(table, subscenario)

        spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                              data=subscenario_data)

    # Insert the subscenario data
    # Get column names for this table
    table_data_query = c.execute(
      """SELECT * FROM inputs_{};""".format(table)
    )

    # If we have passed headers, check that they are as expected (i.e.
    # the same as in the table we're inserting into)
    column_names = [s[0] for s in table_data_query.description]
    if headers_for_validation is not None:
        if headers_for_validation != column_names:
            raise AssertionError(
                """
                Headers and table column names don't match.
                Column names are {}.
                Header names are {}.
                Please ensure that your header names are the same as the 
                database column names.
                """.format(column_names, headers_for_validation)
            )


    # Create the appropriate strings needed for the insert query
    column_string = ", ".join(column_names)
    values_string = ", ".join(["?"] * len(column_names))

    inputs_sql = """
        INSERT OR IGNORE INTO inputs_{} ({}) VALUES ({});
        """.format(table, column_string, values_string)

    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
