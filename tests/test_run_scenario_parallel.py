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

import os
import unittest

from gridpath import run_scenario_parallel

# Change directory to the 'gridpath' directory as that's what
# run_scenario_parallel.py expects; the rest of the variables are relative
# paths from there
os.chdir(os.path.join(os.path.dirname(__file__), "../gridpath"))


class TestRunScenarioParallel(unittest.TestCase):
    def test_parallel_scenarios(self):
        scenarios_csv_path = os.path.join(
            os.getcwd(), "../tests/test_data/scenarios_to_run.csv"
        )
        run_scenario_parallel.main(
            ["--scenarios_csv", scenarios_csv_path, "--n_parallel_scenarios", "2"]
        )


if __name__ == "__main__":
    unittest.main()
