# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.api.common_functions import connect_to_database


# ### API: Scenario Detail ### #
class ScenarioDetailAPI(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        io, c = connect_to_database(db_path=self.db_path)
        all_tables = c.execute(
            """SELECT ui_table 
            FROM ui_scenario_detail_table_metadata
            ORDER BY ui_table_id ASC;"""
        ).fetchall()

        scenario_detail_api = list()

        for ui_table in all_tables:
            scenario_detail_api.append(
                get_scenario_detail(
                  cursor=c,
                  scenario_id=scenario_id,
                  ui_table_name_in_db=ui_table[0]
                )
            )

        return scenario_detail_api


class ScenarioDetailAll(Resource):
    """
    All selections for a scenario.
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        io, c = connect_to_database(db_path=self.db_path)
        scenario_detail_query = c.execute(
            "SELECT * "
            "FROM scenarios_view "
            "WHERE scenario_id = {}".format(scenario_id)
        )

        column_names = [s[0] for s in scenario_detail_query.description]
        column_values = list(list(scenario_detail_query)[0])
        scenario_detail_api = dict(zip(column_names, column_values))

        return scenario_detail_api


class ScenarioDetailName(Resource):
    """
    The name of the a scenario by scenario ID
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        io, c = connect_to_database(db_path=self.db_path)
        scenario_name = c.execute(
            "SELECT scenario_name "
            "FROM scenarios "
            "WHERE scenario_id = {}".format(scenario_id)
        ).fetchone()[0]

        return scenario_name


def get_scenario_detail(cursor, scenario_id, ui_table_name_in_db):
    """
    :param cursor: the database cursor
    :param scenario_id: integer, the scenario ID
    :param ui_table_name_in_db:
    :return:


    """
    c = cursor

    # Get and set the table caption for this table
    table_caption = c.execute(
        """SELECT ui_table, ui_table_caption 
        FROM ui_scenario_detail_table_metadata
        WHERE ui_table = '{}';""".format(ui_table_name_in_db)
    ).fetchone()

    scenario_detail_api = dict()
    scenario_detail_api["uiTableNameInDB"] = table_caption[0]
    scenario_detail_api["scenarioDetailTableCaption"] = table_caption[1]

    # Get the metadata and value for the rows
    scenario_detail_api["scenarioDetailTableRows"] = list()

    row_metadata = c.execute(
        """SELECT ui_table_row, ui_row_caption, ui_row_db_scenarios_view_column, 
        ui_row_db_input_table 
        FROM ui_scenario_detail_table_row_metadata
        WHERE ui_table = '{}'""".format(ui_table_name_in_db)
    ).fetchall()

    for row in row_metadata:
        row_value = c.execute(
            """SELECT {}
              FROM scenarios_view
              WHERE scenario_id = {}""".format(row[2], scenario_id)
        ).fetchone()[0]

        scenario_detail_api["scenarioDetailTableRows"].append({
            'uiRowNameInDB': row[0],
            'rowCaption': row[1],
            'rowValue': row_value,
            'inputTable':  row[3]
        })

    return scenario_detail_api
