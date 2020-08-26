#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Common functions for data-loading utilities and port script.
"""

import math
import os
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock
import db.utilities.custom_functions as custom


# ### Functions for converting CSVs to lists of tuples for DB insertion ### #

def get_subscenario_info(
    dir_subsc, inputs_dir, csv_file, project_flag
):
    """
    :param dir_subsc: boolean; whether this is a directory-based
        subscenario; changes whether we use the inputs_dir or csv_file to
        determine the scenario info
    :param inputs_dir: string; the directory in which the CSV is located;
        this is the subscenario directory for directory-based subscenarios,
        which we use to determine the scenario info; if we're looking at a
        CSV-based scenario, we need the directory to find the subscenario
        description file
    :param csv_file: string; the name of the CSV file, which we'll use to
        determine the scenario info if this is a CSV-based subscenario
    :param project_flag: boolean; whether the CSV file contains project
        level data
    :return: tuple; (subscenario_id, subscenario_name,
        subscenario_description)

    This function determines the subscenario info and returns it as a tuple.

    If this is a directory-based scenario, description of the subscenario
    can be optionally provided in a file named description.txt in the
    subscenario directory (inputs_dir); if this is a CSV-based subscenario,
    description of the subscenario can be optionally provided in file with
    same name as the CSV subscenario file but with the extension .txt.

    If this is a directory-based scenario, we use the directory name and if
    this is a CSV-based subscenario, we use the file name to determine the
    subscenario ID and subscenario name. We're expecting this "base name" to
    start with an integer (the subscenario ID), followed by an underscore,
    and then the subscenario name.

    For project-level subscenarios, we're expecting the file name to start
    with the project name, followed by a dash, an integer (the subscenario
    ID), followed by a dash, and then the subscenario name

    """
    # Get the subscenario description
    if dir_subsc:
        # The get_subscenario_description function expects a .txt file with
        # the same name as the .csv filename passed, so pass description.csv
        # to get the contents of the description.txt file
        subscenario_description = get_subscenario_description(
            input_dir=inputs_dir, csv_filename="description.csv"
        )
    else:
        subscenario_description = get_subscenario_description(
            input_dir=inputs_dir, csv_filename=csv_file
        )

    # Get the subscenario ID and name
    if not project_flag:
        if dir_subsc:
            basename = os.path.basename(inputs_dir)
        else:
            basename = csv_file

        subscenario_id = int(basename.split("_", 1)[0])
        subscenario_name = basename.split("_", 1)[1].split(".csv")[0]

        subsc_tuples = [
            (subscenario_id, subscenario_name, subscenario_description)
        ]
    else:
        project = csv_file.split("-", 1)[0]
        subscenario_id = int(csv_file.split("-", 2)[1])
        subscenario_name = csv_file.split("-", 2)[2].split(".csv")[0]

        subsc_tuples = [
            (project, subscenario_id, subscenario_name,
             subscenario_description)
        ]

    return subsc_tuples


def get_subscenario_data(csv_file, cols_to_exclude_str, **kwargs):
    """
    :param csv_file: str, path to CSV file
    :param cols_to_exclude_str:
    :return: list of header strings, list of tuples

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

    # Read the CSV
    df = pd.read_csv(csv_file, delimiter=",")
    csv_columns = df.columns.tolist()

    # Exclude some columns if directed to do so
    if cols_to_exclude_str == "nan":
        pass
    else:
        cols_to_exclude = [
            i for i in csv_columns if i.startswith(cols_to_exclude_str)
        ]
        for c in cols_to_exclude:
            csv_columns.remove(c)

    # Make the dataframe with the correct columns
    df = df[csv_columns]

    # Convert to tuples
    tuples_for_import = [
        kwd_tuple + tuple(x)
        for x in df.to_records(index=False)
    ]

    return csv_columns, tuples_for_import


def csv_to_subscenario_for_insertion(
    dir_subsc, inputs_dir, csv_file, project_flag, cols_to_exclude_str
):
    """
    :param dir_subsc: boolean;
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

    # Get the subscenario info
    subsc_tuples = get_subscenario_info(
        dir_subsc, inputs_dir, csv_file, project_flag
    )

    # Get the data from the CSV if a CSV file name is passed (if not,
    # we're expecting the object to not be a string and to be 'nan')
    if not isinstance(csv_file, str) and math.isnan(csv_file):
        csv_headers = None
        data_tuples = None
    else:
        # Get the CSV headers (for later validation) and subscenario data
        csv_file_path = os.path.join(inputs_dir, csv_file)

        if not project_flag:
            # We only need the subscenario ID as keyword argument to
            # get_subscenario_data()
            subscenario_id = subsc_tuples[0][0]
            csv_headers, data_tuples = \
                get_subscenario_data(
                    csv_file=csv_file_path,
                    cols_to_exclude_str=cols_to_exclude_str,
                    subscenario_id=subscenario_id
                )
        else:
            # We need the project and subscenario ID as keyword arguments to
            # get_subscenario_data()
            project = subsc_tuples[0][0]
            subscenario_id = subsc_tuples[0][1]
            # Make sure to give project as keyword argument first, then the
            # subscenario ID, as this is the order in the database tables,
            # so we need to create the correct tuple
            csv_headers, data_tuples = \
                get_subscenario_data(
                    csv_file=csv_file_path,
                    cols_to_exclude_str=cols_to_exclude_str,
                    project=project, subscenario_id=subscenario_id,
                )

    return subsc_tuples, csv_headers, data_tuples


def get_subscenario_description(input_dir, csv_filename):
    """
    :param input_dir: string
    :param csv_filename: string
    :return: string

    Get the description for the subscenario from a .txt file with the same
    name as the CSV file for the subscenario if the .txt file exists.

    """
    # Description of the subscenario can be provided in file with same
    # name as the CSV filename passed but extension .txt
    description_filename = csv_filename.split(".csv")[0] + ".txt"
    description_file = os.path.join(input_dir, description_filename)
    if os.path.isfile(description_file):
        with open(description_file, "r") as desc_f:
            subscenario_description = desc_f.read()
    else:
        subscenario_description = ""

    return subscenario_description


def get_subscenario_data_and_insert_into_db(
    conn, quiet, subscenario, table, dir_subsc, inputs_dir, csv_file,
    use_project_method, skip_subscenario_info, skip_subscenario_data,
    cols_to_exclude_str, custom_method, delete_flag
):
    """
    :param conn: database connection object
    :param quiet: boolean
    :param subscenario: string
    :param table: string
    :param dir_subsc: boolean
    :param inputs_dir: string
    :param csv_file: string
    :param use_project_method: boolean
    :param skip_subscenario_info: boolean
    :param skip_subscenario_data: boolean
    :param cols_to_exclude_str: boolean
    :param custom_method: string

    Read the data for a subscenario, convert it to tuples, and insert into the
    database.
    """
    if not quiet:
        print("   ...importing data from {}".format(csv_file))

    subscenario_tuples, csv_headers, inputs_tuples = \
        csv_to_subscenario_for_insertion(
            dir_subsc=dir_subsc,
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            project_flag=use_project_method,
            cols_to_exclude_str=cols_to_exclude_str
        )

    if delete_flag:
        generic_delete_subscenario(
            conn=conn, subscenario=subscenario, table=table,
            subscenario_data=subscenario_tuples,
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
        skip_subscenario_info=skip_subscenario_info,
        skip_subscenario_data=skip_subscenario_data,
        delete_flag=delete_flag
    )

    # If a custom method is requsted, run it here to finalize the subscenario
    if custom_method != "nan":
        getattr(custom, custom_method)(
            conn=conn,
            subscenario_id=subscenario_tuples[0][0]
        )


# ### Functions for loading single-CSV subscenarios ### #

def read_all_csv_subscenarios_from_dir_and_insert_into_db(
    conn, quiet, subscenario, table, inputs_dir, use_project_method,
    cols_to_exclude_str, custom_method, delete_flag
):
    """
    :param conn: database connection object
    :param quiet: boolean
    :param subscenario: string
    :param table: string
    :param inputs_dir: string
    :param use_project_method: boolean
    :param cols_to_exclude_str: string
    :param custom_method: string

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
        print("...importing CSV {}".format(csv_file))
        get_subscenario_data_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=False,
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            use_project_method=use_project_method,
            skip_subscenario_info=False,
            skip_subscenario_data=False,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
            delete_flag=delete_flag
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
    conn, quiet, inputs_dir, subscenario, table, filename,
    skip_subscenario_info, skip_subscenario_data, cols_to_exclude_str,
    custom_method, delete_flag
):
    """
    :param conn: database connection object
    :param quiet: boolean
    :param inputs_dir: string
    :param subscenario: string
    :param table: string
    :param filename: string
    :param skip_subscenario_info: boolean
    :param skip_subscenario_data: boolean
    :param cols_to_exclude_str: string
    :param custom_method: function

    Read data from all subscenario directories in a directory and insert them
    into the database.
    """
    subscenario_directories = \
        get_directory_subscenarios(
            main_directory=inputs_dir,
            quiet=quiet
        )

    for subscenario_directory in subscenario_directories:
        print("...importing data from directory {}".format(
            subscenario_directory))
        get_subscenario_data_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=True,
            inputs_dir=subscenario_directory,
            csv_file=filename,
            use_project_method=False,
            skip_subscenario_info=skip_subscenario_info,
            skip_subscenario_data=skip_subscenario_data,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
            delete_flag=delete_flag
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
    skip_subscenario_info, skip_subscenario_data, delete_flag, csv_headers=None
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param subscenario_data: list of tuples
    :param inputs_data: list of tuples
    :param project_flag: boolean
    :param skip_subscenario_info: boolean
    :param skip_subscenario_data: boolean
    :param csv_headers: list of strings

    Generic function that loads subscenario info and inputs data for a
    particular subscenario. The subscenario_data and inputs_data
    are given as lists of tuples. If csv_headers are passed, this function
    also validates that they match the columns of the table into which we're
    inserting.
    """

    # Load in the subscenario name and description
    if not skip_subscenario_info:
        generic_insert_subscenario_info(
            conn, subscenario, table, subscenario_data, project_flag,
            delete_flag
        )

    # Insert the subscenario data
    if not skip_subscenario_data:
        generic_insert_subscenario_data(
            conn, subscenario, table, inputs_data, project_flag,
            delete_flag, csv_headers
        )


def generic_delete_subscenario(
    conn, subscenario, table, subscenario_data, project_flag
):
    c = conn.cursor()

    print(subscenario_data)

    if not project_flag:
        del_sql = """
            DELETE FROM inputs_{}
            WHERE {} = ?;
            """.format(table, subscenario)
    else:
        del_sql = """
            DELETE FROM inputs_{}
            WHERE project = ?
            AND {} = ?;
            """.format(table, subscenario)

    spin_on_database_lock(conn=conn, cursor=c, sql=del_sql,
                          data=subscenario_data[0], many=False)

    if not project_flag:
        del_sql = """
            DELETE FROM subscenarios_{}
            WHERE {} = ?;
            """.format(table, subscenario)
    else:
        del_sql = """
            DELETE FROM subscenarios_{}
            WHERE project = ?
            AND {} = ?;
            """.format(table, subscenario)

    spin_on_database_lock(conn=conn, cursor=c, sql=del_sql,
                          data=[subscenario_data], many=False)


def generic_insert_subscenario_info(
    conn, subscenario, table, subscenario_data, project_flag, delete_flag
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param subscenario_data: list of tuples
    :param project_flag: boolean

    Generic function that loads subscenario info for a
    particular subscenario. The subscenario_data are given as lists of
    tuples.
    """
    c = conn.cursor()

    # Load in the subscenario name and description
    if not project_flag:
        subs_sql = """
            INSERT INTO subscenarios_{}
            ({}, name, description)
            VALUES (?, ?, ?);
            """.format(table, subscenario)
    else:
        subs_sql = """
            INSERT INTO subscenarios_{}
            (project, {}, name, description)
            VALUES (?, ?, ?, ?);
            """.format(table, subscenario)

    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    c.close()


def generic_insert_subscenario_data(
    conn, subscenario, table, inputs_data, project_flag,
    delete_flag, csv_headers=None,
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param inputs_data: list of tuples
    :param project_flag: boolean
    :param csv_headers: list of strings

    Generic function that loads subscenario info and inputs data for a
    particular subscenario. The subscenario_data and inputs_data
    are given as lists of tuples. If csv_headers are passed, this function
    also validates that they match the columns of the table into which we're
    inserting.
    """
    c = conn.cursor()
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
        INSERT INTO inputs_{} ({}) VALUES ({});
        """.format(table, column_string, values_string)

    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def load_all_subscenario_ids_from_dir_to_subscenario_table(
    conn, subscenario, table, subscenario_type, project_flag,
    cols_to_exclude_str, custom_method, inputs_dir, filename, delete_flag,
    quiet
):
    """
    :param conn: the database connection
    :param subscenario: str; the subscenario (e.g. 'temporal_scenario_id')
    :param table: str; the subscenario table name
    :param subscenario_type: str; determines which CSV-to-DB functions to use
    :param project_flag: boolean
    :param cols_to_exclude_str:
    :param custom_method: str
    :param inputs_dir: str
    :param filename: str
    :param quiet: boolean
    :return:

    Load all data for a subscenario (i.e. all subscenario IDs) from a
    directory.
    """
    if subscenario_type == "simple":
        read_all_csv_subscenarios_from_dir_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            inputs_dir=inputs_dir,
            use_project_method=project_flag,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
            delete_flag=delete_flag
        )
    elif subscenario_type in [
        "dir_subsc_only", "dir_main", "dir_aux"
    ]:
        skip_subscenario_info, skip_subscenario_data = \
            determine_whether_to_skip_subscenario_info_and_or_data(
                subscenario_type=subscenario_type
            )
        read_all_dir_subscenarios_from_dir_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            inputs_dir=inputs_dir,
            subscenario=subscenario,
            table=table,
            filename=filename,
            skip_subscenario_info=skip_subscenario_info,
            skip_subscenario_data=skip_subscenario_data,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
            delete_flag=delete_flag
        )
    else:
        pass


def load_single_subscenario_id_from_dir_to_subscenario_table(
    conn, subscenario, table, subscenario_type, project_flag,
    cols_to_exclude_str, custom_method, inputs_dir, filename, quiet,
    subscenario_id_to_load, delete_flag
):
    """
    :param conn: the database connection
    :param subscenario: str; the subscenario (e.g. 'temporal_scenario_id')
    :param table: str; the subscenario table name
    :param subscenario_type: str; determines which CSV-to-DB functions to use
    :param project_flag: boolean
    :param cols_to_exclude_str:
    :param custom_method: str
    :param inputs_dir: str
    :param filename: str
    :param quiet: boolean
    :param subscenario_id_to_load: integer; the subscenario ID to load
    :param delete_flag: boolean; whether to delete prior data for the
        subscenario ID
    :return:

    Load data for a particular subscenario ID from a directory.
    """
    print("Here")
    if subscenario_type == "simple":
        csv_files = [
            f for f in os.listdir(inputs_dir)
            if f.startswith(str(subscenario_id_to_load))
            and f[len(str(subscenario_id_to_load))] == "_"
            and f.endswith(".csv")
        ]
        print(csv_files)
        if len(csv_files) == 1:
            csv_file = csv_files[0]
        else:
            raise ValueError("Only one CSV file may have ID {}".format(
                subscenario_id_to_load))

        get_subscenario_data_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=False,
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            use_project_method=project_flag,
            skip_subscenario_info=False,
            skip_subscenario_data=False,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
            delete_flag=delete_flag
        )

    elif subscenario_type in [
        "dir_subsc_only", "dir_main", "dir_aux"
    ]:
        subscenario_directories = [
            d for d in sorted(next(os.walk(inputs_dir))[1])
            if d.startswith(str(subscenario_id_to_load))
        ]
        if len(subscenario_directories) == 1:
            subscenario_directory = subscenario_directories[0]
        else:
            raise ValueError("Only one CSV file must have ID ".format(
                subscenario_id_to_load))

        skip_subscenario_info, skip_subscenario_data = \
            determine_whether_to_skip_subscenario_info_and_or_data(
                subscenario_type=subscenario_type
            )

        get_subscenario_data_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=True,
            inputs_dir=os.path.join(inputs_dir, subscenario_directory),
            csv_file=filename,
            use_project_method=False,
            skip_subscenario_info=skip_subscenario_info,
            skip_subscenario_data=skip_subscenario_data,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
            delete_flag=delete_flag
        )
    else:
        pass


def determine_whether_to_skip_subscenario_info_and_or_data(subscenario_type):
    """
    :param subscenario_type:
    :return:
    """
    if subscenario_type == "dir_subsc_only":
        skip_subscenario_info = False
        skip_subscenario_data = True
    elif subscenario_type == "dir_aux":
        skip_subscenario_info = True
        skip_subscenario_data = False
    else:
        skip_subscenario_info = False
        skip_subscenario_data = False

    return skip_subscenario_info, skip_subscenario_data
