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

from db.common_functions import spin_on_database_lock


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
        load_mod_months(db=db, c=c)
        load_mod_capacity_types(db=db, c=c)
        load_mod_operational_types(db=db, c=c)
        load_mod_reserve_types(db=db, c=c)
        load_mod_capacity_and_operational_type_invalid_combos(db=db, c=c)
        load_mod_horizon_boundary_types(db=db, c=c)
        load_mod_run_status_types(db=db, c=c)
        load_mod_validation_status_types(db=db, c=c)
        load_mod_features(db=db, c=c)
        load_mod_feature_subscenarios(db=db, c=c)

        # Data required for the UI
        load_ui_scenario_detail_table_metadata(db=db, c=c)
        ui_scenario_detail_table_row_metadata(db=db, c=c)
        load_ui_scenario_results_table_metadata(db=db, c=c)
        load_ui_scenario_results_plot_metadata(db=db, c=c)

    else:
        pass


def load_mod_months(db, c):
    sql = \
        """INSERT INTO mod_months
        (month, description)
        VALUES (?, ?);"""    
    load_aux_data(conn=db, cursor=c, filename="mod_months.csv", sql=sql)


def load_mod_capacity_types(db, c):
    sql = \
         """INSERT INTO mod_capacity_types
                (capacity_type, description)
                VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_capacity_types.csv", 
                  sql=sql)


def load_mod_operational_types(db, c):
    sql = \
        """INSERT INTO mod_operational_types
        (operational_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_operational_types.csv", 
                  sql=sql)


def load_mod_reserve_types(db, c):
    sql = \
        """INSERT INTO mod_reserve_types
        (reserve_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_reserve_types.csv", sql=sql)


def load_mod_capacity_and_operational_type_invalid_combos(db, c):
    sql = \
        """INSERT INTO 
        mod_capacity_and_operational_type_invalid_combos
        (capacity_type, operational_type)
        VALUES (?, ?);""".format()
    load_aux_data(conn=db, cursor=c, 
                  filename=
                  "mod_capacity_and_operational_type_invalid_combos.csv", 
                  sql=sql)


def load_mod_horizon_boundary_types(db, c):
    sql = \
        """INSERT INTO mod_horizon_boundary_types
        (horizon_boundary_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_horizon_boundary_types.csv",
                  sql=sql)


def load_mod_run_status_types(db, c):
    sql = \
        """INSERT INTO mod_run_status_types
        (run_status_id, run_status_name)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_run_status_types.csv", 
                  sql=sql)


def load_mod_validation_status_types(db, c):
    sql = \
        """INSERT INTO mod_validation_status_types
        (validation_status_id, validation_status_name)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, 
                  filename="mod_validation_status_types.csv", sql=sql)


def load_mod_features(db, c):
    sql = \
        """INSERT INTO mod_features
        (feature, description)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_features.csv", sql=sql)


def load_mod_feature_subscenarios(db, c):
    sql = \
        """INSERT INTO mod_feature_subscenarios
        (feature, subscenario_id)
        VALUES (?, ?);"""
    load_aux_data(conn=db, cursor=c, filename="mod_feature_subscenarios.csv", 
                  sql=sql)


def load_ui_scenario_detail_table_metadata(db, c):
    sql = \
        """INSERT INTO ui_scenario_detail_table_metadata
        (ui_table, include, ui_table_caption)
        VALUES (?, ?, ?);"""
    load_aux_data(conn=db, cursor=c, 
                  filename="ui_scenario_detail_table_metadata.csv", sql=sql)


def ui_scenario_detail_table_row_metadata(db, c):
    sql = \
        """INSERT INTO ui_scenario_detail_table_row_metadata
        (ui_table, ui_table_row, include, ui_row_caption,
        ui_row_db_scenarios_view_column, 
        ui_row_db_subscenario_table, 
        ui_row_db_subscenario_table_id_column, 
        ui_row_db_input_table)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
    load_aux_data(conn=db, cursor=c,
                  filename="ui_scenario_detail_table_row_metadata.csv",
                  sql=sql)


def load_ui_scenario_results_table_metadata(db, c):
    sql = \
        """INSERT INTO ui_scenario_results_table_metadata
        (results_table, include, caption)
        VALUES (?, ?, ?);
        """
    load_aux_data(conn=db, cursor=c,
                  filename="ui_scenario_results_table_metadata.csv",
                  sql=sql)


def load_ui_scenario_results_plot_metadata(db, c):
    sql = \
        """INSERT INTO ui_scenario_results_plot_metadata
        (results_plot, include, caption, load_zone_form_control,
        rps_zone_form_control, carbon_cap_zone_form_control,
        period_form_control, horizon_form_control, 
        stage_form_control, project_form_control)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
    load_aux_data(conn=db, cursor=c,
                  filename="ui_scenario_results_plot_metadata.csv",
                  sql=sql)


def load_aux_data(conn, cursor, filename, sql):
    """
    :param conn: 
    :param cursor: 
    :param filename: 
    :param sql: 
    
    
    """
    data = []
    with open(os.path.join(os.getcwd(), "data", filename), "r") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for row in reader:
            data.append(tuple([row[i] for i in range(len(row))]))

    spin_on_database_lock(conn=conn, cursor=cursor, sql=sql, data=data)


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
        # Connect to the database
        db = sqlite3.connect(database=db_path)
        # Allow concurrent reading and writing
        db.execute("PRAGMA journal_mode=WAL")
        # Create schema
        create_database_schema(db=db, parsed_arguments=parsed_args)
        # Load data
        load_data(db=db, omit_data=parsed_args.omit_data)
        # Close the database
        db.close()


if __name__ == "__main__":
    main()
