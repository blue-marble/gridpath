#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Read input data
"""

from collections import OrderedDict
import pandas as pd
import os
import csv


def csv_read_data(folder_path):
    '''
    :param folder_path: Path to folder with input csv files
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
            print(f)
            csv_subscenario = pd.read_csv(os.path.join(folder_path, f))

    for row in range(0, len(csv_subscenario.index)):
        subscenario_filename = csv_subscenario.iloc[row]['filename']
        if '.csv' not in subscenario_filename:
            subscenario_filename = subscenario_filename + '.csv'
        print(subscenario_filename)
        csv_data = csv_data.append(
            pd.read_csv(os.path.join(folder_path, subscenario_filename)))


    return (csv_subscenario, csv_data)

def csv_read_temporal_data(folder_path):
    '''
    :param folder_path: Path to folder with input csv files
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
            print(subscenario_filename)
            csv_data[temporal_table] = csv_data[temporal_table].append(
                pd.read_csv(os.path.join(folder_path, 'temporal_' + temporal_table, subscenario_filename)))

    return (csv_subscenario, csv_data)

def csv_read_data_old(folder_path):
    '''
    :param folder_path: Path to folder with input csv files
    :return csv_subscenario: A dictionary with subscenario id, name, description
    '''
    # The specific function will call a generic file scanner function, which will scan the folder and note the files except the template
    # In a for loop, a generic csv reader function will read the first file, pull the first 5 lines into their corresponding fields, and then read the rest of the data in a dataframe from 6th row onwards.
    # The specific feature function will then pull the specific data on subscenario_id, name, and description from the output of the generic csv reader function and pass it to the load_data_into_sql function
    # Then the specific feature function will take the dataframe and manipulate it to create a dictionary that will also feed into the load_data_into_sql function.


    csv_subscenario = OrderedDict(OrderedDict())
    csv_data = pd.DataFrame()
    data_starting_from_row = 5  # Notes rows start from 0. So this is the 6th row in the csv.

    for filename in os.listdir(folder_path):
        if filename.endswith(".csv") and 'template' not in filename:
            with open(os.path.join(folder_path, filename), "r") as f:
                rows_list = list(csv.reader(f))

                csv_subscenario[
                    int(float(rows_list[1 - 1][2 - 1]))
                ] = {}
                for row in range(2 - 1, data_starting_from_row):
                    if rows_list[row][2-1] != '':
                        csv_subscenario[
                            int(float(rows_list[1 - 1][2 - 1]))
                        ][rows_list[row][1 - 1]
                        ] = rows_list[row][2-1]

            # Read data from xth line
            csv_data = csv_data.append(pd.read_csv(os.path.join(folder_path, filename), skiprows=range(1-1, data_starting_from_row)))

    return (csv_subscenario, csv_data)

# Useful functions ######
# TODO: do we want to keep these?
# from https://stackoverflow.com/questions/50929768/pandas-multiindex-more-than-2-levels-dataframe-to-nested-dict-json?noredirect=1&lq=1
# TODO: Can we move this function out of this function so they are available to the rest of the functions?

def nest(d: dict) -> dict:
    result = {}
    for key, value in d.items():
        target = result
        for k in key[:-1]:  # traverse all keys but the last
            target = target.setdefault(k, {})
        target[key[-1]] = value
    return result

def df_to_nested_dict(df: pd.DataFrame) -> dict:
    d = df.to_dict(orient='index')
    return {k: nest(v) for k, v in d.items()}

    #########