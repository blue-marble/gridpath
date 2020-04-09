#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import csv
import os.path
import pandas as pd


# TODO: use this in capacity and operational type project subset
#  determinations
def determine_project_subset(
        scenario_directory, subproblem, stage, column, type
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param column:
    :param type:
    :return:

    """

    project_subset = list()

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs",
                         "projects.tab"),
            sep="\t", usecols=["project", column]
        )

    for row in zip(dynamic_components["project"],
                   dynamic_components[column]):
        if row[1] == type:
            project_subset.append(row[0])
        else:
            pass

    return project_subset


def check_if_linear_horizon_first_timepoint(mod, tmp, balancing_type):
    return tmp == mod.first_hrz_tmp[
        balancing_type, mod.horizon[tmp, balancing_type]] \
            and mod.boundary[
               balancing_type, mod.horizon[tmp, balancing_type]] \
            == "linear"


def check_if_linear_horizon_last_timepoint(mod, tmp, balancing_type):
    return tmp == mod.last_hrz_tmp[
        balancing_type, mod.horizon[tmp, balancing_type]] \
            and mod.boundary[
               balancing_type, mod.horizon[tmp, balancing_type]] \
            == "linear"


def get_column_row_value(header, column_name, row):
    """
    :param header: list; the CSV file header (list of column names)
    :param column_name: string; the column name we're looking for
    :param row: list; the values in the current row
    :return:

    Check if the header contains the column_name; if not, return None for
    the value for this column_name in this row; if it does, get the right
    value from the value based on the column_name index in the header.
    """
    try:
        column_index = header.index(column_name)
    except ValueError:
        column_index = None

    row_column_value = None if column_index is None else row[column_index]

    return row_column_value


def append_to_input_file(
        inputs_directory, input_file, query_results, new_columns
):
    """

    :param inputs_directory:
    :param input_file:
    :param query_results:
    :param new_columns:
    :return:
    """

    # Make a dictionary by project for easy access
    dict_by_project = dict()
    for row in query_results:
        prj = str(row[0])
        prj_char = row[1:]
        # Assign values for each project key
        # Replace None values with "." to feed into Pyomo
        dict_by_project[prj] = ["." if x is None else x for x in prj_char]

    # Open the projects file
    with open(os.path.join(inputs_directory, input_file), "r") as f_in:
        # Read in the file
        reader = csv.reader(f_in, delimiter="\t", lineterminator="\n")

        # We'll be changing each row of the reader and adding the updated
        # row to this list
        new_rows = list()

        # First, add the new items to the header and append the updated
        # header to the new_rows list
        header = next(reader)
        for h in new_columns:
            header.append(h)
        new_rows.append(header)

        # Next, append the new values to the row for each project and add
        # the updated row to the new_rows list
        for row in reader:
            prj = row[0]
            # If the project is in the dictionary keys, add the values from
            # the dictionary to the project row and append the updated row
            # to the new_rows list
            if prj in list(dict_by_project.keys()):
                for char in dict_by_project[prj]:
                    row.append(char)
                new_rows.append(row)
            # If project is not in the dictionary keys, fill the row with
            # "." to feed empty values into Pyomo and append the updated row
            # to the new_rows list
            else:
                for h in new_columns:
                    row.append(".")
                new_rows.append(row)

    # Now that we have updated all our rows, overwrite the previous
    # projects.tab file
    with open(os.path.join(inputs_directory, input_file), "w",
              newline="") as f_out:
        writer = csv.writer(f_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)
