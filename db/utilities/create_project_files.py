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
Create individual project-subscenario ID files from a file containing data
for all project-subscenario IDs.

This expects the first three columns of the aggregated file to be
"project", "subscenario_id", and "subscenario_name" in that order.
These should be followed by the data columns for the particular subscenario,
e.g. "down_time_cutoff_hours", "startup_plus_ramp_up_rate", and
"startup_cost_per_mw" for startup characteristics.
"""

from argparse import ArgumentParser
import os.path
import pandas as pd
import sys


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    # Database name and location options
    parser.add_argument(
        "--agg_csv_filepath",
        help="The path to the file with the data for all "
        "project-subscenario IDs. Note that the first "
        "three columns of this file should be'project', "
        "'subscenario_id', and 'subscenario_name', "
        "and those should be followed by the data "
        "columns.",
    )
    parser.add_argument(
        "--project_csv_folder",
        help="Path to the folder where the project CSVs " "should be written.",
    )
    parser.add_argument(
        "--verbose", default=False, action="store_true", help="Print output."
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_individual_csvs_from_aggregate_csv(
    agg_csv_filepath,
    project_csv_folder,
    verbose,
):
    """
    :param agg_csv_filepath: str; the path to the CSV with aggregated data
    :param project_csv_folder: str; the directory where to write the
        individual files
    :param verbose: boolean; whether or not to print output

    Read the aggregated CSV file, check for some errors, and write
    individual files based on the data in the aggregated file.
    """

    # Read the aggregate CSV as dataframe
    agg_csv_df = pd.read_csv(agg_csv_filepath)
    if verbose:
        print("Data loaded from {}.".format(agg_csv_filepath))

    # We're expecting the first three columns to be project, subscenario_id,
    # and subscenario_name, so check this first
    header_agg = [col for col in agg_csv_df.columns]
    if header_agg[0:3] != ["project", "subscenario_id", "subscenario_name"]:
        raise ValueError(
            """
            The first three columns of the aggregate file must be:
            "project", "subscenario_id", and "subscenario_name" in that order.
            """
        )

    # Get the data column names
    header_ind = header_agg[3:]

    # Get unique project-subscenario_id-subscenario_name combinations
    unique_prj_id_name = agg_csv_df[
        ["project", "subscenario_id", "subscenario_name"]
    ].drop_duplicates()

    # Get unique project-subscenario_id combinations for a quick check
    unique_prj_id = agg_csv_df[["project", "subscenario_id"]].drop_duplicates()

    # Check that we don't have extra names specified
    if len(unique_prj_id_name) != len(unique_prj_id):
        raise ValueError(
            """
            You have more than subscenario_name specified for the same 
            project-subscenario_id combination.
            """
        )

    # Iterate over project-subscenario_id-subscenario_name combinations to
    # create the individual files
    if verbose:
        print("Writing individual files to {}.".format(project_csv_folder))
    for project, subscenario_id, subscenario_name in unique_prj_id_name.values:
        ind_csv_name = "{}-{}-{}.csv".format(project, subscenario_id, subscenario_name)

        if verbose:
            print("... {}".format(ind_csv_name))

        # Get the sub-dataframe for this project-subscenario_id-name
        ind_df = agg_csv_df[
            (agg_csv_df["project"] == project)
            & (agg_csv_df["subscenario_id"] == subscenario_id)
            & (agg_csv_df["subscenario_name"] == subscenario_name)
        ][header_ind]

        # Write the dataframe to CSV
        ind_filepath = os.path.join(project_csv_folder, ind_csv_name)
        ind_df.to_csv(ind_filepath, index=False)


if __name__ == "__main__":
    parsed_args = parse_arguments(args=sys.argv[1:])

    create_individual_csvs_from_aggregate_csv(
        agg_csv_filepath=parsed_args.agg_csv_filepath,
        project_csv_folder=parsed_args.project_csv_folder,
        verbose=parsed_args.verbose,
    )
