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

import datetime
from flask_restful import Resource

from db.common_functions import connect_to_database
from gridpath.common_functions import string_from_time
from gridpath.auxiliary.scenario_chars import SolverOptions


# ### API: Scenario Detail ### #
class ScenarioDetailAPI(Resource):
    """ """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        scenario_detail_api = dict()

        # Get the scenario name
        [
            scenario_name,
            scenario_description,
            validation_status,
            run_status,
            run_process_id,
            run_start_time,
            run_end_time,
        ] = c.execute(
            """
          SELECT scenarios.scenario_name, scenarios.scenario_description,
            scenarios_view.validation_status,
            scenarios_view.run_status,
            scenarios.run_process_id,
            scenarios.run_start_time,
            scenarios.run_end_time
          FROM scenarios
          JOIN scenarios_view
            USING (scenario_id)
          WHERE scenario_id = {}
          """.format(
                scenario_id
            )
        ).fetchone()

        scenario_detail_api["scenarioName"] = scenario_name
        scenario_detail_api["scenarioDescription"] = scenario_description
        scenario_detail_api["validationStatus"] = validation_status
        scenario_detail_api["runStatus"] = run_status
        scenario_detail_api["runPID"] = run_process_id
        # Format for to match logfile name
        scenario_detail_api["runStartTime"] = (
            ""
            if run_start_time is None
            else string_from_time(
                datetime.datetime.strptime(run_start_time, "%Y-%m-%d %H:%M:%S.%f")
            )
        )
        scenario_detail_api["runEndTime"] = "" if run_end_time is None else run_end_time
        scenario_detail_api["runElapsedTime"] = (
            ""
            if run_start_time is None
            else str(
                datetime.datetime.now()
                - datetime.datetime.strptime(run_start_time, "%Y-%m-%d %H:%M:%S.%f")
            )
        )

        # TODO: should probably specify the default solver somewhere in the
        #  code and use that parameter here
        scenario_detail_api["solver"] = (
            "cbc"
            if SolverOptions(conn=conn, scenario_id=scenario_id).SOLVER_NAME is None
            else SolverOptions(conn=conn, scenario_id=scenario_id).SOLVER_NAME
        )

        # Get the UI table structure and make a dictionary of scenarios_view
        # columns with their ui_table_name_in_db and ui_table_row_name_in_db
        # Also keep track of which scenario_view columns the UI is requesting
        ui_table_row_by_view_column = dict()
        relevant_scenarios_view_columns = list()
        for row in c.execute(
            """SELECT ui_table, ui_table_row, ui_row_db_scenarios_view_column
          FROM ui_scenario_detail_table_row_metadata
          WHERE include = 1;"""
        ).fetchall():
            ui_table_row_by_view_column[row[2]] = row[0] + "$" + row[1]
            relevant_scenarios_view_columns.append(row[2])

        # Get the values for scenario-edit
        scenario_edit_query = c.execute(
            "SELECT * "
            "FROM scenarios_view "
            "WHERE scenario_id = {}".format(scenario_id)
        )

        column_names = [s[0] for s in scenario_edit_query.description]
        column_values = list(list(scenario_edit_query)[0])

        # TODO: more robust way to do this than to rely on the column name
        #  starting with feature?
        # Replace feature columns yes/no's with booleans (for the checkboxes
        # when editing a scenario)
        for n in column_names:
            if n.startswith("feature"):
                index = column_names.index(n)
                column_values[index] = True if column_values[index] == "yes" else False

        scenario_edit_api_all = dict(zip(column_names, column_values))
        scenario_edit_api = dict()

        # We'll need scenario ID and name, which we add separately as they
        # are not in the ui_scenario_detail_table_row_metadata table
        for base_column in ["scenario_id", "scenario_name", "scenario_description"]:
            scenario_edit_api[base_column] = scenario_edit_api_all[base_column]

        # Add only columns requested by the UI to the final scenario-edit API
        for column in relevant_scenarios_view_columns:
            if column in scenario_edit_api_all.keys():
                scenario_edit_api[ui_table_row_by_view_column[column]] = (
                    scenario_edit_api_all[column]
                )

        # Add the edit API to the general scenario-detail API
        scenario_detail_api["editScenarioValues"] = scenario_edit_api

        all_tables = c.execute(
            """SELECT ui_table
            FROM ui_scenario_detail_table_metadata
            WHERE include = 1
            ORDER BY ui_table_id ASC;"""
        ).fetchall()

        scenario_detail_api["scenarioDetailTables"] = list()

        for ui_table in all_tables:
            scenario_detail_api["scenarioDetailTables"].append(
                get_scenario_detail(
                    cursor=c, scenario_id=scenario_id, ui_table_name_in_db=ui_table[0]
                )
            )

        return scenario_detail_api


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
        WHERE ui_table = '{}'
        AND include = 1;""".format(
            ui_table_name_in_db
        )
    ).fetchone()

    scenario_detail_table_api = dict()
    scenario_detail_table_api["uiTableNameInDB"] = table_caption[0]
    scenario_detail_table_api["scenarioDetailTableCaption"] = table_caption[1]

    # Get the metadata and value for the rows
    scenario_detail_table_api["scenarioDetailTableRows"] = list()

    row_metadata = c.execute(
        """SELECT ui_table_row, ui_row_caption,
        ui_row_db_scenarios_view_column, ui_row_db_input_table
        FROM ui_scenario_detail_table_row_metadata
        WHERE ui_table = '{}'
        AND include = 1;""".format(
            ui_table_name_in_db
        )
    ).fetchall()

    for row in row_metadata:
        row_value = c.execute(
            """SELECT {}
                FROM scenarios_view
                WHERE scenario_id = {}""".format(
                row[2], scenario_id
            )
        ).fetchone()[0]
        # Replace yes/no with booleans in 'Features' table, so that we can
        # create checkboxes
        if table_caption[1] == "Features":
            if row_value == "yes":
                row_value = True
            else:
                row_value = False

        scenario_detail_table_api["scenarioDetailTableRows"].append(
            {
                "uiRowNameInDB": row[0],
                "rowCaption": row[1],
                "rowValue": row_value,
                "inputTable": row[3],
            }
        )

    # Sort the 'Features' table features by caption
    if ui_table_name_in_db == "features":
        sorted_features = sorted(
            scenario_detail_table_api["scenarioDetailTableRows"],
            key=lambda k: k["rowCaption"],
        )
        scenario_detail_table_api["scenarioDetailTableRows"] = sorted_features

    return scenario_detail_table_api
