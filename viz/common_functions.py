#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import os.path
import sqlite3


def connect_to_database(parsed_arguments):
    """
    Connect to the database
    :param parsed_arguments:
    :return:
    """
    if parsed_arguments.database is None:
        db_path = os.path.join(os.getcwd(), "..", "db", "io.db")
    else:
        db_path = parsed_arguments.database

    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(
                os.path.abspath(db_path)
            )
        )

    conn = sqlite3.connect(db_path)

    return conn
