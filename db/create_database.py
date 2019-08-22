#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create the database and make schema.
"""

from builtins import str
from argparse import ArgumentParser
import csv
import os.path
import sqlite3
import sys


def connect_to_database(parsed_arguments):
    """
    Connect to the database
    :param parsed_arguments:
    :return:
    """
    if parsed_arguments.in_memory:
        database = ":memory:"
    else:
        database = os.path.join(
                str(parsed_arguments.db_location),
                str(parsed_arguments.db_name)+".db"
            )
    conn = sqlite3.connect(database=database)

    return conn


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--db_name", default="io",
                        help="Name of the database.")
    parser.add_argument("--db_location", default=".",
                        help="Path to the database (relative to "
                             "create_database.py).")
    parser.add_argument("--db_schema", default="db_schema.sql",
                        help="Name of the SQL file containing the database "
                             "schema.")
    parser.add_argument("--in_memory", default=False, action="store_true",
                        help="Create in-memory database. The db_name and "
                             "db_location argument will be inactive.")
    parser.add_argument("--omit_data", default=False, action="store_true",
                        help="Don't load the model defaults data from the "
                             "data directory.")

    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def create_database_schema(db, parsed_arguments):
    """

    :param db:
    :param parsed_arguments:
    :return:
    """
    with open(parsed_arguments.db_schema, "r") as db_schema_script:
        schema = db_schema_script.read()
        db.executescript(schema)


def load_data(db, omit_data):
    """
    Load GridPath structural data (e.g. defaults, allowed modules, validation
    data, UI component data, etc.)
    :param db:
    :param omit_data:
    :return:
    """
    if not omit_data:
        c = db.cursor()

        # Data required for the UI
        with open(os.path.join(os.getcwd(), "data",
                               "ui_scenario_detail_table_metadata.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO ui_scenario_detail_table_metadata
                    (ui_table, include, ui_table_caption)
                    VALUES ('{}', {}, '{}');""".format(row[0], row[1], row[2])
                )
            db.commit()

        with open(os.path.join(os.getcwd(), "data",
                               "ui_scenario_detail_table_row_metadata.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO ui_scenario_detail_table_row_metadata
                    (ui_table, ui_table_row, include, ui_row_caption,
                    ui_row_db_scenarios_view_column, 
                    ui_row_db_subscenario_table, 
                    ui_row_db_subscenario_table_id_column, 
                    ui_row_db_input_table)
                    VALUES ('{}', '{}', {}, '{}', '{}', '{}', '{}', '{}');
                    """.format(row[0], row[1], row[2], row[3], row[4],
                               row[5], row[6], row[7])
                )
            db.commit()
    else:
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)
    db = connect_to_database(parsed_arguments=parsed_args)
    create_database_schema(db=db, parsed_arguments=parsed_args)
    load_data(db=db, omit_data=parsed_args.omit_data)


if __name__ == "__main__":
    main()
