# Copyright 2026 Sylvan Energy Analytics LLC
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
import sqlite3
import unittest

from gridpath.auxiliary.scenario_chars import SolverOptions

REPO_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSolverOptions(unittest.TestCase):
    def test_integral_values_are_written_as_integers(self):
        """
        Solver option values are stored in a FLOAT column; integer-valued
        options must come back as integers (solvers ignore or reject "4.0"
        for an integer option such as HiGHS's threads), other values as
        they are.
        """
        conn = sqlite3.connect(":memory:")
        with open(os.path.join(REPO_DIRECTORY, "db", "db_schema.sql")) as f:
            conn.executescript(f.read())
        conn.execute(
            "INSERT INTO scenarios (scenario_id, scenario_name, solver_options_id) "
            "VALUES (1, 'test', 7)"
        )
        conn.executemany(
            "INSERT INTO inputs_options_solver (solver_options_id, solver_name, "
            "solver_option_name, solver_option_value) VALUES (7, 'highs', ?, ?)",
            [("threads", 4), ("presolve", "off"), ("mip_rel_gap", 0.001)],
        )

        solver_options = SolverOptions(conn=conn, scenario_id=1)

        self.assertEqual(solver_options.SOLVER_NAME, "highs")
        self.assertEqual(
            solver_options.SOLVER_OPTIONS,
            {"threads": 4, "presolve": "off", "mip_rel_gap": 0.001},
        )
        self.assertIsInstance(solver_options.SOLVER_OPTIONS["threads"], int)
        conn.close()


if __name__ == "__main__":
    unittest.main()
