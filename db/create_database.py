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

"""
Create an empty GridPath database with the appropriate table structure.

The user may specify the name and location of the GridPath database path using the
*--database* flag.

>>> gridpath_create_database --database PATH/DO/DB

The default schema for the GridPath SQLite database is in db_schema.sql.

.. _database-structure-section-ref:

"""


from argparse import ArgumentParser
import csv
import os.path
import pandas as pd
import sqlite3
import sys

from db.common_functions import spin_on_database_lock, spin_on_database_lock_generic


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument(
        "--database",
        default="./io.db",
        help="The database file path relative to the current "
        "working directory. Defaults to ./io.db ",
    )
    parser.add_argument(
        "--db_schema",
        default="db_schema.sql",
        help="Name of the SQL file containing the database "
        "schema. Assumed to be in same directory as"
        "create_database.py",
    )
    parser.add_argument(
        "--in_memory",
        default=False,
        action="store_true",
        help="Create in-memory database. The database " "argument will be inactive.",
    )
    parser.add_argument(
        "--data_directory",
        default="./data",
        help="Directory of model defaults data.",
    )
    parser.add_argument(
        "--omit_data",
        default=False,
        action="store_true",
        help="Don't load the model defaults data from the data directory.",
    )
    parser.add_argument(
        "--custom_units",
        default=False,
        action="store_true",
        help="Ask the user for custom units.",
    )

    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def create_database_schema(conn, parsed_arguments):
    """
    :param conn: database connection
    :param parsed_arguments:

    """
    schema_path = os.path.join(os.path.dirname(__file__), parsed_arguments.db_schema)

    with open(schema_path, "r") as db_schema_script:
        schema = db_schema_script.read()
        conn.executescript(schema)


def load_data(conn, data_directory, omit_data, custom_units):
    """
    Load GridPath structural data (e.g. defaults, allowed modules, validation
    data, UI component data, etc.)
    :param conn: database connection
    :param data_directory:
    :param omit_data:
    :param custom_units: Boolean, True if user-specified units
    :return:
    """
    if not omit_data:
        # General Model Data
        expected_files = [
            "mod_availability_types",
            "mod_capacity_types",
            "mod_features",
            "mod_feature_subscenarios",
            "mod_horizon_boundary_types",
            "mod_months",
            "mod_operational_types",
            "mod_prm_types",
            "mod_reserve_types",
            "mod_run_status_types",
            "mod_tx_availability_types",
            "mod_tx_capacity_types",
            "mod_tx_operational_types",
            "mod_capacity_and_operational_type_invalid_combos",
            "mod_tx_capacity_and_tx_operational_type_invalid_combos",
            "mod_units",
            "mod_validation_status_types",
            "ui_scenario_detail_table_metadata",
            "ui_scenario_detail_table_row_metadata",
            "ui_scenario_results_plot_metadata",
            "ui_scenario_results_table_metadata",
            "viz_technologies",
        ]
        for f in expected_files:
            load_aux_data(conn=conn, data_directory=data_directory, filename=f)

        set_custom_units(conn=conn, custom_units=custom_units)


def set_custom_units(conn, custom_units):
    """
    Load the units
    :param conn:
    :param custom_units: Boolean, True if user-specified units
    :return:
    """
    c = conn.cursor()
    if custom_units:
        # Retrieve settings from user
        power = input(
            """
            Specify the unit of power, e.g. kW, MW, GW, etc.
            Note: the unit of energy will be derived from the unit of power by 
            multiplying by 1 hour, e.g. MW -> MWh.
            Use `default` to keep the defaults (MW). 
            """
        )
        fuel_energy = input(
            """
            Specify the unit of fuel energy content, e.g. MMBtu, J, MJ, etc.
            Use 'default' to keep defaults (MMBtu). 
            """
        )
        cost = input(
            """
            Specify the unit of cost, e.g. USD, EUR, INR, etc.
            Use 'default' to keep defaults (USD).
            """
        )
        carbon_emissions = input(
            """
            Specify the unit of carbon emissions, e.g. tCO2, MtCO2, etc. 
            Use 'default' to keep defaults (tCO2; metric tonne)
            """
        )

        # Update table with user settings
        if power != "default":
            sql = """UPDATE mod_units
                SET unit = ?
                WHERE metric = 'power'"""
            spin_on_database_lock(
                conn=conn, cursor=c, sql=sql, many=False, data=(power,)
            )
            # add energy units based on user's power units
            energy = power + "h"
            sql = """UPDATE mod_units
                SET unit = ?
                WHERE metric = 'energy'"""
            spin_on_database_lock(
                conn=conn, cursor=c, sql=sql, many=False, data=(energy,)
            )
        if fuel_energy != "default":
            sql = """UPDATE mod_units
                SET unit = ?
                WHERE metric = 'fuel_energy'"""
            spin_on_database_lock(
                conn=conn, cursor=c, sql=sql, many=False, data=(fuel_energy,)
            )
        if cost != "default":
            sql = """UPDATE mod_units
                SET unit = ?
                WHERE metric = 'cost'"""
            spin_on_database_lock(
                conn=conn, cursor=c, sql=sql, many=False, data=(cost,)
            )
        if carbon_emissions != "default":
            sql = """UPDATE mod_units
                SET unit = ?
                WHERE metric = 'carbon_emissions'"""
            spin_on_database_lock(
                conn=conn, cursor=c, sql=sql, many=False, data=(carbon_emissions,)
            )

    # Derive secondary units
    df = pd.read_sql(sql="SELECT * FROM mod_units", con=conn, index_col="metric")
    for sec_metric in df[df["type"] == "secondary"].index:
        numerator = df.loc[sec_metric, "numerator_core_units"]
        if pd.isna(numerator) or numerator == "":
            num_str = "1"
        else:
            num_metrics = numerator.split("*")
            num_units = [df.loc[m, "unit"] for m in num_metrics]
            num_str = "-".join(num_units)

        denominator = df.loc[sec_metric, "denominator_core_units"]
        if pd.isna(denominator) or denominator == "":
            denom_str = ""
        else:
            denom_metrics = denominator.split("*")
            denom_units = [df.loc[m, "unit"] for m in denom_metrics]
            denom_str = "/" + "-".join(denom_units)

        sec_unit = num_str + denom_str

        sql = """UPDATE mod_units
            SET unit = ?
            WHERE metric = ?"""
        spin_on_database_lock(
            conn=conn, cursor=c, sql=sql, many=False, data=(sec_unit, sec_metric)
        )


def load_aux_data(conn, data_directory, filename):
    """
    :param conn:
    :param data_directory:
    :param filename:
    :param sql:
    :return:

    """
    data = []
    cursor = conn.cursor()

    file_path = os.path.join(data_directory, f"{filename}.csv")
    df = pd.read_csv(file_path, delimiter=",")
    spin_on_database_lock_generic(
        command=df.to_sql(
            name=filename,
            con=conn,
            if_exists="append",
            index=False,
        )
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)

    if parsed_args.in_memory:
        db_path = ":memory:"
    else:
        db_path = parsed_args.database
        if os.path.isfile(db_path):
            print(
                """WARNING: The database file {} already exists. Please 
                delete it before re-creating the database""".format(
                    os.path.abspath(db_path)
                )
            )
            sys.exit()

    # Connect to the database
    conn = sqlite3.connect(database=db_path)
    # Allow concurrent reading and writing
    conn.execute("PRAGMA journal_mode=WAL")
    # Enforce foreign keys (default = not enforced)
    conn.execute("PRAGMA foreign_keys=ON;")
    # Create schema
    create_database_schema(conn=conn, parsed_arguments=parsed_args)
    # Load data
    load_data(
        conn=conn,
        omit_data=parsed_args.omit_data,
        data_directory=parsed_args.data_directory,
        custom_units=parsed_args.custom_units,
    )
    # Close the database
    conn.close()


if __name__ == "__main__":
    main()
