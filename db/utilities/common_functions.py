#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Common functions for data-loading utilities and port script.
"""

import os
import pandas as pd
import warnings


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
