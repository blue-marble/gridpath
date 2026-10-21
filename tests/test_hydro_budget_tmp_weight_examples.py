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
Differential test for hydro energy budgets on horizons whose timepoints
carry different weights. The compact example represents a year with one
circular 'day' horizon holding a peak day (weight 1) and a median day
(weight 364); its expanded twin spells the same year out as the peak day
followed by 364 explicit, identical median days (all weights 1) in one
horizon. Because the energy budget weights each timepoint by hours x
timepoint weight, the two must agree:

* identical objective function values;
* the compact example's hydro output, weighted, equals its budget, i.e.
  the average power fraction x capacity x 8760 h, and the model still
  moves energy toward the peak day within the min/max fractions;
* the twin's hydro energy equals the same budget.

Without the weights the compact example constrains only the unweighted
average output, and the optimizer moves hydro energy from the peak day to
the median day and delivers far more represented energy than the budget
(objective -11.8M instead of -19.4M, measured before the fix).

The twin equality needs every other objective term to be linear in the
timepoint weight as well, which is why the example's gas units carry no
startup or shutdown costs: a commitment change between the two days is
charged once per timepoint weight in the compact example but once in the
twin, a representative-day artifact unrelated to the budget.

The scenarios are solved into a temporary directory so that the committed
example directories are not touched.
"""

import os
import shutil
import tempfile
import unittest

import pandas as pd

from db import create_database
from db.utilities import port_csvs_to_db, scenario
from gridpath import run_end_to_end

REPO_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_TEMPLATE_ENV_VAR = "GRIDPATH_TEST_EXAMPLES_DB_TEMPLATE"

COMPACT = "hydro_budget_w_mixed_tmp_weights"
EXPANDED_TWIN = "hydro_budget_w_mixed_tmp_weights_expanded_twin"
PEAK_DAY_TMP = 2020001
MEDIAN_DAY_TMP = 2020001 + 1
HYDRO_CAPACITY_MW = 6
HYDRO_AVERAGE_POWER_FRACTION = 0.5
HOURS_IN_YEAR = 8760


class TestHydroBudgetTimepointWeightExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "examples.db")
        cls.scenario_location = os.path.join(cls.tmp_dir.name, "scenarios")
        os.makedirs(cls.scenario_location)

        template_path = os.environ.get(DB_TEMPLATE_ENV_VAR)
        if template_path and os.path.exists(template_path):
            shutil.copyfile(template_path, cls.db_path)
        else:
            csv_path = os.path.join(REPO_DIRECTORY, "db", "csvs_test_examples")
            create_database.main(
                [
                    "--database",
                    cls.db_path,
                    "--db_schema",
                    os.path.join(REPO_DIRECTORY, "db", "db_schema.sql"),
                    "--data_directory",
                    os.path.join(REPO_DIRECTORY, "db", "data"),
                ]
            )
            port_csvs_to_db.main(
                ["--database", cls.db_path, "--csv_location", csv_path, "--quiet"]
            )
            scenario.main(
                [
                    "--database",
                    cls.db_path,
                    "--csv_path",
                    os.path.join(csv_path, "scenarios.csv"),
                    "--quiet",
                ]
            )

        cls.objectives = {}
        for scenario_name in [COMPACT, EXPANDED_TWIN]:
            cls.objectives[scenario_name] = run_end_to_end.main(
                [
                    "--database",
                    cls.db_path,
                    "--scenario",
                    scenario_name,
                    "--scenario_location",
                    cls.scenario_location,
                    "--quiet",
                    "--mute_solver_output",
                    "--testing",
                ]
            )

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def hydro_dispatch(self, scenario_name):
        df = pd.read_csv(
            os.path.join(
                self.scenario_location,
                scenario_name,
                "results",
                "project_timepoint.csv",
            )
        )
        return df[df["project"] == "Hydro"].set_index("timepoint")

    def test_objectives_match(self):
        compact = self.objectives[COMPACT][("", "", "", 1)][1]
        twin = self.objectives[EXPANDED_TWIN][("", "", "", 1)][1]
        self.assertAlmostEqual(compact, twin, delta=1e-6 * abs(twin))

    def test_weighted_hydro_energy_equals_budget_and_shifts_to_peak_day(self):
        hydro = self.hydro_dispatch(COMPACT)
        self.assertEqual(sorted(hydro.index), [PEAK_DAY_TMP, MEDIAN_DAY_TMP])
        self.assertEqual(hydro.loc[PEAK_DAY_TMP, "timepoint_weight"], 1)
        self.assertEqual(hydro.loc[MEDIAN_DAY_TMP, "timepoint_weight"], 364)

        weighted_energy = (
            hydro["power_mw"]
            * hydro["number_of_hours_in_timepoint"]
            * hydro["timepoint_weight"]
        ).sum()
        self.assertAlmostEqual(
            weighted_energy,
            HYDRO_AVERAGE_POWER_FRACTION * HYDRO_CAPACITY_MW * HOURS_IN_YEAR,
            places=3,
        )
        # The peak day is the expensive one: hydro runs at its maximum there
        # and the median day gets what is left of the budget
        self.assertAlmostEqual(hydro.loc[PEAK_DAY_TMP, "power_mw"], HYDRO_CAPACITY_MW)
        self.assertLess(
            hydro.loc[MEDIAN_DAY_TMP, "power_mw"],
            HYDRO_AVERAGE_POWER_FRACTION * HYDRO_CAPACITY_MW,
        )

    def test_twin_hydro_energy_equals_the_same_budget(self):
        """
        The twin's 365 days are all weight 1, so its plain energy must equal
        the compact example's weighted energy. (Its day-by-day dispatch is
        not compared: the median days share a price, so how the solver
        spreads the energy among them is degenerate.)
        """
        hydro = self.hydro_dispatch(EXPANDED_TWIN)
        self.assertEqual(len(hydro), 365)
        self.assertTrue((hydro["timepoint_weight"] == 1).all())
        energy = (hydro["power_mw"] * hydro["number_of_hours_in_timepoint"]).sum()
        self.assertAlmostEqual(
            energy,
            HYDRO_AVERAGE_POWER_FRACTION * HYDRO_CAPACITY_MW * HOURS_IN_YEAR,
            places=3,
        )


if __name__ == "__main__":
    unittest.main()
