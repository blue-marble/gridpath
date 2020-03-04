#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""

"""

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
    return tmp == mod.first_horizon_timepoint[
        balancing_type, mod.horizon[tmp, balancing_type]] \
            and mod.boundary[
               balancing_type, mod.horizon[tmp, balancing_type]] \
            == "linear"


def check_if_linear_horizon_last_timepoint(mod, tmp, balancing_type):
    return tmp == mod.last_horizon_timepoint[
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
