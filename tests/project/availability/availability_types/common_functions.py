#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from collections import OrderedDict
import os.path
import pandas as pd


def get_endogenous_params(test_data_directory, param, project_subset):
    """
    :param test_data_directory:
    :param param:
    :param project_subset:
    :return:

    Get the correct subset dictionary for a param from
    project_availability_endogenous.tab.
    """
    all_dict = OrderedDict(
        pd.read_csv(
            os.path.join(test_data_directory, "inputs",
                         "project_availability_endogenous.tab"),
            sep="\t"
        ).set_index('project').to_dict()[param].items()
    )
    subset_dict = dict()
    for prj in all_dict:
        if prj in project_subset:
            subset_dict[prj] = all_dict[prj]
        else:
            pass

    return subset_dict
