# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.server.common_functions import connect_to_database


class ViewDataAPI(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, table):
        """

        :return:
        """
        print(scenario_id, table)
        io, c = connect_to_database(db_path=self.db_path)

        table_data_query = c.execute(
          """SELECT * FROM {} WHERE scenario_id = {}""".format(
            table, scenario_id
          )
        )

        column_names = [s[0] for s in table_data_query.description]

        rows_data = []
        for row in table_data_query.fetchall():
            row_values = list(row)
            row_dict = dict(zip(column_names, row_values))
            rows_data.append(row_dict)


        data_table_api = {
            'columns': column_names,
            'rowsData': rows_data
        }

        return data_table_api
