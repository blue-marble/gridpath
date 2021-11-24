# Copyright 2016-2020 Blue Marble Analytics LLC.
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
Validate a scenario based on input from the UI client.
"""

from gridpath import validate_inputs


def validate_scenario(db_path, client_message):
    """

    :param db_path:
    :param client_message:
    :return:
    """
    scenario_id = str(client_message["scenario"])
    validate_inputs.main(["--database", db_path, "--scenario_id", scenario_id])
