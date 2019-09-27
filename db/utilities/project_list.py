#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create a list of all projects
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def project_list(
        io, c,
        projects
):
    """
    Make a list of all projects
    This list is used only indirectly to make other input tables
    :param io: 
    :param c: 
    :param projects: 
    :return: 
    """

    print("project list")

    data = [(p,) for p in projects]
    sql = \
        """INSERT INTO inputs_project_all (project) VALUES (?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=sql, data=data)


if __name__ == "__main__":
    pass
