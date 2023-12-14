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


# ### API: Scenarios List ### #
class Scenarios(Resource):
    """
    The list of scenarios.
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        scenarios_query = c.execute(
            """SELECT scenario_id, scenario_name, validation_status, run_status
            FROM scenarios_view
            ORDER by scenario_id ASC;"""
        )

        scenarios_api = []
        for s in scenarios_query:
            # TODO: make this more robust than relying on column order
            scenarios_api.append(
                {"id": s[0], "name": s[1], "validationStatus": s[2], "runStatus": s[3]}
            )

        return scenarios_api
