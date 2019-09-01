# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.server.common_functions import connect_to_database


# TODO: add the subscenario names (not just IDs) to the inputs tables --
#  this will make it easier to show the right information to the user
#  without having to resort to JOINS


class ViewDataAPI(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, table, row):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db=table,
            ui_row_name_in_db=row,
            scenario_id=scenario_id
        )


class ViewDataValidation(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        io, c = connect_to_database(db_path=self.db_path)

        scenario_name = c.execute(
          "SELECT scenario_name "
          "FROM scenarios "
          "WHERE scenario_id = {};".format(scenario_id)
        ).fetchone()[0]
        data_table_api = dict()
        data_table_api['ngIfKey'] = "validation"
        data_table_api['caption'] = "{} Validation Errors".format(
          scenario_name)

        column_names, data_rows = get_table_data(
          c=c, input_table='mod_input_validation',
          subscenario_id_column=None, subscenario_id='all',
        )
        data_table_api['columns'] = column_names
        data_table_api['rowsData'] = data_rows

        return data_table_api


def create_data_table_api(
  db_path, ui_table_name_in_db, ui_row_name_in_db, scenario_id
):
    """
    :param db_path:
    :param ui_table_name_in_db:
    :param ui_row_name_in_db:
    :param scenario_id:
    :return:
    """
    # Convert scenario_id to integer, as it's passed as string
    scenario_id = int(scenario_id)

    # Connect to database
    io, c = connect_to_database(db_path=db_path)

    # Make the data table API
    data_table_api = dict()
    data_table_api['ngIfKey'] = ui_table_name_in_db + '-' + ui_row_name_in_db

    row_metadata = c.execute(
      """SELECT ui_row_caption, ui_row_db_input_table, 
      ui_row_db_subscenario_table_id_column
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}' AND ui_table_row = '{}'""".format(
        ui_table_name_in_db, ui_row_name_in_db
      )
    ).fetchone()

    data_table_api['caption'] = row_metadata[0]
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
      subscenario_id=subscenario_id
    )
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


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
        query_where = " WHERE {} = {}".format(
          subscenario_id_column, subscenario_id
        )
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
