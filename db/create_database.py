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

from db.common_functions import spin_on_database_lock


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
        "--omit_data",
        default=False,
        action="store_true",
        help="Don't load the model defaults data from the " "data directory.",
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


def load_data(conn, omit_data, custom_units):
    """
    Load GridPath structural data (e.g. defaults, allowed modules, validation
    data, UI component data, etc.)
    :param conn: database connection
    :param omit_data:
    :param custom_units: Boolean, True if user-specified units
    :return:
    """
    # TODO: refactor this
    if not omit_data:
        # General Model Data
        load_mod_months(conn=conn)
        load_mod_capacity_types(conn=conn)
        load_mod_availability_types(conn=conn)
        load_mod_operational_types(conn=conn)
        load_mod_reserve_types(conn=conn)
        load_mod_tx_capacity_types(conn=conn)
        load_mod_tx_availability_types(conn=conn)
        load_mod_tx_operational_types(conn=conn)
        load_mod_prm_types(conn=conn)
        load_mod_capacity_and_operational_type_invalid_combos(conn=conn)
        load_mod_tx_capacity_and_tx_operational_type_invalid_combos(conn=conn)
        load_mod_horizon_boundary_types(conn=conn)
        load_mod_run_status_types(conn=conn)
        load_mod_validation_status_types(conn=conn)
        load_mod_features(conn=conn)
        load_mod_feature_subscenarios(conn=conn)
        load_mod_units(conn=conn, custom_units=custom_units)

        # Data required for the UI
        load_ui_scenario_detail_table_metadata(conn=conn)
        ui_scenario_detail_table_row_metadata(conn=conn)
        load_ui_scenario_results_table_metadata(conn=conn)
        load_ui_scenario_results_plot_metadata(conn=conn)

        # Data for plotting
        load_viz_technologies(conn=conn)


def load_mod_months(conn):
    sql = """
        INSERT INTO mod_months
        (month, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_months.csv", sql=sql)


def load_mod_capacity_types(conn):
    sql = """
        INSERT INTO mod_capacity_types
        (capacity_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_capacity_types.csv", sql=sql)


def load_mod_availability_types(conn):
    sql = """
        INSERT INTO mod_availability_types
        (availability_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_availability_types.csv", sql=sql)


def load_mod_operational_types(conn):
    sql = """
        INSERT INTO mod_operational_types
        (operational_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_operational_types.csv", sql=sql)


def load_mod_reserve_types(conn):
    sql = """
        INSERT INTO mod_reserve_types
        (reserve_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_reserve_types.csv", sql=sql)


def load_mod_tx_capacity_types(conn):
    sql = """
        INSERT INTO mod_tx_capacity_types
        (capacity_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_tx_capacity_types.csv", sql=sql)


def load_mod_tx_availability_types(conn):
    sql = """
        INSERT INTO mod_tx_availability_types
        (availability_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_tx_availability_types.csv", sql=sql)


def load_mod_tx_operational_types(conn):
    sql = """
        INSERT INTO mod_tx_operational_types
        (operational_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_tx_operational_types.csv", sql=sql)


def load_mod_prm_types(conn):
    sql = """
        INSERT INTO mod_prm_types
        (prm_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_prm_types.csv", sql=sql)


def load_mod_capacity_and_operational_type_invalid_combos(conn):
    sql = """
        INSERT INTO 
        mod_capacity_and_operational_type_invalid_combos
        (capacity_type, operational_type)
        VALUES (?, ?);"""
    load_aux_data(
        conn=conn,
        filename="mod_capacity_and_operational_type_invalid_combos.csv",
        sql=sql,
    )


def load_mod_tx_capacity_and_tx_operational_type_invalid_combos(conn):
    sql = """
        INSERT INTO 
        mod_tx_capacity_and_tx_operational_type_invalid_combos
        (capacity_type, operational_type)
        VALUES (?, ?);"""
    load_aux_data(
        conn=conn,
        filename="mod_tx_capacity_and_tx_operational_type_invalid_combos.csv",
        sql=sql,
    )


def load_mod_horizon_boundary_types(conn):
    sql = """
        INSERT INTO mod_horizon_boundary_types
        (horizon_boundary_type, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_horizon_boundary_types.csv", sql=sql)


def load_mod_run_status_types(conn):
    sql = """
        INSERT INTO mod_run_status_types
        (run_status_id, run_status_name)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_run_status_types.csv", sql=sql)


def load_mod_validation_status_types(conn):
    sql = """
        INSERT INTO mod_validation_status_types
        (validation_status_id, validation_status_name)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_validation_status_types.csv", sql=sql)


def load_mod_features(conn):
    sql = """
        INSERT INTO mod_features
        (feature, description)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_features.csv", sql=sql)


def load_mod_feature_subscenarios(conn):
    sql = """
        INSERT INTO mod_feature_subscenarios
        (feature, subscenario_id)
        VALUES (?, ?);"""
    load_aux_data(conn=conn, filename="mod_feature_subscenarios.csv", sql=sql)


def load_mod_units(conn, custom_units):
    """
    Load the units
    :param conn:
    :param custom_units: Boolean, True if user-specified units
    :return:
    """
    c = conn.cursor()

    sql = """
        INSERT INTO mod_units
        (metric, type, numerator_core_units, denominator_core_units,
        unit, description)
        VALUES (?, ?, ?, ?, ?, ?);"""
    load_aux_data(conn=conn, filename="mod_units.csv", sql=sql)

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


def load_ui_scenario_detail_table_metadata(conn):
    sql = """
        INSERT INTO ui_scenario_detail_table_metadata
        (ui_table, include, ui_table_caption)
        VALUES (?, ?, ?);"""
    load_aux_data(conn=conn, filename="ui_scenario_detail_table_metadata.csv", sql=sql)


def ui_scenario_detail_table_row_metadata(conn):
    sql = """
        INSERT INTO ui_scenario_detail_table_row_metadata
        (ui_table, ui_table_row, include, ui_row_caption,
        ui_row_db_scenarios_view_column, 
        ui_row_db_subscenario_table, 
        ui_row_db_subscenario_table_id_column, 
        ui_row_db_input_table)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
    load_aux_data(
        conn=conn, filename="ui_scenario_detail_table_row_metadata.csv", sql=sql
    )


def load_ui_scenario_results_table_metadata(conn):
    sql = """
        INSERT INTO ui_scenario_results_table_metadata
        (results_table, include, caption)
        VALUES (?, ?, ?);
        """
    load_aux_data(conn=conn, filename="ui_scenario_results_table_metadata.csv", sql=sql)


def load_ui_scenario_results_plot_metadata(conn):
    sql = """
        INSERT INTO ui_scenario_results_plot_metadata
        (results_plot, include, caption, load_zone_form_control,
        energy_target_zone_form_control, carbon_cap_zone_form_control,
        period_form_control, horizon_form_control,
        start_timepoint_form_control, end_timepoint_form_control,
        stage_form_control, project_form_control, commit_project_form_control)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
    load_aux_data(conn=conn, filename="ui_scenario_results_plot_metadata.csv", sql=sql)


def load_viz_technologies(conn):
    sql = """
        INSERT INTO viz_technologies
        (technology, color, plotting_order)
        VALUES (?, ?, ?);"""
    load_aux_data(conn=conn, filename="viz_technologies.csv", sql=sql)


def load_aux_data(conn, filename, sql):
    """
    :param conn:
    :param filename:
    :param sql:
    :return:

    """
    data = []
    cursor = conn.cursor()

    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(file_path, "r") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for row in reader:
            data.append(tuple([row[i] for i in range(len(row))]))

    spin_on_database_lock(conn=conn, cursor=cursor, sql=sql, data=data)


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
        custom_units=parsed_args.custom_units,
    )
    # Close the database
    conn.close()


if __name__ == "__main__":
    main()
