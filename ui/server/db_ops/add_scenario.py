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
Create or update scenario based on input from the UI client.
"""

from flask_socketio import emit

from db.utilities.scenario import create_scenario, update_scenario_multiple_columns
from db.common_functions import connect_to_database


def add_or_update_scenario(db_path, msg):
    """
    :param db_path: the database path
    :param msg: the client message
    :return: None

    Create or update a scenario. If the scenario name already exists,
    we will update the scenario; otherwise, a new scenario is created.
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    # Check if this is a new scenario or if we're updating an existing scenario
    # TODO: implement UI warnings if scenario exists
    scenario_exists = c.execute(
        "SELECT scenario_name"
        " FROM scenarios "
        "WHERE scenario_name = '{}';".format(msg["scenarioName"])
    ).fetchone()

    if scenario_exists is not None:
        print("Updating scenario {}".format(msg["scenarioName"]))
        # TODO: need a process for dealing with updating scenarios that have
        #  been run
        update_scenario_multiple_columns(
            io=conn,
            c=c,
            scenario_name=msg["scenarioName"],
            column_values_dict=make_column_values_dict(db_path=db_path, msg=msg),
        )
    else:
        print("Inserting new scenario {}".format(msg["scenarioName"]))
        create_scenario(
            io=conn,
            c=c,
            column_values_dict=make_column_values_dict(db_path=db_path, msg=msg),
        )

    scenario_id = c.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_name = '{}'".format(
            msg["scenarioName"]
        )
    ).fetchone()[0]

    emit("return_new_scenario_id", scenario_id)


def make_column_values_dict(db_path, msg):
    """
    :param db_path: the path to the database
    :param msg: the client message (a dictionary)
    :return: a dictionary of column names and their values for
        populating/upating the scenarios table

    Create a dictionary with column names and their values based on the
    message sent by the client to be used to create a new scenario or update
    an existing one.
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()
    column_values_dict = dict()
    column_values_dict["scenario_name"] = msg["scenarioName"]

    for key in msg.keys():
        if not key == "scenarioName":
            if key == "scenarioDescription":
                column_values_dict["scenario_description"] = msg["scenarioDescription"]
            else:
                id_column, column_value = get_subscenario_id_value(
                    c=c, msg=msg, key=key
                )

                column_values_dict[id_column] = column_value

    return column_values_dict


def get_subscenario_id_value(c, msg, key):
    """
    :param c: the database cursor
    :param msg: the form data sent by Angular, dictionary
    :param key: the key for the values we want to get from the form data
    :return: the name of the column in the scenarios table and its value

    Convert the values in the client message (the subscenario names) to
    their respective subscenario IDs. For features, set to 1 if the message
    value is True and 0 if it is False.
    # TODO: avoid this by setting the ID as 'value' in the form control?
    """
    feature_bool, table, id_column = get_meta_data(c=c, form_key=key)

    # If this key is a feature, get the value directly from the client message
    if feature_bool:
        setting_value = 1 if msg[key] else 0
    # Otherwise, figure out what subscenario_id the value corresponds to
    else:
        # If None (user didn't touch the field) or empty string (user
        # selected the blank field), set to None
        if msg[key] is None or msg[key] == "":
            setting_value = None
        else:
            setting_value = c.execute(
                """SELECT {} FROM {} WHERE name = '{}';""".format(
                    id_column, table, msg[key]
                )
            ).fetchone()[0]

    return id_column, setting_value


def get_meta_data(c, form_key):
    """
    :param c: the database cursor
    :param form_key: the ui_table$ui_table_row key from the client message
    :return: feature_bool, subscenario_table, subscenario_id_column:
        feature_bool is a True/False indicating whether the form_key is for a
        feature column; subscenario_table is the relevant subscenario table
        with the IDs and names for the form_key; subscenario_id_column is the
        name of the column containing the subscenario_id

    Get the metadata for each form key (table-rows in the scenario-new view)
    from the 'ui_scenario_detail_table_row_metadata' table. The form key is
    created by concatenating ui_table, $, and the ui_table_row, so that's
    the rule we use here to separate back into ui_table and ui_table_row.
    """
    sep = form_key.index("$")
    ui_table = form_key[:sep]
    ui_table_row = form_key[sep + 1 :]

    print(ui_table, ui_table_row)
    (subscenario_table, subscenario_id_column) = c.execute(
        """SELECT ui_row_db_subscenario_table,
      ui_row_db_subscenario_table_id_column
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}'
      AND ui_table_row = '{}';""".format(
            ui_table, ui_table_row
        )
    ).fetchone()

    feature_bool = True if ui_table == "features" else False

    return feature_bool, subscenario_table, subscenario_id_column
