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