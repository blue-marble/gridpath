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
Differential test for storage state-of-charge tracking on a multi-sample
horizon. The compact example represents a year with one circular 'day'
horizon holding a peak day (weight 1) and a median day (weight 364), four
6-hour timepoints each; its expanded twin spells the same year out as the
peak day followed by 364 explicit, identical median days (all weights 1).
The storage type repeats the median-day sample block 364 times, carrying
the energy in storage across the repeats, so:

* the two examples share an objective function value (the median days
  are exchangeable here: no self-discharge, so holding energy costs
  nothing, and the model can charge the battery a little on every median
  day instead of all at once on one of them);
* the compact example's battery dispatch, repeated 364 times through the
  storage chain, is a feasible dispatch of the twin: the energy in storage
  stays within its bounds in every repeat and the circular horizon closes;
* the reported starting energy at the last repeat matches that simulation.

Without the repeats the compact example would charge the battery once on
the median day, discharge it on the peak day and count the median day's
charging 364 times in the objective but not in the storage chain
(objective -16.8M instead of -17.6M, measured before the feature).

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

COMPACT = "stor_soc_w_mixed_tmp_weights"
EXPANDED_TWIN = "stor_soc_w_mixed_tmp_weights_expanded_twin"
PRJ = "Battery"
PEAK_DAY_TMPS = [20200011, 20200012, 20200013, 20200014]
MEDIAN_DAY_TMPS = [20200021, 20200022, 20200023, 20200024]
MEDIAN_DAY_WEIGHT = 364
ENERGY_CAPACITY_MWH = 6
CHARGING_EFFICIENCY = 0.8
DISCHARGING_EFFICIENCY = 0.8
TOLERANCE_MWH = 1e-6


class TestStorMultiSampleHorizonExamples(unittest.TestCase):
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

    def battery_dispatch(self, scenario_name):
        df = pd.read_csv(
            os.path.join(
                self.scenario_location,
                scenario_name,
                "results",
                "project_timepoint.csv",
            )
        )
        return df[df["project"] == PRJ].set_index("timepoint")

    @staticmethod
    def energy_step(row):
        return (
            row["charge_mw"] * row["number_of_hours_in_timepoint"] * CHARGING_EFFICIENCY
            - row["discharge_mw"]
            * row["number_of_hours_in_timepoint"]
            / DISCHARGING_EFFICIENCY
        )

    def simulate_compact_chain(self, battery):
        """
        Run the compact example's dispatch through the storage chain with
        the median day repeated: returns the starting energy in every
        timepoint of the peak day and of each repeat of the median day, in
        chronological order, and the energy after the last repeat.
        """
        soc = battery.loc[PEAK_DAY_TMPS[0], "starting_energy_mwh"]
        trajectory = []
        for tmp in PEAK_DAY_TMPS:
            trajectory.append((tmp, 1, soc))
            soc += self.energy_step(battery.loc[tmp])
        for repeat in range(1, MEDIAN_DAY_WEIGHT + 1):
            for tmp in MEDIAN_DAY_TMPS:
                trajectory.append((tmp, repeat, soc))
                soc += self.energy_step(battery.loc[tmp])
        return trajectory, soc

    def test_objectives_match(self):
        compact = self.objectives[COMPACT][("", "", "", 1)][1]
        twin = self.objectives[EXPANDED_TWIN][("", "", "", 1)][1]
        self.assertAlmostEqual(compact, twin, delta=1e-6 * abs(twin))

    def test_compact_dispatch_repeated_is_feasible_and_closes_the_horizon(self):
        battery = self.battery_dispatch(COMPACT)
        self.assertEqual(sorted(battery.index), PEAK_DAY_TMPS + MEDIAN_DAY_TMPS)
        self.assertTrue((battery.loc[MEDIAN_DAY_TMPS, "timepoint_weight"] == 364).all())
        trajectory, soc_after_last_repeat = self.simulate_compact_chain(battery)
        for tmp, repeat, soc in trajectory:
            self.assertGreaterEqual(soc, -TOLERANCE_MWH, msg=(tmp, repeat))
            self.assertLessEqual(
                soc, ENERGY_CAPACITY_MWH + TOLERANCE_MWH, msg=(tmp, repeat)
            )
        # Circular horizon: the last repeat of the median day leads back to
        # the peak day's starting energy
        self.assertAlmostEqual(
            soc_after_last_repeat,
            battery.loc[PEAK_DAY_TMPS[0], "starting_energy_mwh"],
            delta=TOLERANCE_MWH,
        )
        # The model's variables are the first repeat; the results also
        # report the last repeat, which the simulation must reproduce
        first_repeat = {tmp: soc for tmp, repeat, soc in trajectory if repeat == 1}
        last_repeat = {
            tmp: soc
            for tmp, repeat, soc in trajectory
            if repeat == MEDIAN_DAY_WEIGHT and tmp in MEDIAN_DAY_TMPS
        }
        for tmp in PEAK_DAY_TMPS + MEDIAN_DAY_TMPS:
            self.assertAlmostEqual(
                battery.loc[tmp, "starting_energy_mwh"],
                first_repeat[tmp],
                delta=TOLERANCE_MWH,
                msg=tmp,
            )
        for tmp in MEDIAN_DAY_TMPS:
            self.assertAlmostEqual(
                battery.loc[tmp, "starting_energy_last_repeat_mwh"],
                last_repeat[tmp],
                delta=TOLERANCE_MWH,
                msg=tmp,
            )
        self.assertTrue(
            battery.loc[PEAK_DAY_TMPS, "starting_energy_last_repeat_mwh"].isna().all()
        )

    def test_battery_moves_energy_from_the_median_days_to_the_peak_day(self):
        """
        The battery is charged on the median days (a little per repeat)
        and discharged on the peak day, where the marginal unit is dearer.
        """
        battery = self.battery_dispatch(COMPACT)
        median_net = sum(self.energy_step(battery.loc[tmp]) for tmp in MEDIAN_DAY_TMPS)
        peak_net = sum(self.energy_step(battery.loc[tmp]) for tmp in PEAK_DAY_TMPS)
        self.assertGreater(median_net, 0)
        self.assertAlmostEqual(
            peak_net, -MEDIAN_DAY_WEIGHT * median_net, delta=TOLERANCE_MWH
        )


if __name__ == "__main__":
    unittest.main()
