#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Read input data
"""

from collections import OrderedDict
import pandas as pd
import os


def csv_read_data(folder_path, quiet):
    '''
    :param folder_path: Path to folder with input csv files
    :param quiet: boolean
    :return csv_subscenario: A pandas dataframe with subscenario id, name, description
    :return csv_data: Data for all subscenarios in a dataframe
    '''
    # The specific function will call a generic file scanner function, which will scan the folder and note the
    # subscenario file. The file only needs the string 'subscenario' in its name. The function will then read
    # each subscenario data using the filename in the subscenario file. All other files will be ignored.

    csv_data = pd.DataFrame()
    data_starting_from_row = 1  # Notes rows start from 0. So this is the 6th row in the csv.

    # ### WILL NEED TO REMOVE FROM HERE ###
    # for f in os.listdir(folder_path):
    #     if f.endswith(".csv") and 'template' not in f and 'subscenario' in f and 'ignore' not in f:
    #         if not quiet:
    #             print(f)
    #         csv_subscenario = pd.read_csv(os.path.join(folder_path, f))
    #         print(csv_subscenario)
    #
    # for row in range(0, len(csv_subscenario.index)):
    #     subscenario_filename = csv_subscenario.iloc[row]['filename']
    #     if '.csv' not in subscenario_filename:
    #         subscenario_filename = subscenario_filename + '.csv'
    #     if not quiet:
    #         print(subscenario_filename)
    #     csv_data = csv_data.append(
    #         pd.read_csv(os.path.join(folder_path, subscenario_filename)))
    # ### TO HERE ###

    # Look for CSV files
    # TODO: this does not allow for underscores in the scenario name,
    # so pass count https://stackoverflow.com/questions/30636248/split-a-string-only-by-first-space-in-python
    csv_subscenario = pd.DataFrame(columns=["id", "name", "description"])
    row_number = 0
    for f in os.listdir(folder_path):
        if f.endswith(".csv"):
            if not quiet:
                print(f)
            subscenario_id = int(f.split("_", 1)[0])
            subscenario_name = f.split("_", 1)[1].split(".csv")[0]
            print(subscenario_id, subscenario_name)
            csv_subscenario.loc[row_number] = [subscenario_id,
                                               subscenario_name, ""]
            subscenario_data_df = pd.read_csv(os.path.join(folder_path, f))
            subscenario_data_df["id"] = subscenario_id
            csv_data = csv_data.append(subscenario_data_df)

    print(csv_subscenario, csv_data)

    return (csv_subscenario, csv_data)


def csv_read_project_data(folder_path, quiet):
    '''
    :param folder_path: Path to folder with input csv files
    :param quiet: boolean
    :return csv_subscenario: A pandas dataframe with subscenario id, name, description
    :return csv_data: Data for all subscenarios in a dataframe
    '''
    # The specific function will call a generic file scanner function, which will scan the folder and note the
    # subscenario file. The file only needs the string 'subscenario' in its name. The function will then read
    # each subscenario data using the filename in the subscenario file. All other files will be ignored.

    csv_data = pd.DataFrame()
    # Look for CSV files

    csv_subscenario = pd.DataFrame(
        columns=["project", "id", "name", "description"]
    )
    row_number = 0
    for f in os.listdir(folder_path):
        if f.endswith(".csv"):
            if not quiet:
                print(f)
            # TODO: need a robust method for splitting the filename in case
            #  the same characters exist in say the project name
            #  Split on dash instead of underscore for now to allow for
            #  underscores in project name
            project = f.split("-", 1)[0]
            subscenario_id = int(f.split("-", 2)[1])
            subscenario_name = f.split("-", 2)[2].split(".csv")[0]
            print(project, subscenario_id, subscenario_name)
            csv_subscenario.loc[row_number] = [project, subscenario_id,
                                               subscenario_name, ""]
            subscenario_data_df = pd.read_csv(os.path.join(folder_path, f))
            subscenario_data_df["project"] = project
            subscenario_data_df["id"] = subscenario_id
            csv_data = csv_data.append(subscenario_data_df)

    # print(csv_subscenario, csv_data)

    return (csv_subscenario, csv_data)


def csv_read_temporal_data(folder_path, quiet):
    '''
    :param folder_path: Path to folder with input csv files
    :param quiet: boolean
    :return csv_subscenario: A pandas dataframe with subscenario id, name, description
    :return csv_data: Data for all subscenarios in a dataframe
    '''
    # The specific function will call a generic file scanner function, which will scan the folder and note the
    # subscenario file. The file only needs the string 'subscenario' in its name. The function will then read
    # each subscenario data using the filename in the subscenario file. All other files will be ignored.

    csv_data = pd.DataFrame()
    data_starting_from_row = 1  # Notes rows start from 0. So this is the 6th row in the csv.

    for f in os.listdir(folder_path):
        if f.endswith(".csv") and 'template' not in f and 'subscenario' in f and 'ignore' not in f:
            if not quiet:
                print(f)
            csv_subscenario = pd.read_csv(os.path.join(folder_path, f))

    csv_data = {}
    csv_temporal_tables = ['horizon_timepoints',
                  'horizons',
                  'periods',
                  'subproblems',
                  'subproblems_stages',
                  'timepoints']

    for temporal_table in csv_temporal_tables:
        csv_data[temporal_table] = pd.DataFrame()

    for row in range(0, len(csv_subscenario.index)):
        for temporal_table in csv_temporal_tables:
            subscenario_filename = csv_subscenario.iloc[row][temporal_table + '_filename']
            if '.csv' not in subscenario_filename:
                subscenario_filename = subscenario_filename + '.csv'
            if not quiet:
                print(subscenario_filename)
            csv_data[temporal_table] = csv_data[temporal_table].append(
                pd.read_csv(os.path.join(folder_path, 'temporal_' + temporal_table, subscenario_filename)))

    return (csv_subscenario, csv_data)

