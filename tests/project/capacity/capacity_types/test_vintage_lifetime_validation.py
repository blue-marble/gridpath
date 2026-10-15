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
New-build lifetimes are checked against the boundaries of the periods on
each vintage's trajectory: a lifetime that covers no period is a High
finding, one ending partway through a period a Low finding.
"""

import os.path
import sqlite3
import unittest

from gridpath.project.capacity.capacity_types.common_methods import (
    validate_vintage_lifetimes,
    vintage_lifetime_period_findings,
)

DB_SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "db", "db_schema.sql"
)

# Uneven periods with a gap between 2030 and 2035: (period, start, end,
# prev_period)
UNEVEN_PERIODS = [
    (2020, 2020, 2025, None),
    (2025, 2025, 2030, None),
    (2035, 2035, 2045, None),
]


class TestVintageLifetimePeriodFindings(unittest.TestCase):
    def test_uneven_periods(self):
        """
        * A: 5 years from 2020 end at the 2020/2025 boundary
        * B: 7 years from 2020 end partway through 2025, after 2 years
        * C: 12 years from 2020 end in the gap between 2030 and 2035
        * D: 20 years from 2020 end partway through 2035, after 5 years
        * E: 30 years from 2020 end after the last period
        * F: 3 years from 2020 end before the end of 2020
        * G: 4.9999999 years from 2020 are at the boundary within the
          tolerance
        """
        no_period, cut_short = vintage_lifetime_period_findings(
            periods=UNEVEN_PERIODS,
            vintage_lifetimes=[
                ("A", 2020, 5),
                ("B", 2020, 7),
                ("C", 2020, 12),
                ("D", 2020, 20),
                ("E", 2020, 30),
                ("F", 2020, 3),
                ("G", 2020, 4.9999999),
                ("H", 2050, 3),
                ("I", 2020, None),
            ],
        )
        self.assertListEqual([("F", 2020, 3)], no_period)
        self.assertListEqual([("B", 2020, 2025, 2), ("D", 2020, 2035, 5)], cut_short)

    def test_scenario_tree_branches(self):
        """
        Branch 20301 is 5 years long and branch 20302 20 years: a 15-year
        lifetime of the 2020 vintage (A) ends at the end of 20301 but partway
        through 20302. A 15-year lifetime of the 20301 vintage (B) ends in
        2045, which would be inside 20302, but 20302 is not on B's
        trajectory.
        """
        periods = [
            (2020, 2020, 2030, None),
            (20301, 2030, 2035, 2020),
            (20302, 2030, 2050, 2020),
        ]
        no_period, cut_short = vintage_lifetime_period_findings(
            periods=periods,
            vintage_lifetimes=[("A", 2020, 15), ("B", 20301, 15)],
        )
        self.assertListEqual([], no_period)
        self.assertListEqual([("A", 2020, 20302, 5)], cut_short)


class SubScenariosStub:
    PROJECT_PORTFOLIO_SCENARIO_ID = 1
    PROJECT_NEW_COST_SCENARIO_ID = 1
    TEMPORAL_SCENARIO_ID = 1


class TestValidateVintageLifetimes(unittest.TestCase):
    """
    Periods 2020 and 2030 (20 years each, 2020-2060); gen_new_lin projects:

    * Good: 40-year operational and 20-year financial lifetimes
    * Free: a 10-year financial lifetime, which covers no period
    * Cut: a 30-year operational lifetime, which ends 10 years into 2040's
      period
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        with open(DB_SCHEMA_FILE) as f:
            self.conn.executescript(f.read())
        c = self.conn.cursor()
        for period in [2020, 2040]:
            c.execute(
                """INSERT INTO inputs_temporal_periods
                (temporal_scenario_id, period, discount_factor,
                period_start_year, period_end_year)
                VALUES (1, ?, 1, ?, ?)""",
                (period, period, period + 20),
            )
            c.execute(
                """INSERT INTO inputs_temporal
                (temporal_scenario_id, subproblem_id, stage_id, timepoint,
                period, number_of_hours_in_timepoint, timepoint_weight,
                spinup_or_lookahead)
                VALUES (1, 1, 1, ?, ?, 1, 8760, 0)""",
                (period * 100 + 1, period),
            )
        rows = [("Good", 40, 20), ("Free", 40, 10), ("Cut", 30, 20)]
        c.executemany(
            """INSERT INTO inputs_project_portfolios
            (project_portfolio_scenario_id, project, capacity_type)
            VALUES (1, ?, 'gen_new_lin')""",
            [(prj,) for prj, _, _ in rows],
        )
        c.executemany(
            """INSERT INTO inputs_project_new_cost
            (project_new_cost_scenario_id, project, vintage,
            operational_lifetime_yrs, financial_lifetime_yrs)
            VALUES (1, ?, 2020, ?, ?)""",
            rows,
        )
        self.conn.commit()

    def test_findings_written_to_validation_table(self):
        validate_vintage_lifetimes(
            conn=self.conn,
            scenario_id=1,
            subscenarios=SubScenariosStub(),
            weather_iteration=0,
            hydro_iteration=0,
            availability_iteration=0,
            subproblem=1,
            stage=1,
            gridpath_module="test",
            capacity_type="gen_new_lin",
        )
        findings = self.conn.execute(
            """SELECT severity, description FROM status_validation
            ORDER BY severity, description"""
        ).fetchall()
        self.assertEqual(2, len(findings))
        (high_severity, high), (low_severity, low) = findings
        self.assertEqual("High", high_severity)
        self.assertIn("Financial lifetime", high)
        self.assertIn("('Free', 2020, 10.0)", high)
        self.assertEqual("Low", low_severity)
        self.assertIn("Operational lifetime", low)
        self.assertIn("('Cut', 2020, 2040, 10.0)", low)


if __name__ == "__main__":
    unittest.main()
