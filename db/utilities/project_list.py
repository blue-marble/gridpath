#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create a list of all projects
"""


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

    for project in projects:
        c.execute(
            """INSERT INTO inputs_project_all
            (project)
            VALUES ('{}');""".format(
                project
            )
        )
    io.commit()


if __name__ == "__main__":
    pass
