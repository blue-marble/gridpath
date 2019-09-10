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


def database_file_exists(db_path):
    """
    :param db_path:
    :return: boolean

    Check if the database file exists.
    """
    if os.path.isfile(db_path):
        return True
    else:
        return False


def get_database_file_path(parsed_arguments):
    """
    :param parsed_arguments: the parsed script arguments
    :return: the path to the database

    Get the database file path from the script arguments.
    """
    if parsed_arguments.in_memory:
        database = ":memory:"
    else:
        database = os.path.join(
                str(parsed_arguments.db_location),
                str(parsed_arguments.db_name)+".db"
            )

    return database


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

        # General Model Data

        # mod_months
        with open(os.path.join(os.getcwd(), "data",
                               "mod_months.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_months
                    (month, description)
                    VALUES ({}, '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_capacity_types
        with open(os.path.join(os.getcwd(), "data",
                               "mod_capacity_types.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_capacity_types
                    (capacity_type, description)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_operational_types
        with open(os.path.join(os.getcwd(), "data",
                               "mod_operational_types.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_operational_types
                    (operational_type, description)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # reserve_types
        with open(os.path.join(os.getcwd(), "data",
                               "mod_reserve_types.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_reserve_types
                    (reserve_type, description)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_capacity_and_operational_type_invalid_combos
        with open(
                os.path.join(
                    os.getcwd(), "data",
                    "mod_capacity_and_operational_type_invalid_combos.csv"
                ),
                "r"
        ) as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO 
                    mod_capacity_and_operational_type_invalid_combos
                    (capacity_type, operational_type)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_horizon_boundary_types
        with open(os.path.join(os.getcwd(), "data",
                               "mod_horizon_boundary_types.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_horizon_boundary_types
                    (horizon_boundary_type, description)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_run_status_types
        with open(os.path.join(os.getcwd(), "data",
                               "mod_run_status_types.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_run_status_types
                    (run_status_id, run_status_name)
                    VALUES ({}, '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_validation_status_types
        with open(os.path.join(os.getcwd(), "data",
                               "mod_validation_status_types.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_validation_status_types
                    (validation_status_id, validation_status_name)
                    VALUES ({}, '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_features
        with open(os.path.join(os.getcwd(), "data",
                               "mod_features.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_features
                    (feature, description)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # mod_feature_subscenarios
        with open(os.path.join(os.getcwd(), "data",
                               "mod_feature_subscenarios.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO mod_feature_subscenarios
                    (feature, subscenario_id)
                    VALUES ('{}', '{}');""".format(row[0], row[1])
                )
            db.commit()

        # Data required for the UI

        # ui_scenario_detail_table_metadata
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

        # ui_scenario_detail_table_row_metadata
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

        # ui_scenario_results_plot_metadata
        with open(os.path.join(os.getcwd(), "data",
                               "ui_scenario_results_plot_metadata.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO ui_scenario_results_plot_metadata
                    (results_plot, include, caption, load_zone_form_control,
                    rps_zone_form_control, carbon_cap_zone_form_control,
                    period_form_control, horizon_form_control, 
                    stage_form_control, project_form_control)
                    VALUES ('{}', {}, '{}', {}, {}, {}, {}, {}, {}, {});
                    """.format(row[0], row[1], row[2], row[3], row[4],
                               row[5], row[6], row[7], row[8], row[9])
                )
            db.commit()

        # ui_scenario_results_plot_metadata
        with open(os.path.join(os.getcwd(), "data",
                               "ui_scenario_results_table_metadata.csv"),
                  "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                c.execute(
                    """INSERT INTO ui_scenario_results_table_metadata
                    (results_table, include, caption)
                    VALUES ('{}', {}, '{}');
                    """.format(row[0], row[1], row[2])
                )
            db.commit()

    else:
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)

    db_path = get_database_file_path(parsed_arguments=parsed_args)

    if database_file_exists(db_path=db_path):
        print(
            "WARNING: The database file {} already exists. Please delete it "
            "before re-creating the database.".format(os.path.abspath(db_path))
        )
        sys.exit()
    else:
        db = sqlite3.connect(database=db_path)
        create_database_schema(db=db, parsed_arguments=parsed_args)
        load_data(db=db, omit_data=parsed_args.omit_data)


if __name__ == "__main__":
    main()
