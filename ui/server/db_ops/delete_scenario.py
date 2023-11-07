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

"""
Clear scenario results/statuses or delete scenario completely based on input
from the UI client.
"""

from db.utilities.scenario import delete_scenario_results_and_status, delete_scenario
from db.common_functions import connect_to_database


def clear(db_path, scenario_id):
    """

    :param db_path:
    :param scenario_id:
    :return:
    """
    conn = connect_to_database(db_path=db_path)
    delete_scenario_results_and_status(conn=conn, scenario_id=scenario_id)


def delete(db_path, scenario_id):
    """

    :param db_path:
    :param scenario_id:
    :return:
    """
    conn = connect_to_database(db_path=db_path)
    delete_scenario(conn=conn, scenario_id=scenario_id)
