# Copyright 2026 Sylvan Energy Analytics LLC.
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
Validation of specified transmission capacities against an in-memory
database built from the real schema: an unspecified (NULL) min_mw or max_mw
means "no flow limit in that direction" and is accepted, except where the
line carries a fixed cost or is of the tx_simple_binary operational type.
"""

import os
import sqlite3
import unittest

from gridpath.transmission.capacity.capacity_types.tx_spec import validate_inputs

DB_SCHEMA = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "db", "db_schema.sql"
)

TEMPORAL_SCENARIO_ID = 1
PORTFOLIO_SCENARIO_ID = 1
OPCHAR_SCENARIO_ID = 1
CAPACITY_SCENARIO_ID = 1
PERIOD = 2020
SUBPROBLEM = 1
STAGE = 1


class SubScenarios(object):
    """Stand-in for the SubScenarios object the module reads IDs from."""

    TEMPORAL_SCENARIO_ID = TEMPORAL_SCENARIO_ID
    TRANSMISSION_PORTFOLIO_SCENARIO_ID = PORTFOLIO_SCENARIO_ID
    TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID = OPCHAR_SCENARIO_ID
    TRANSMISSION_SPECIFIED_CAPACITY_SCENARIO_ID = CAPACITY_SCENARIO_ID


class TestTxSpecValidation(unittest.TestCase):
    """ """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        with open(DB_SCHEMA) as f:
            self.conn.executescript(f.read())
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO inputs_temporal_periods (temporal_scenario_id, period) "
            "VALUES (?, ?)",
            (TEMPORAL_SCENARIO_ID, PERIOD),
        )
        c.execute(
            """INSERT INTO inputs_temporal
            (temporal_scenario_id, subproblem_id, stage_id, timepoint, period,
             number_of_hours_in_timepoint, timepoint_weight, spinup_or_lookahead)
            VALUES (?, ?, ?, 1, ?, 1, 1, 0)""",
            (TEMPORAL_SCENARIO_ID, SUBPROBLEM, STAGE, PERIOD),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def add_line(self, tx, operational_type, min_mw, max_mw, fixed_cost=None):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO inputs_transmission_portfolios "
            "(transmission_portfolio_scenario_id, transmission_line, capacity_type) "
            "VALUES (?, ?, 'tx_spec')",
            (PORTFOLIO_SCENARIO_ID, tx),
        )
        c.execute(
            "INSERT INTO inputs_transmission_operational_chars "
            "(transmission_operational_chars_scenario_id, transmission_line, "
            "operational_type) VALUES (?, ?, ?)",
            (OPCHAR_SCENARIO_ID, tx, operational_type),
        )
        c.execute(
            "INSERT INTO inputs_transmission_specified_capacity "
            "(transmission_specified_capacity_scenario_id, transmission_line, "
            "period, min_mw, max_mw, fixed_cost_per_mw_yr) VALUES (?, ?, ?, ?, ?, ?)",
            (CAPACITY_SCENARIO_ID, tx, PERIOD, min_mw, max_mw, fixed_cost),
        )
        self.conn.commit()

    def validation_errors(self):
        validate_inputs(
            scenario_id=1,
            subscenarios=SubScenarios(),
            weather_iteration=0,
            hydro_iteration=0,
            availability_iteration=0,
            subproblem=SUBPROBLEM,
            stage=STAGE,
            conn=self.conn,
        )
        return [
            row[0]
            for row in self.conn.cursor().execute(
                "SELECT description FROM status_validation"
            )
        ]

    def test_unspecified_capacity_is_accepted(self):
        self.add_line("Tx_Open", "tx_simple", None, None)
        self.add_line("Tx_One_Way", "tx_simple", -10, None, fixed_cost=0)
        self.assertListEqual(self.validation_errors(), [])

    def test_fixed_cost_requires_both_capacities(self):
        self.add_line("Tx_Costed", "tx_simple", -10, None, fixed_cost=5)
        errors = self.validation_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("Tx_Costed", errors[0])
        self.assertIn("fixed_cost_per_mw_yr", errors[0])

    def test_binary_lines_must_specify_both_capacities(self):
        self.add_line("Tx_Binary", "tx_simple_binary", None, 10)
        self.add_line("Tx_Binary_OK", "tx_simple_binary", -10, 10)
        errors = self.validation_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("Tx_Binary", errors[0])
        self.assertIn("tx_simple_binary", errors[0])

    def test_min_above_max_is_flagged_by_line(self):
        self.add_line("Tx_Inverted", "tx_simple", 10, -10)
        errors = self.validation_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("Tx_Inverted", errors[0])


if __name__ == "__main__":
    unittest.main()
