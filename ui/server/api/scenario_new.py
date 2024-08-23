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

# ### API: New Scenario Settings ### #

# TODO: need to require setting 'name' column to be unique
# TODO: figure out how to deal with tables with two (or more) subscenario IDs
from db.common_functions import connect_to_database


class ScenarioNewAPI(Resource):
    """ """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        all_tables = c.execute(
            """SELECT ui_table
            FROM ui_scenario_detail_table_metadata
            WHERE include = 1
            ORDER BY ui_table_id ASC;"""
        ).fetchall()

        scenario_new_api = {"allRowIdentifiers": None, "SettingsTables": []}

        for ui_table in all_tables:
            row_identifiers, settings_tables = create_scenario_new_api(
                c=c, ui_table_name_in_db=ui_table[0]
            )
            if scenario_new_api["allRowIdentifiers"] is None:
                scenario_new_api["allRowIdentifiers"] = row_identifiers
            else:
                for row_id in row_identifiers:
                    scenario_new_api["allRowIdentifiers"].append(row_id)
            scenario_new_api["SettingsTables"].append(settings_tables)

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
      WHERE ui_table = '{}'
      AND include = 1;""".format(
            ui_table_name_in_db
        )
    ).fetchone()

    settings_table_api = {
        "uiTableNameInDB": ui_table_name_in_db,
        "tableCaption": table_caption[0],
        "settingRows": [],
    }

    row_metadata = c.execute(
        """SELECT ui_table_row,
      ui_row_caption, ui_row_db_subscenario_table_id_column,
      ui_row_db_subscenario_table
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}'
      AND include = 1;""".format(
            ui_table_name_in_db
        )
    ).fetchall()

    # Keep track of the the row identifiers in a list; we will use the final
    # list in scenario-new instead of hard-coding the identifiers
    all_row_identifiers = []

    for row in row_metadata:
        ui_row_name_in_db = row[0]
        row_caption = row[1]
        row_subscenario_id = row[2]
        row_subscenario_table = row[3]

        row_identifier = ui_table_name_in_db + "$" + ui_row_name_in_db
        all_row_identifiers.append(row_identifier)

        if ui_table_name_in_db == "features":
            setting_options_query = []
        else:
            setting_options_query = c.execute(
                """SELECT {}, name FROM {};""".format(
                    row_subscenario_id, row_subscenario_table
                )
            ).fetchall()

        settings = []
        for setting in setting_options_query:
            if setting_options_query:
                settings.append({"id": setting[0], "name": setting[1]})

        settings_table_api["settingRows"].append(
            {
                "uiRowNameInDB": ui_row_name_in_db,
                "rowName": row_caption,
                "rowFormControlName": row_identifier,
                "settingOptions": settings,
            }
        )

    # Sort the 'Features' table features by caption
    if ui_table_name_in_db == "features":
        sorted_features = sorted(
            settings_table_api["settingRows"], key=lambda k: k["rowName"]
        )
        settings_table_api["settingRows"] = sorted_features

    return all_row_identifiers, settings_table_api
