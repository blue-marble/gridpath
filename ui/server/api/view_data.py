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


class ViewDataAPI(Resource):
    """ """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, table):
        """

        :return:
        """
        print(scenario_id, table)

        return get_table_data(
            scenario_id=scenario_id,
            other_scenarios=[],  # todo: does this break anything
            table=table,
            db_path=self.db_path,
        )


def get_table_data(scenario_id, other_scenarios, table, db_path):
    """

    :param scenario_id:
    :param other_scenarios:
    :param table:
    :param db_path:
    :return:
    """

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    query_for_column_names = c.execute("""SELECT * FROM {} LIMIT 1;""".format(table))

    column_names = [s[0] for s in query_for_column_names.description]

    for index, value in enumerate(column_names):
        if value == "scenario_id":
            column_names[index] = "scenario_name"

    columns_for_query = str()
    n = 1
    for column in column_names:
        if n < len(column_names):
            columns_for_query += "{}, ".format(column)
        else:
            columns_for_query += "{}".format(column)
        n += 1

    other_scenarios_string = str()
    if len(other_scenarios) > 0:
        for scenario in other_scenarios:
            other_scenarios_string += ", {}".format(scenario)

    table_data_query = c.execute(
        """
      SELECT {}
      FROM {}
      JOIN scenarios USING (scenario_id)
      WHERE scenario_id in ({}{});
      """.format(
            columns_for_query, table, scenario_id, other_scenarios_string
        )
    )

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    data_table_api = {"columns": column_names, "rowsData": rows_data}

    return data_table_api
