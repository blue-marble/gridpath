#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project list
"""

from db.utilities import project_list

def load_project_list(io, c, subscenario_input, data_input):

    """
    Insert list of all projects
    :return:
    """

    projects = list()

    projects = data_input['project'].unique().tolist()

    project_list.project_list(
        io=io, c=c,
        projects=projects
    )