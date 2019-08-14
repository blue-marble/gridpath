# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import sqlite3

# TODO: use flask built-in DB tools?
def connect_to_database(db_path):
    """
    :param db_path: the path to the database we're connecting to
    :return: the database connection object and a cursor object for the
      connection

    Connect to a database and return the connection object and a
    connection cursor object.
    """
    io = sqlite3.connect(db_path)
    c = io.cursor()

    return io, c
