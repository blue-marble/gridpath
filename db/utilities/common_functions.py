#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Common functions for data-loading utilities and port script.
"""

import os
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock


# This will be deleted once we've dealt with scenarios and solver options
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


# ### Functions for converting CSVs to lists of tuples ### #

def get_csv_data(csv_file, **kwargs):
    """
    :param csv_file: str, path to CSV file
    :return: list of tuples, list of header strings

    Get the CSV headers and convert the data from a CSV into a list of tuples
    for later insertion into an input table.

    The kwargs determine what values, if any, are added at the beginning of
    each tuple in the list of tuples to import (e.g. subscenario_id, project
    and subscenario_id, etc.) Note that the kwargs must be given in the
    order in which they appear in the database table we'll be inserting into.
    """

    kwd_tuple = tuple()
    for kwd in kwargs.keys():
        kwd_tuple += (kwargs[kwd], )

    df = pd.read_csv(csv_file, delimiter=",")
    tuples_for_import = [
        kwd_tuple + tuple(x)
        for x in df.to_records(index=False)
    ]

    return df.columns.tolist(), tuples_for_import


def csv_to_subscenario_tuples(inputs_dir, csv_file, project_flag):
    """
    :param inputs_dir: string; the directory where the CSV is located
    :param csv_file: string; the name of the CSV file
    :param project_flag: boolean; whether this is a project-level subscenario
    :return: list of tuples (the subscenario info), list of tuples (the
        subscenario data), list of strings (the CSV headers)

    This function reads in a CSV file and converts it into two lists of
    tuples, the one first containing the subscenario ID, name,
    and description and the second one containing the data for the
    subscenario; this also returns the CSV headers as a list for later
    validating that the CSV structure conforms to the database table structure.
    """

    csv_file_path = os.path.join(inputs_dir, csv_file)

    # Description of the subscenario can be provided in file with same
    # name as the CSV subscenario file but extension .txt
    subscenario_description = get_subscenario_description(
        folder_path=inputs_dir, csv_filename=csv_file
    )

    if not project_flag:
        # Get the subscenario ID and subscenario name from the file name
        # We're expecting the file name to start with an integer (the
        # subscenario ID), followed by an underscore, and then the
        # subscenario name
        subscenario_id = int(csv_file.split("_", 1)[0])
        subscenario_name = csv_file.split("_", 1)[1].split(".csv")[0]

        # Insert the subscenario ID, name, and description into the
        # subscenario dataframe
        subsc_tuples = [
            (subscenario_id, subscenario_name, subscenario_description)
        ]

        # Get the CSV headers and create the data tuples
        csv_headers, data_tuples = get_csv_data(
            csv_file=csv_file_path, subscenario_id=subscenario_id
        )

    else:
        # Get the subscenario ID and subscenario name from the file name
        # We're expecting the file name to start with the project name,
        # followed by a dash, an integer (the subscenario ID), followed
        # by a dash, and then the subscenario name
        # TODO: need a robust method for splitting the filename in case
        #  the same character as used to delineate (currently a dash)
        #  exists in the project name
        #  Split on dash instead of underscore for now to allow for
        #  underscores in project name
        project = csv_file.split("-", 1)[0]
        subscenario_id = int(csv_file.split("-", 2)[1])
        subscenario_name = csv_file.split("-", 2)[2].split(".csv")[0]

        # Insert the project name, subscenario ID, subscenario name,
        # and description into the subscenario dataframe
        subsc_tuples = [
            (project, subscenario_id, subscenario_name,
             subscenario_description)
        ]

        # Get the CSV headers and create the data tuples
        # Make sure to give project as keyword argument first, then the
        # subscenario ID, as this is the order in the database tables,
        # so we need to create the correct tuple
        csv_headers, data_tuples = get_csv_data(
            csv_file=csv_file_path,
            project=project, subscenario_id=subscenario_id,
        )

    return subsc_tuples, csv_headers, data_tuples


# ### Functions for loading single-CSV subscenarios ### #
def read_csv_subscenario_and_insert_into_db(
    conn, quiet, subscenario, table, inputs_dir, csv_file, use_project_method
):
    """
    :param conn:
    :param quiet:
    :param subscenario:
    :param table:
    :param inputs_dir:
    :param csv_file:
    :param use_project_method:
    :return:

    Read data from a single subscenario CSV in a directory and insert it
    into the database.
    """
    if not quiet:
        print(csv_file)

    subscenario_tuples, csv_headers, inputs_tuples = \
        csv_to_subscenario_tuples(
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            project_flag=use_project_method
        )

    if use_project_method:
        headers_for_validation = \
            ["project", subscenario] + csv_headers
    else:
        headers_for_validation = \
            [subscenario] + csv_headers

    generic_insert_subscenario(
        conn=conn,
        subscenario=subscenario,
        table=table,
        subscenario_data=subscenario_tuples,
        inputs_data=inputs_tuples,
        project_flag=use_project_method,
        headers_for_validation=headers_for_validation
    )


def read_all_csv_subscenarios_from_dir_and_insert_into_db(
    conn, quiet, subscenario, table, inputs_dir, use_project_method
):
    """
    :param conn:
    :param quiet:
    :param subscenario:
    :param table:
    :param inputs_dir:
    :param use_project_method:
    :return:

    Read data from all subscenario CSVs in a directory and insert them into
    the database.
    """
    # List all files in directory and look for CSVs
    csv_files = [f for f in os.listdir(inputs_dir) if f.endswith(".csv")]

    # If the subscenario is included, make a list of tuples for the subscenario
    # and inputs, and insert into the database via the relevant method
    for csv_file in csv_files:
        read_csv_subscenario_and_insert_into_db(
            conn=conn, quiet=quiet, subscenario=subscenario, table=table,
            inputs_dir=inputs_dir, csv_file=csv_file,
            use_project_method=use_project_method
        )


# ### Functions for loading subscenarios with multiple files ### #

def get_directory_subscenarios(main_directory, quiet):
    """
    :param main_directory:
    :param quiet:
    :return: list of strings

    Read directory subscenarios from a main directory.
    """
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


def read_dir_subscenario_and_insert_into_db(
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
    if not quiet:
        print(subscenario_directory)

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
    csv_headers, inputs_tuple_list = get_csv_data(
        csv_file=filepath, subscenario_id=subscenario_id
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


def read_all_dir_subscenarios_from_dir_and_insert_into_db(
    conn, quiet, inputs_dir, subscenario, table, filename, main_flag
):
    """
    :param conn:
    :param quiet:
    :param inputs_dir:
    :param subscenario:
    :param table:
    :param filename:
    :param main_flag:
    :return:

    Read data from all subscenario directories in a directory and insert them
    into the database.
    """
    subscenario_directories = \
        get_directory_subscenarios(
            main_directory=inputs_dir,
            quiet=quiet
        )

    for subscenario_directory in subscenario_directories:
        read_dir_subscenario_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            subscenario_directory=subscenario_directory,
            filename=filename,
            main_flag=main_flag
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


# ### Generic function for inserting subscenario into the database ### #

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
