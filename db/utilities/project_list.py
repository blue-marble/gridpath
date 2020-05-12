#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create a list of all projects
"""

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

    data = [(p,) for p in projects]
    sql = """
        INSERT OR IGNORE INTO inputs_project_all (project) VALUES (?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=sql, data=data)

    c.close()


if __name__ == "__main__":
    pass


# TODO: revisit role of project list
def load_from_csv(io, c, subscenario_input, data_input):

    """
    Insert list of all projects
    :return:
    """

    projects = data_input['project'].unique().tolist()

    project_list(
        io=io, c=c,
        projects=projects
    )

    c.close()
