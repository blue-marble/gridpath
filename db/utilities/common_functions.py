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

"""
Common functions for data-loading utilities and port script.
"""

import math
import os
import pandas as pd
import sys
import warnings

from db.common_functions import spin_on_database_lock
import db.utilities.custom_functions as custom


# ### Functions for converting CSVs to lists of tuples for DB insertion ### #


def get_subscenario_info(dir_subsc, inputs_dir, csv_file, project_flag):
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

        subsc_tuples = [(subscenario_id, subscenario_name, subscenario_description)]
    else:
        project = csv_file.split("-", 1)[0]
        subscenario_id = int(csv_file.split("-", 2)[1])
        subscenario_name = csv_file.split("-", 2)[2].split(".csv")[0]

        subsc_tuples = [
            (project, subscenario_id, subscenario_name, subscenario_description)
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
        kwd_tuple += (kwargs[kwd],)

    # Read the CSV
    df = pd.read_csv(csv_file, delimiter=",")
    csv_columns = df.columns.tolist()

    # Exclude some columns if directed to do so
    if cols_to_exclude_str != "nan":
        cols_to_exclude = [i for i in csv_columns if i.startswith(cols_to_exclude_str)]
        for c in cols_to_exclude:
            csv_columns.remove(c)

    # Make the dataframe with the correct columns
    df = df[csv_columns]

    # Convert to tuples
    tuples_for_import = [kwd_tuple + tuple(x) for x in df.to_records(index=False)]

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
    subsc_tuples = get_subscenario_info(dir_subsc, inputs_dir, csv_file, project_flag)

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
            csv_headers, data_tuples = get_subscenario_data(
                csv_file=csv_file_path,
                cols_to_exclude_str=cols_to_exclude_str,
                subscenario_id=subscenario_id,
            )
        else:
            # We need the project and subscenario ID as keyword arguments to
            # get_subscenario_data()
            project = subsc_tuples[0][0]
            subscenario_id = subsc_tuples[0][1]
            # Make sure to give project as keyword argument first, then the
            # subscenario ID, as this is the order in the database tables,
            # so we need to create the correct tuple
            csv_headers, data_tuples = get_subscenario_data(
                csv_file=csv_file_path,
                cols_to_exclude_str=cols_to_exclude_str,
                project=project,
                subscenario_id=subscenario_id,
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
    conn,
    quiet,
    subscenario,
    table,
    dir_subsc,
    inputs_dir,
    csv_file,
    use_project_method,
    project_is_tx,
    skip_subscenario_info,
    skip_subscenario_data,
    cols_to_exclude_str,
    custom_method,
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

    subscenario_tuples, csv_headers, inputs_tuples = csv_to_subscenario_for_insertion(
        dir_subsc=dir_subsc,
        inputs_dir=inputs_dir,
        csv_file=csv_file,
        project_flag=use_project_method,
        cols_to_exclude_str=cols_to_exclude_str,
    )

    generic_insert_subscenario(
        conn=conn,
        subscenario=subscenario,
        table=table,
        subscenario_data=subscenario_tuples,
        inputs_data=inputs_tuples,
        project_flag=use_project_method,
        project_is_tx=project_is_tx,
        csv_headers=csv_headers,
        skip_subscenario_info=skip_subscenario_info,
        skip_subscenario_data=skip_subscenario_data,
    )

    # If a custom method is requsted, run it here to finalize the subscenario
    if custom_method != "nan":
        getattr(custom, custom_method)(
            conn=conn, subscenario_id=subscenario_tuples[0][0]
        )


# ### Functions for loading single-CSV subscenarios ### #


def read_all_csv_subscenarios_from_dir_and_insert_into_db(
    conn,
    quiet,
    subscenario,
    table,
    inputs_dir,
    use_project_method,
    project_is_tx,
    cols_to_exclude_str,
    custom_method,
):
    """
    :param conn: database connection object
    :param quiet: boolean
    :param subscenario: string
    :param table: string
    :param inputs_dir: string
    :param use_project_method: boolean
    :param project_is_tx: boolean
    :param cols_to_exclude_str: string
    :param custom_method: string

    Read data from all subscenario CSVs in a directory and insert them into
    the database.
    """
    # List all files in directory and look for CSVs
    csv_files = [f for f in os.listdir(inputs_dir) if f.endswith(".csv")]

    # Check that the subscenario IDs based on the file names are unique
    check_ids_are_unique(
        inputs_dir=inputs_dir,
        csv_files=csv_files,
        use_project_method=use_project_method,
    )

    # If the subscenario is included, make a list of tuples for the subscenario
    # and inputs, and insert into the database via the relevant method
    for csv_file in csv_files:
        if not quiet:
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
            project_is_tx=project_is_tx,
            skip_subscenario_info=False,
            skip_subscenario_data=False,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
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
    conn,
    quiet,
    inputs_dir,
    subscenario,
    table,
    filename,
    skip_subscenario_info,
    skip_subscenario_data,
    cols_to_exclude_str,
    custom_method,
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
    subscenario_directories = get_directory_subscenarios(
        main_directory=inputs_dir, quiet=quiet
    )

    for subscenario_directory in subscenario_directories:
        if not quiet:
            print("...importing data from directory {}".format(subscenario_directory))
        get_subscenario_data_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=True,
            inputs_dir=subscenario_directory,
            csv_file=filename,
            use_project_method=False,
            project_is_tx=False,
            skip_subscenario_info=skip_subscenario_info,
            skip_subscenario_data=skip_subscenario_data,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
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
        # Ignore "__pycache__" directory, which can be created when using
        # local doc.py file
        if subscenario == "__pycache__":
            subscenario_dir_names.remove(subscenario)
        elif not subscenario.split("_")[0].isdigit():
            warnings.warn(
                "Subfolder `{}` does not start with an integer to "
                "indicate the subscenario ID and will not be imported. "
                "Please follow the required folder naming structure "
                "<subscenarioID_subscenarioName>, e.g. "
                "'1_default4periods'.".format(subscenario)
            )
        else:
            # Get the full path of the subscenario directory and append to the
            # directory list
            subscenario_directory = os.path.join(main_directory, subscenario)
            subscenario_directories.append(subscenario_directory)

    return subscenario_directories


# ### Generic function for inserting subscenario into the database ### #


def generic_insert_subscenario(
    conn,
    subscenario,
    table,
    subscenario_data,
    inputs_data,
    project_flag,
    project_is_tx,
    skip_subscenario_info,
    skip_subscenario_data,
    csv_headers=None,
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
            conn, subscenario, table, subscenario_data, project_flag, project_is_tx
        )

    # Insert the subscenario data
    if not skip_subscenario_data:
        generic_insert_subscenario_data(
            conn,
            subscenario,
            table,
            inputs_data,
            project_flag,
            project_is_tx,
            csv_headers,
        )


def determine_tables_to_delete_from(csv_structure, subscenario):
    """
    :param csv_structure: Pandas DataFrame
    :param subscenario: str;
    :return: subscenario_table, input_tables, project_flag, project_is_tx,
        base_table, base_subscenario

    Determine the relevant tables from which to delete prior data.
    """
    # Get the sub-dataframe for this subscenario from the CSV structure file
    subscenario_df = csv_structure.loc[csv_structure["subscenario"] == subscenario]

    # Determine the relevant tables for this subscenario
    subscenario_table = None
    input_tables = list()
    project_flag = False
    base_table = None
    base_subscenario = None
    project_is_tx = False

    for index, row in subscenario_df.iterrows():
        # The subscenario table name will be based on the
        # "simple", "dir_subsc_only", or "dir_main" row
        if row["subscenario_type"] in ["simple", "dir_subsc_only", "dir_main"]:
            subscenario_table = "subscenarios_{}".format(row["table"])
        # Add to the list of input tables if this is not a "dir_subsc_only" row
        # This shouldn't matter, as we deal with the temporal_scenario_id
        # separately below, and currently that's the only subscenario that
        # has the "dir_subsc_only" subscenario_type
        if (
            row["subscenario_type"] != "dir_subsc_only"
            and subscenario != "temporal_scenario_id"
        ):
            input_tables.append("inputs_{}".format(row["table"]))
        # Add base table/subscenario for project-level inputs
        if int(row["project_input"]):
            project_flag = True
            base_table = row["base_table"]
            base_subscenario = row["base_subscenario"]
        if int(row["project_is_tx"]):
            project_is_tx = True

    # If we're loading a temporal_scenario_id, we'll hard code the
    # tables instead, as the structure is quite different / we load with
    # custom method
    if subscenario == "temporal_scenario_id":
        input_tables = [
            "inputs_temporal_subproblems",
            "inputs_temporal_subproblems_stages",
            "inputs_temporal_periods",
            "inputs_temporal",
            "inputs_temporal_horizons",
            "inputs_temporal_horizon_timepoints_start_end",
            "inputs_temporal_horizon_timepoints",
        ]

    # We need to reverse the order in which inputs are deleted relative to
    # how they are loaded to avoid foreign key errors
    input_tables.reverse()

    return (
        subscenario_table,
        input_tables,
        project_flag,
        project_is_tx,
        base_table,
        base_subscenario,
    )


def confirm_and_temp_update_affected_tables(
    conn,
    project_flag,
    project_is_tx,
    subscenario,
    subscenario_id,
    project,
    base_table,
    base_subscenario,
):
    """
    :param conn:
    :param project_flag: boolean
    :param project_flag: project_is_tx
    :param subscenario: str
    :param subscenario_id: int
    :param project: str
    :param base_table: str
    :param base_subscenario: str
    :return: scenario_reupdate_tuples, base_subscenario_ids_str, \
        base_subscenario_ids_data

    If this subscenario ID or the base subscenario IDs using the
    project-level subscenario_id are used in the scenarios table, confirm with
    the user that they want to update the inputs. If so, NULLify this ID in
    the scenarios table to avoid FOREIGN KEY errors when deleting the data.

    For project-level data, also NULLify
    """
    # Verify project-project_flag alignmnet
    verify_project_flag_project_alignment(
        project=project, project_flag=project_flag, subscenario=subscenario
    )

    c = conn.cursor()

    # Project-level params default to None
    base_subscenario_ids_str, base_subscenario_ids_data = None, None

    # For project-level data, we first check whether this
    # project-subscenario_id is used in the base table
    if project_flag:
        if project_is_tx:
            project_type = "transmission_line"
        else:
            project_type = "project"
        # Check if this project-subscenario ID exists in the base table
        base_subscenario_ids_sql = """
            SELECT {} FROM {} WHERE {} = ? and {} = ?
            """.format(
            base_subscenario, base_table, project_type, subscenario
        )
        base_subscenario_ids_tuples = c.execute(
            base_subscenario_ids_sql, (project, subscenario_id)
        ).fetchall()

        # If the base table has base subscenario IDs that use this
        # project-subscenario ID, check if the base subscenario is used in
        # the scenarios table
        if base_subscenario_ids_tuples:
            # To create the query, we need to create the '?' str and a tuple
            # with the base subscenario IDs
            base_subscenario_ids_str = str()
            base_subscenario_ids_data = tuple()
            for s in base_subscenario_ids_tuples:
                base_subscenario_ids_str += "?,".format(s[0])
                base_subscenario_ids_data += (s[0],)
            # Remove the final comma of the created string
            base_subscenario_ids_str = base_subscenario_ids_str[:-1]

            # Determine if there are scenarios using any of the base
            # subscenario IDs that use this project-subscenario ID;
            # if there are, we need to NULLify that base subscenario for these
            # scenarios in order to avoid a FOREIGN KEY error when deleting the
            # base subscenario ID in the base subscenario table and the
            # subscenario ID in the subscenario table
            scenarios_sql = """
                SELECT scenario_id, {}
                FROM scenarios
                WHERE {} in ({})
            """.format(
                base_subscenario, base_subscenario, base_subscenario_ids_str
            )

            scenario_reupdate_tuples = c.execute(
                scenarios_sql, base_subscenario_ids_data
            ).fetchall()
        # If this project-subscenario ID does not exist in the base table,
        # no scenarios are affected
        else:
            scenario_reupdate_tuples = []
    # For non-project-level data, we only need to check if any scenarios
    # have this subscenario ID
    else:
        # Figure out if there are scenarios using this subscenario_id;
        # if there are, we need to NULLify that subscenario for these
        # scenarios in order to avoid a FOREIGN KEY error when deleting the
        # subscenario_id
        scenarios_sql = """
            SELECT scenario_id, {}
            FROM scenarios
            WHERE {} = ?
        """.format(
            subscenario, subscenario
        )

        scenario_reupdate_tuples = c.execute(
            scenarios_sql, (subscenario_id,)
        ).fetchall()

    # If we found affected scenarios, check with the user that they aren't
    # worried about data mismatch and want to delete prior data
    # We'll exit if they say 'no'
    if scenario_reupdate_tuples:
        proceed = confirm(
            prompt="""You have scenarios that use {} {}. Deleting prior inputs 
            and reimporting may result in a mismatch between the inputs 
            specified for these scenarios and their results. Are you 
            sure you want to proceed?""".format(
                subscenario, subscenario_id
            )
        )
    # If there aren't any affected scenarios, we'll just proceed
    else:
        proceed = True

    # If we decide to proceed, we'll make the necessary temporary updates to
    # the affected tables before input deletion to avoid FOREIGN KEY errors
    if proceed:
        # To avoid foreign key errors, first NULL-ify the relevant subscenario
        # for all scenarios that use the input data we'll be deleting
        # downstream
        # Make a tuple for each affected scenario for use in the update queries
        scenarios_tuples = [(s[0],) for s in scenario_reupdate_tuples]
        scenario_update_sql = """
            UPDATE scenarios SET {} = NULL WHERE scenario_id = ?
        """.format(
            base_subscenario if project_flag else subscenario
        )
        spin_on_database_lock(
            conn=conn, cursor=c, sql=scenario_update_sql, data=scenarios_tuples
        )

        # Next, update the base table with NULLs where this
        # project-subscenario ID is used if this is a project-level input
        if project_flag:
            base_subscenario_ids_project_tuples = [
                base + (project,) for base in base_subscenario_ids_tuples
            ]
            base_table_update_sql = """
                UPDATE {} SET {} = NULL WHERE {} = ? and {} = ?
            """.format(
                base_table, subscenario, base_subscenario, project_type
            )
            spin_on_database_lock(
                conn=conn,
                cursor=c,
                sql=base_table_update_sql,
                data=base_subscenario_ids_project_tuples,
            )
    # Otherwise, we'll exit
    else:
        sys.exit()

    # We'll need to reverse the changes made above, so keep track of the
    # affected scenarios and the respective subscenario values we NULLified
    # and return for use downstream
    # We'll also pass the needed info to reupdate the scenarios table as
    # well as, for project-level data, the base table (these are None for
    # non-project-level inputs)
    scenario_reupdate_tuples = [tuple(reversed(t)) for t in scenario_reupdate_tuples]

    return scenario_reupdate_tuples, base_subscenario_ids_str, base_subscenario_ids_data


def repopulate_tables(
    conn,
    project_flag,
    project_is_tx,
    subscenario,
    subscenario_id,
    project,
    base_table,
    base_subscenario,
    scenario_reupdate_tuples,
    base_subscenario_ids_str,
    base_subscenario_ids_data,
):
    """
    :param conn:
    :param project_flag: boolean
    :param project_is_tx: boolean
    :param subscenario: str
    :param subscenario_id: int
    :param project: str
    :param base_table: str
    :param base_subscenario: int
    :param scenario_reupdate_tuples: list of tuples
    :param base_subscenario_ids_str: str
    :param base_subscenario_ids_data: tuple

    If project-level subscenario, update the base subscenario table with the
    values passed.

    Update the scenarios table with the values passed.
    """
    c = conn.cursor()

    # Update the base table if project-level if there's any update data
    if project_flag and base_subscenario_ids_data:
        if project_is_tx:
            project_type = "transmission_line"
        else:
            project_type = "project"
        base_subscenario_reupdate_sql = """
            UPDATE {} SET {} = ? WHERE {} in ({}) AND {} = ?
            """.format(
            base_table,
            subscenario,
            base_subscenario,
            base_subscenario_ids_str,
            project_type,
        )
        base_subscenario_update_tuple = (
            (int(subscenario_id),) + tuple(base_subscenario_ids_data) + (project,)
        )
        spin_on_database_lock(
            conn=conn,
            cursor=c,
            sql=base_subscenario_reupdate_sql,
            data=base_subscenario_update_tuple,
            many=False,
        )

    # Update the scenarios table if there's any update data
    if scenario_reupdate_tuples:
        scenario_reupdate_sql = """
            UPDATE scenarios SET {} = ? WHERE scenario_id = ?
        """.format(
            base_subscenario if project_flag else subscenario
        )

        spin_on_database_lock(
            conn=conn,
            cursor=c,
            sql=scenario_reupdate_sql,
            data=scenario_reupdate_tuples,
        )

        c.close()


def generic_delete_subscenario(
    conn,
    subscenario,
    subscenario_id,
    project,
    subscenario_table,
    input_tables,
    project_flag,
    project_is_tx,
):
    """
    :param conn:
    :param subscenario: str
    :param subscenario_id: int
    :param project: str
    :param subscenario_table: str
    :param input_tables: list of strings
    :param project_flag: boolean
    :param project_is_tx: boolean

    Delete prior data for a particular subscenario and subscenario ID. Some
    subscenarios have more than one input table associated with them,
    so we iterate over those. Here, we assume the input tables are in the
    correct order to avoid FOREIGN KEY errors.
    """
    c = conn.cursor()

    # Create the SQL delete statements for the subscenario info and input
    # tables
    if not project_flag:
        delete_data = (subscenario_id,)
        del_inputs_sql_list = [
            """
            DELETE FROM {}
            WHERE {} = ?;
            """.format(
                table, subscenario
            )
            for table in input_tables
        ]
        del_subscenario_sql = """
            DELETE FROM {}
            WHERE {} = ?;
            """.format(
            subscenario_table, subscenario
        )
    else:
        if project_is_tx:
            project_type = "transmission_line"
        else:
            project_type = "project"
        delete_data = (
            project,
            subscenario_id,
        )
        del_inputs_sql_list = [
            """
            DELETE FROM {}
            WHERE {} = ?
            AND {} = ?;
            """.format(
                table, project_type, subscenario
            )
            for table in input_tables
        ]
        del_subscenario_sql = """
                    DELETE FROM {}
                    WHERE {} = ?
                    AND {} = ?;
                    """.format(
            subscenario_table, project_type, subscenario
        )

    # Delete the inputs and subscenario info
    for del_inputs_sql in del_inputs_sql_list:
        spin_on_database_lock(
            conn=conn, cursor=c, sql=del_inputs_sql, data=delete_data, many=False
        )
    spin_on_database_lock(
        conn=conn, cursor=c, sql=del_subscenario_sql, data=delete_data, many=False
    )

    c.close()


def generic_insert_subscenario_info(
    conn, subscenario, table, subscenario_data, project_flag, project_is_tx
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param subscenario_data: list of tuples
    :param project_flag: boolean
    :param project_is_tx: boolean

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
            """.format(
            table, subscenario
        )
    else:
        if project_is_tx:
            project_type = "transmission_line"
        else:
            project_type = "project"
        subs_sql = """
            INSERT INTO subscenarios_{table}
            ({project}, {subscenario_id}, name, description)
            VALUES (?, ?, ?, ?);
            """.format(
            table=table, project=project_type, subscenario_id=subscenario
        )

    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql, data=subscenario_data)

    c.close()


def generic_insert_subscenario_data(
    conn,
    subscenario,
    table,
    inputs_data,
    project_flag,
    project_is_tx,
    csv_headers=None,
):
    """
    :param conn: the database connection object
    :param subscenario: str
    :param table: str
    :param inputs_data: list of tuples
    :param project_flag: boolean
    :param project_is_tx: boolean
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
    table_data_query = c.execute("""SELECT * FROM inputs_{};""".format(table))

    # If we have passed headers, check that they are as expected (i.e.
    # the same as in the table we're inserting into)
    column_names = [s[0] for s in table_data_query.description]

    if csv_headers is not None:
        if project_flag:
            headers_for_validation = [
                "transmission_line" if project_is_tx else "project",
                subscenario,
            ] + csv_headers
        else:
            headers_for_validation = [subscenario] + csv_headers
        if headers_for_validation != column_names:
            raise AssertionError(
                """
                Headers and table column names don't match.
                Column names are {}.
                Header names are {}.
                Please ensure that your header names are the same as the 
                database column names.
                """.format(
                    column_names, headers_for_validation
                )
            )

    # Create the appropriate strings needed for the insert query
    column_string = ", ".join(column_names)
    values_string = ", ".join(["?"] * len(column_names))

    inputs_sql = """
        INSERT INTO inputs_{} ({}) VALUES ({});
        """.format(
        table, column_string, values_string
    )

    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql, data=inputs_data)

    c.close()


def load_all_subscenario_ids_from_dir_to_subscenario_table(
    conn,
    subscenario,
    table,
    subscenario_type,
    project_flag,
    project_is_tx,
    cols_to_exclude_str,
    custom_method,
    inputs_dir,
    filename,
    quiet,
):
    """
    :param conn: the database connection
    :param subscenario: str; the subscenario (e.g. 'temporal_scenario_id')
    :param table: str; the subscenario table name
    :param subscenario_type: str; determines which CSV-to-DB functions to use
    :param project_flag: boolean
    :param project_is_tx: boolean
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
            project_is_tx=project_is_tx,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
        )
    elif subscenario_type in ["dir_subsc_only", "dir_main", "dir_aux"]:
        (
            skip_subscenario_info,
            skip_subscenario_data,
        ) = determine_whether_to_skip_subscenario_info_and_or_data(
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
        )


def load_single_subscenario_id_from_dir_to_subscenario_table(
    conn,
    subscenario,
    table,
    subscenario_type,
    project_flag,
    project_is_tx,
    cols_to_exclude_str,
    custom_method,
    inputs_dir,
    filename,
    quiet,
    subscenario_id_to_load,
    project,
):
    """
    :param conn: the database connection
    :param subscenario: str; the subscenario (e.g. 'temporal_scenario_id')
    :param table: str; the subscenario table name
    :param subscenario_type: str; determines which CSV-to-DB functions to use
    :param project_flag: boolean
    :param project_is_tx: boolean
    :param cols_to_exclude_str:
    :param custom_method: str
    :param inputs_dir: str
    :param filename: str
    :param quiet: boolean
    :param subscenario_id_to_load: integer; the subscenario ID to load
    :param project: str; the project for which to load data
    :return:

    Load data for a particular (project-)subscenario ID from a directory.
    """

    # Verify project-project_flag alignment
    verify_project_flag_project_alignment(
        project=project, project_flag=project_flag, subscenario=subscenario
    )

    if subscenario_type == "simple":
        if not project_flag:
            file_startswith = str(subscenario_id_to_load)
            description_delimiter = "_"
        else:
            file_startswith = "{}-{}".format(project, str(subscenario_id_to_load))
            description_delimiter = "-"

        csv_files = [
            f
            for f in os.listdir(inputs_dir)
            if f.startswith(file_startswith)
            and f[len(file_startswith)] == description_delimiter
            and f.endswith(".csv")
        ]

        if not csv_files:
            raise ValueError(
                "A CSV file for ID {} does not exist".format(file_startswith)
            )
        if len(csv_files) == 1:
            csv_file = csv_files[0]
        else:
            print("CSVS found: ", csv_files)
            raise ValueError("Only one CSV file may have ID ".format(file_startswith))

        get_subscenario_data_and_insert_into_db(
            conn=conn,
            quiet=quiet,
            subscenario=subscenario,
            table=table,
            dir_subsc=False,
            inputs_dir=inputs_dir,
            csv_file=csv_file,
            use_project_method=project_flag,
            project_is_tx=project_is_tx,
            skip_subscenario_info=False,
            skip_subscenario_data=False,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
        )

    elif subscenario_type in ["dir_subsc_only", "dir_main", "dir_aux"]:
        subscenario_directories = [
            d
            for d in sorted(next(os.walk(inputs_dir))[1])
            if d.startswith("{}_".format(subscenario_id_to_load))
        ]
        if len(subscenario_directories) == 1:
            subscenario_directory = subscenario_directories[0]
        else:
            raise ValueError(
                "Only one CSV file must have ID ".format(subscenario_id_to_load)
            )

        (
            skip_subscenario_info,
            skip_subscenario_data,
        ) = determine_whether_to_skip_subscenario_info_and_or_data(
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
            project_is_tx=False,
            skip_subscenario_info=skip_subscenario_info,
            skip_subscenario_data=skip_subscenario_data,
            cols_to_exclude_str=cols_to_exclude_str,
            custom_method=custom_method,
        )


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


def confirm(prompt=None, resp=False):
    """
    :param prompt: str
    :param resp: boolean
    :return: boolean

    Prompts for 'yes' or 'no' response from the user. Returns True for 'yes'
    and False for 'no'.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.
    """
    if prompt is None:
        prompt = "Confirm"

    if resp:
        prompt = "{} [{}]|{}: ".format(prompt, "y", "n")
    else:
        prompt = "{} [{}]|{}: ".format(prompt, "n", "y")

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ["y", "Y", "n", "N"]:
            print("Please enter y or n.")
            continue
        if ans == "y" or ans == "Y":
            return True
        if ans == "n" or ans == "N":
            return False


def verify_project_flag_project_alignment(project, project_flag, subscenario):
    """
    :param project: str
    :param project_flag: boolean
    :param subscenario: str

    Check that the if a project is specified, this is a project-level
    subscenario.

    Check that if a project is not specified, this is not a project-level
    subscenario.
    """
    if project is not None and not project_flag:
        raise ValueError(
            "The {} is not a project-level input but you have specified "
            "project {}.".format(subscenario, project)
        )

    if project is None and project_flag:
        raise ValueError(
            "Please specify which project you'd like to import data for "
            "in addition to the {}.".format(subscenario)
        )
