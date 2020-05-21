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


# ### Functions for converting CSVs to lists of tuples for DB insertion ### #

def get_subscenario_description_as_tuple(
    dir_subsc, inputs_dir, csv_file, project_flag
):
    # Description of the subscenario can be provided in file with same
    # name as the CSV subscenario file but extension .txt
    # Check if there's a description file, otherwise the description will
    # be an empty string
    if not dir_subsc:
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
    else:
        # Make the tuple for insertion into the subscenario table
        # The get_subscenario_description function expects a .txt file with
        # the same name as the .csv filename passed, so pass description.csv
        # to get the description.txt file
        subscenario_description = get_subscenario_description(
            folder_path=inputs_dir, csv_filename="description.csv"
        )
        # Get subscenario ID, name, and description
        # The subscenario directory must start with an integer for the
        # subscenario_id followed by "_" and then the subscenario name
        # The subscenario description must be in the description.txt file under
        # the subscenario directory
        directory_basename = os.path.basename(inputs_dir)
        subscenario_id = int(directory_basename.split("_", 1)[0])
        subscenario_name = directory_basename.split("_", 1)[1]

        subsc_tuples = [
            (subscenario_id, subscenario_name, subscenario_description)
        ]

    return subsc_tuples


def get_headers_and_subscenario_data_tuples_from_csv(csv_file, **kwargs):
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


def csv_to_subscenario_tuples(
    dir_subsc, inputs_dir, csv_file, project_flag
):
    """
    :param inputs_dir: string; the directory where the CSV is located
    :param csv_file: string; the name of the CSV file
    :param project_flag: boolean; whether this is a project-level subscenario
    :return: list of tuples (the subscenario info), list of tuples (the
        subscenario data), list of strings (the CSV headers)

    This function reads in a CSV file and converts it into two lists of
    tuples, the first one containing the subscenario ID, name,
    and description and the second one containing the data for the
    subscenario; this also returns the CSV headers as a list for later
    validating that the CSV structure conforms to the database table structure.
    """

    csv_file_path = os.path.join(inputs_dir, csv_file)

    subsc_tuples = get_subscenario_description_as_tuple(
        dir_subsc, inputs_dir, csv_file, project_flag
    )

    if not project_flag:
        subscenario_id = subsc_tuples[0][0]
        # Get the CSV headers and create the data tuples
        csv_headers, data_tuples = \
            get_headers_and_subscenario_data_tuples_from_csv(
                csv_file=csv_file_path, subscenario_id=subscenario_id
            )
    else:
        project = subsc_tuples[0][0]
        subscenario_id = subsc_tuples[0][1]

        # Get the CSV headers and create the data tuples
        # Make sure to give project as keyword argument first, then the
        # subscenario ID, as this is the order in the database tables,
        # so we need to create the correct tuple
        csv_headers, data_tuples = \
            get_headers_and_subscenario_data_tuples_from_csv(
                csv_file=csv_file_path,
                project=project, subscenario_id=subscenario_id,
            )

    return subsc_tuples, csv_headers, data_tuples


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


def read_csv_subscenario_and_insert_into_db(
    conn, quiet, subscenario, table, dir_subsc, inputs_dir, csv_file,
    use_project_method, skip_subscenario_info
):
    """
    :param conn:
    :param quiet:
    :param subscenario:
    :param table:
    :param inputs_dir:
    :param csv_file:
    :param use_project_method:
    :param skip_subscenario_info:
    :return:

    Read data from a single subscenario CSV in a directory and insert it
    into the database.
    """
    if not quiet:
        print(csv_file)

    subscenario_tuples, csv_headers, inputs_tuples = \
        csv_to_subscenario_tuples(
            dir_subsc=dir_subsc,
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            project_flag=use_project_method
        )

    generic_insert_subscenario(
        conn=conn,
        subscenario=subscenario,
        table=table,
        subscenario_data=subscenario_tuples,
        inputs_data=inputs_tuples,
        project_flag=use_project_method,
        csv_headers=csv_headers,
        skip_subscenario_info=skip_subscenario_info
    )


# ### Functions for loading single-CSV subscenarios ### #

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

    # Check that the subscenario IDs based on the file names are unique
    check_ids_are_unique(inputs_dir=inputs_dir, csv_files=csv_files,
                         use_project_method=use_project_method)

    # If the subscenario is included, make a list of tuples for the subscenario
    # and inputs, and insert into the database via the relevant method
    for csv_file in csv_files:
        read_csv_subscenario_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=False,
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            use_project_method=use_project_method,
            skip_subscenario_info=True
        )


def check_ids_are_unique(inputs_dir, csv_files, use_project_method):
    """
    :param inputs_dir: the folder path; just used for the error message
    :param csv_files: a list of the CSV files in the folder
    :param use_project_method: boolean; changes behavior depending on whether we're
        checking in csv_read_data or csv_read_project_data, as subscenario
        filename structure is different
    :return:
    """
    all_ids = list()
    for f in csv_files:
        # Get subscenario ID (differs between csv_read_data and
        # csv_read_project_data)
        if use_project_method:
            use_project_method = f.split("-", 1)[0]
            subscenario_id = int(f.split("-", 2)[1])
            all_ids.append((use_project_method, subscenario_id))
        else:
            subscenario_id = int(f.split("_", 1)[0])
            all_ids.append(subscenario_id)

    if len(all_ids) > len(set(all_ids)):
        warnings.warn(
            "You have duplicate {}subscenario IDs in {}.".format(
                "project-" if use_project_method else "", inputs_dir
            )
        )


# ### Functions for loading subscenarios with multiple files ### #


def read_all_dir_subscenarios_from_dir_and_insert_into_db(
    conn, quiet, inputs_dir, subscenario, table, filename, skip_subscenario_info
):
    """
    :param conn:
    :param quiet:
    :param inputs_dir:
    :param subscenario:
    :param table:
    :param filename:
    :param skip_subscenario_info:
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
        read_csv_subscenario_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=True,
            inputs_dir=subscenario_directory,
            csv_file=filename,
            use_project_method=False,
            skip_subscenario_info=skip_subscenario_info
        )


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


# ### Generic function for inserting subscenario into the database ### #

def generic_insert_subscenario(
    conn, subscenario, table, subscenario_data, inputs_data, project_flag,
    skip_subscenario_info, csv_headers=None,
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param subscenario_data: list of tuples
    :param inputs_data: list of tuples
    :param project_flag: boolean
    :param csv_headers: list of strings

    Generic function that loads subscenario info and inputs data for a
    particular subscenario. The subscenario_data and inputs_data are given
    as lists of tuples.
    """
    c = conn.cursor()

    # Load in the subscenario name and description
    if not skip_subscenario_info:
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

    if csv_headers is not None:
        if project_flag:
            headers_for_validation = \
                ["project", subscenario] + csv_headers
        else:
            headers_for_validation = \
                [subscenario] + csv_headers
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
