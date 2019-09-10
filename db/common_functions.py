#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import os.path
import sqlite3


def connect_to_database(db_path, relative_path="..", timeout=5,
                        detect_types=0):
    """
    :param db_path: the path to the database
    :param relative_path: the path to the database
    :param timeout: number of seconds the connection should wait for the
        database lock to go away before raising an exception (the default is 5)
    :param detect_types: type detection parameter, defaults to 0
    :return: the connection object

    Connect to a database and return the connection object.
    """

    # If no database is specified, the database is in the 'db' directory and
    # named io.db, so give relative path to this location. The default is
    # '..' (e.g. it works if the script is in 'gridpath' or 'viz' directory)
    if db_path is None:
        db_path = os.path.join(os.getcwd(), relative_path, "db", "io.db")

    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(
                os.path.abspath(db_path)
            )
        )

    conn = sqlite3.connect(db_path, timeout=timeout, detect_types=detect_types)

    return conn
