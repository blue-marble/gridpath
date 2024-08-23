# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
import sqlite3
import sys
import time
import traceback


def connect_to_database(db_path="../db/io.db", timeout=5, detect_types=0):
    """
    :param db_path: str, the path to the database, relative to the
        current working directory, defaults to "../db/io.db"
    :param timeout: int, number of seconds the connection should wait for the
        database lock to go away before raising an exception, defaults to 5
    :param detect_types: int, type detection parameter, defaults to 0
    :return: the sqlite3 database connection object

    Connect to a database and return the connection object.
    """
    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(os.path.abspath(db_path))
        )

    conn = sqlite3.connect(db_path, timeout=timeout, detect_types=detect_types)

    # Enforce foreign keys (default = not enforced)
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn


# TODO: move to spin_database_lock_generic
def spin_on_database_lock(
    conn, cursor, sql, data, many=True, max_attempts=61, interval=10, quiet=True
):
    """
    :param conn: the connection object
    :param cursor: the cursor object
    :param sql: the SQL statement to execute
    :param data: the data to bind to the SQL statement
    :param many: boolean for whether to use executemany or execute; the
        default is True (i.e. use executemany)
    :param max_attempts: how long to wait for the database lock to be
        released; the default is 600 seconds, but that can be overridden
    :param interval: how frequently to poll the database for whether
        the lock has been released; the default is 10 seconds, but that can
        be overridden
    :param quiet: boolean; set to False to see the SQL query

    If the database is locked, wait for the lock to be released for a
    certain amount of time and occasionally retry to execute the SQL
    statement until the timeout.

    To lock the database deliberately, run the following:
        PRAGMA locking_mode = EXCLUSIVE;
        BEGIN EXCLUSIVE;
    The database will be locked until you run:
        COMMIT;
    """
    if not quiet:
        print(sql)

    for i in range(0, max_attempts):
        if i > 0:
            print("...retrying (attempt {} of {})...".format(i, max_attempts))
        try:
            if many:
                cursor.executemany(sql, data)
            else:
                cursor.execute(sql, data)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                print(
                    "Database is locked, sleeping for {} seconds, "
                    "then retrying.".format(interval)
                )
                if i == max_attempts:
                    print(
                        "Database still locked after {} seconds. "
                        "Exiting.".format(max_attempts * interval)
                    )
                    sys.exit(1)
                else:
                    time.sleep(interval)
            else:
                print("Error while running the following query:\n", sql)
                traceback.print_exc()
                sys.exit()
        # Do this if exception not caught
        else:
            # print("...done.")
            break


def spin_on_database_lock_generic(
    command,
    max_attempts=61,
    interval=10,
):
    """
    :param command:
    :param max_attempts: how long to wait for the database lock to be
        released; the default is 600 seconds, but that can be overridden
    :param interval: how frequently to poll the database for whether
        the lock has been released; the default is 10 seconds, but that can
        be overridden

    If the database is locked, wait for the lock to be released for a
    certain amount of time and occasionally retry to execute the SQL
    statement until the timeout.

    To lock the database deliberately, run the following:
        PRAGMA locking_mode = EXCLUSIVE;
        BEGIN EXCLUSIVE;
    The database will be locked until you run:
        COMMIT;
    """
    for i in range(0, max_attempts):
        if i > 0:
            print("...retrying (attempt {} of {})...".format(i, max_attempts))
        try:
            command
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                print(
                    "Database is locked, sleeping for {} seconds, "
                    "then retrying.".format(interval)
                )
                if i == max_attempts:
                    print(
                        "Database still locked after {} seconds. "
                        "Exiting.".format(max_attempts * interval)
                    )
                    sys.exit(1)
                else:
                    time.sleep(interval)
            else:
                print("Error while running the following query:\n", command)
                traceback.print_exc()
                sys.exit()
        # Do this if exception not caught
        else:
            # print("...done.")
            break
