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

"""
The project-level default_exogenous_availability: it replaces 1 as the
outage timepoint derate where the project has no timepoint-level
outage derate, explicit timepoint rows take precedence, and the other
derates still multiply it.
"""

import os.path
import shutil
import sqlite3
import tempfile
import unittest

import pandas as pd

from gridpath.project.availability.availability_types import exogenous
from tests.common_functions import add_components_and_load_data
from tests.project.availability.availability_types.test_exogenous import (
    IMPORTED_PREREQ_MODULES,
    MODULE_BEING_TESTED,
    TEST_DATA_DIRECTORY,
)

DB_SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "db", "db_schema.sql"
)


class TestExogenousDefaultModel(unittest.TestCase):
    """
    Copies the unit-test fixture and adds project defaults for Coal (which
    has timepoint-level outage derates) and Wind (which has none).
    """

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.test_data_dir = os.path.join(self.tmp_dir.name, "test_data")
        shutil.copytree(TEST_DATA_DIRECTORY, self.test_data_dir)
        pd.DataFrame(
            {"project": ["Coal", "Wind"], "default_exogenous_availability": [0.8, 0.9]}
        ).to_csv(
            os.path.join(
                self.test_data_dir, "inputs", exogenous.DEFAULT_DERATE_FILENAME
            ),
            sep="\t",
            index=False,
        )

    def get_instance(self):
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=self.test_data_dir,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        return m.create_instance(data)

    def test_outage_derate_falls_back_to_default(self):
        instance = self.get_instance()
        explicit = pd.read_csv(
            os.path.join(
                self.test_data_dir,
                "inputs",
                "project_availability_exogenous_outage.tab",
            ),
            sep="\t",
        )
        explicit_derates = {
            (p, tmp): d
            for p, tmp, d in zip(
                explicit.project,
                explicit.timepoint,
                explicit.availability_derate_outage,
            )
        }
        defaults = {"Coal": 0.8, "Wind": 0.9}

        expected = {
            (p, tmp): explicit_derates.get((p, tmp), defaults.get(p, 1))
            for (p, tmp) in instance.AVL_EXOG_OPR_TMPS
        }
        actual = {
            (p, tmp): instance.avl_exog_cap_derate_outage[p, tmp]
            for (p, tmp) in instance.AVL_EXOG_OPR_TMPS
        }
        self.assertDictEqual(expected, actual)

        # The fixture exercises all three cases: default only, explicit rows
        # over a default, and no default
        wind_tmps = [tmp for (p, tmp) in instance.AVL_EXOG_OPR_TMPS if p == "Wind"]
        self.assertTrue(wind_tmps)
        self.assertTrue(all(actual["Wind", tmp] == 0.9 for tmp in wind_tmps))
        self.assertTrue(any(p == "Coal" for (p, _) in explicit_derates))
        self.assertTrue(any(p not in defaults for (p, _) in instance.AVL_EXOG_OPR_TMPS))

    def test_other_derates_multiply_the_default(self):
        instance = self.get_instance()
        for p, tmp in instance.AVL_EXOG_OPR_TMPS:
            expected = (
                instance.avl_exog_cap_derate_outage[p, tmp]
                * instance.avl_exog_cap_derate_weather[p, tmp]
                * instance.avl_exog_cap_derate_weather_bt_hrz_by_tmp[p, tmp]
                * instance.avl_exog_cap_derate_outage_bt_hrz_by_tmp[p, tmp]
                * instance.avl_exog_mnth_derate[p, instance.month[tmp]]
            )
            self.assertAlmostEqual(
                exogenous.availability_derate_cap_rule(instance, p, tmp), expected
            )
        wind_tmp = next(tmp for (p, tmp) in instance.AVL_EXOG_OPR_TMPS if p == "Wind")
        self.assertAlmostEqual(
            exogenous.availability_derate_cap_rule(instance, "Wind", wind_tmp)
            / (
                instance.avl_exog_cap_derate_weather["Wind", wind_tmp]
                * instance.avl_exog_cap_derate_weather_bt_hrz_by_tmp["Wind", wind_tmp]
                * instance.avl_exog_cap_derate_outage_bt_hrz_by_tmp["Wind", wind_tmp]
                * instance.avl_exog_mnth_derate["Wind", instance.month[wind_tmp]]
            ),
            0.9,
        )

    def test_hybrid_storage_derate_unaffected(self):
        instance = self.get_instance()
        for p, tmp in instance.AVL_EXOG_OPR_TMPS:
            if p in ("Coal", "Wind"):
                self.assertNotIn(
                    (p, tmp),
                    list(instance.avl_exog_hyb_stor_cap_derate_outage.sparse_keys()),
                )
                self.assertEqual(
                    instance.avl_exog_hyb_stor_cap_derate_outage[p, tmp], 1
                )


class SubScenarios:
    """Scenario subscenario IDs; unset IDs are "NULL" as in the database"""

    TEMPORAL_SCENARIO_ID = 1
    PROJECT_PORTFOLIO_SCENARIO_ID = 1
    PROJECT_AVAILABILITY_SCENARIO_ID = 1

    def __getattr__(self, name):
        return "NULL"


class TestExogenousDefaultDatabase(unittest.TestCase):
    """
    The default rows the database query selects: exogenous portfolio
    projects with a non-NULL default only.
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        with open(DB_SCHEMA_FILE) as f:
            self.conn.executescript(f.read())
        self.conn.executemany(
            "INSERT INTO inputs_project_portfolios "
            "(project_portfolio_scenario_id, project) VALUES (1, ?)",
            [("A",), ("B",), ("C",), ("D",)],
        )
        self.conn.executemany(
            "INSERT INTO inputs_project_availability "
            "(project_availability_scenario_id, project, availability_type, "
            "default_exogenous_availability) VALUES (?, ?, ?, ?)",
            [
                (1, "A", "exogenous", 0.9),
                # No default
                (1, "B", "exogenous", None),
                # Not exogenous
                (1, "C", "binary", 0.5),
                # Not in the portfolio
                (1, "E", "exogenous", 0.7),
                # Other availability scenario
                (2, "D", "exogenous", 0.6),
            ],
        )

    def test_default_rows(self):
        default_rows = exogenous.get_inputs_from_database(
            scenario_id=1,
            subscenarios=SubScenarios(),
            weather_iteration=0,
            hydro_iteration=0,
            availability_iteration=0,
            subproblem=1,
            stage=1,
            conn=self.conn,
        )[-1].fetchall()
        self.assertListEqual(default_rows, [("A", 0.9)])


if __name__ == "__main__":
    unittest.main()
