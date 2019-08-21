# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

# ### API: New Scenario Settings ### #

# TODO: need to require setting 'name' column to be unique
# TODO: figure out how to deal with tables with two (or more) subscenario IDs
from ui.server.common_functions import connect_to_database


class ScenarioNewAPI(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        io, c = connect_to_database(db_path=self.db_path)
        all_tables = c.execute(
            """SELECT ui_table 
            FROM ui_scenario_detail_table_metadata
            ORDER BY ui_table_id ASC;"""
        ).fetchall()

        scenario_new_api = list()

        for ui_table in all_tables:
            scenario_new_api.append(
                create_scenario_new_api(
                    c=c,
                    ui_table_name_in_db=ui_table[0]
                )
            )

        return scenario_new_api


def create_scenario_new_api(c, ui_table_name_in_db):
    """
    :param c: the database cursor
    :param ui_table_name_in_db:
    :return:
    """
    # Get and set the table caption for this table
    table_caption = c.execute(
      """SELECT ui_table_caption 
      FROM ui_scenario_detail_table_metadata
      WHERE ui_table = '{}';""".format(ui_table_name_in_db)
    ).fetchone()

    scenario_new_api = {
      "uiTableNameInDB": ui_table_name_in_db,
      "tableCaption": table_caption[0],
      "settingRows": []
    }

    row_metadata = c.execute(
      """SELECT ui_table_row, 
      ui_row_caption, ui_row_db_subscenario_table_id_column, 
      ui_row_db_subscenario_table
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}';""".format(
        ui_table_name_in_db
      )
    ).fetchall()

    for row in row_metadata:
        ui_row_name_in_db = row[0]
        row_caption = row[1]
        row_subscenario_id = row[2]
        row_subscenario_table = row[3]

        if ui_table_name_in_db == 'features':
            setting_options_query = []
        else:
            setting_options_query = c.execute(
                """SELECT {}, name FROM {};""".format(
                  row_subscenario_id, row_subscenario_table
                )
            ).fetchall()

        settings = []
        for setting in setting_options_query:
            if not setting_options_query:
                pass
            else:
                settings.append(
                    {'id': setting[0], 'name': setting[1]}
                )

        scenario_new_api["settingRows"].append({
          "uiRowNameInDB": ui_row_name_in_db,
          "rowName": row_caption,
          "rowFormControlName": ui_table_name_in_db + "$" + ui_row_name_in_db,
          "settingOptions": settings
        })

    # Sort the 'Features' table features by caption
    if ui_table_name_in_db == "features":
        sorted_features = \
            sorted(scenario_new_api["settingRows"],
                   key=lambda k: k['rowName'])
        scenario_new_api["settingRows"] = sorted_features

    return scenario_new_api
