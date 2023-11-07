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

from flask_restful import Resource

from db.common_functions import connect_to_database


# TODO: add the subscenario names (not just IDs) to the inputs tables --
#  this will make it easier to show the right information to the user
#  without having to resort to JOINS


class ScenarioInputs(Resource):
    """ """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, table_type, table, row):
        """

        :return:
        """
        return create_input_data_table_api(
            db_path=self.db_path,
            table_type=table_type,
            ui_table_name_in_db=table,
            ui_row_name_in_db=row,
            scenario_id=scenario_id,
        )


def create_input_data_table_api(
    db_path, table_type, ui_table_name_in_db, ui_row_name_in_db, scenario_id
):
    """
    :param db_path:
    :param table_type:
    :param ui_table_name_in_db:
    :param ui_row_name_in_db:
    :param scenario_id:
    :return:
    """
    # Convert scenario_id to integer, as it's passed as string
    scenario_id = int(scenario_id)

    # Connect to database
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    # Make the data table API
    data_table_api = dict()

    row_metadata = c.execute(
        """SELECT ui_row_caption, ui_row_db_{}_table,
      ui_row_db_subscenario_table_id_column
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}' AND ui_table_row = '{}'""".format(
            table_type, ui_table_name_in_db, ui_row_name_in_db
        )
    ).fetchone()

    data_table_api["caption"] = row_metadata[0]
    input_table = row_metadata[1]
    subscenario_id_column = row_metadata[2]

    # Get the subscenario_id for the scenario
    if scenario_id == 0:
        subscenario_id = "all"
    else:
        subscenario_id = c.execute(
            """SELECT {} FROM scenarios WHERE scenario_id = {}""".format(
                subscenario_id_column, scenario_id
            )
        ).fetchone()[0]

    column_names, data_rows = get_table_data(
        c=c,
        input_table=input_table,
        subscenario_id_column=subscenario_id_column,
        subscenario_id=subscenario_id,
    )
    data_table_api["columns"] = column_names
    data_table_api["rowsData"] = data_rows

    return data_table_api


# TODO: this can probably be refactored to consolidate with the
#  get_table_data function from view-data
def get_table_data(c, input_table, subscenario_id_column, subscenario_id):
    """
    :param c:
    :param input_table:
    :param subscenario_id_column:
    :param subscenario_id:
    :return:
    """
    if subscenario_id == "all":
        query_where = ""
    else:
        query_where = " WHERE {} = {}".format(subscenario_id_column, subscenario_id)
    table_data_query = c.execute(
        """SELECT * FROM {}{};""".format(input_table, query_where)
    )

    column_names = [s[0] for s in table_data_query.description]

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    return column_names, rows_data
