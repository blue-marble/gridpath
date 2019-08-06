# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.api.common_functions import connect_to_database


class ScenarioResultsProjectCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='results-project-capacity',
            caption='Project Capacity',
            table='results_project_capacity_all',
            scenario_id=scenario_id
        )


# TODO: common function?
def create_data_table_api(db_path, ngifkey, caption, table, scenario_id):
    """
    :param db_path:
    :param ngifkey:
    :param caption:
    :param table:
    :param scenario_id:
    :return:
    """
    data_table_api = dict()
    data_table_api['ngIfKey'] = ngifkey
    data_table_api['caption'] = caption
    column_names, data_rows = get_table_data(
      db_path=db_path,
      table=table,
      scenario_id=scenario_id
    )
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


def get_table_data(db_path, table, scenario_id):
    """
    :param db_path:
    :param table:
    :param scenario_id:
    :return:
    """
    io, c = connect_to_database(db_path=db_path)

    table_data_query = c.execute(
      """SELECT * FROM {} 
         WHERE scenario_id = {};""".format(table, scenario_id))

    column_names = [s[0] for s in table_data_query.description]

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    return column_names, rows_data
