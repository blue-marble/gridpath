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
Proof that the per-BA cap on a project's reserve provision binds in the
``2periods_new_build_2zones_multi_ba_reserves`` example.

In the example, Zone1's load-following-up providers are its two gas CTs,
which may each send at most half of their provision to Zone2, where the only
local provider is the (dearer, for reserves) Gas_CCGT_z2; Zone2's requirement
is twice Zone1's. The solved example must satisfy the allocation identity,
hit the caps with a nonzero dual, and be strictly worse than an otherwise
identical twin whose caps are lifted.
"""

import os
import shutil
import tempfile
import unittest
import warnings

from pyomo.environ import value

from db import create_database
from db.utilities import port_csvs_to_db, scenario
from gridpath import get_scenario_inputs, run_scenario

TOLERANCE = 1e-6
DB_TEMPLATE_ENV_VAR = "GRIDPATH_TEST_EXAMPLES_DB_TEMPLATE"
REPO_DIRECTORY = os.path.join(os.path.dirname(__file__), "..")
EXAMPLE = "2periods_new_build_2zones_multi_ba_reserves"
UNCAPPED_TWIN = EXAMPLE + "_uncapped_twin"
CAPPED_PROJECTS = ["Gas_CT", "Gas_CT_new"]
BACKSTOP_PROJECT = "Gas_CCGT_z2"
CAP = 0.5


class TestMultiBAReservesExample(unittest.TestCase):
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

        get_scenario_inputs.main(
            [
                "--database",
                cls.db_path,
                "--scenario",
                EXAMPLE,
                "--scenario_location",
                cls.scenario_location,
                "--quiet",
            ]
        )

        # A copy with the caps lifted (the default of 1, written as ".")
        example_dir = os.path.join(cls.scenario_location, EXAMPLE)
        twin_dir = os.path.join(cls.scenario_location, UNCAPPED_TWIN)
        shutil.copytree(example_dir, twin_dir)
        map_file = os.path.join(twin_dir, "inputs", "project_lf_reserves_up_bas.tab")
        with open(map_file) as f:
            rows = f.read().splitlines()
        for prj in CAPPED_PROJECTS:
            capped_row = f"{prj}\tZone2\t{CAP}"
            assert capped_row in rows, rows
            rows[rows.index(capped_row)] = f"{prj}\tZone2\t."
        with open(map_file, "w") as f:
            f.write("\n".join(rows) + "\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def build_and_solve(self, scenario_name):
        parsed_arguments = run_scenario.parse_arguments(
            [
                "--scenario",
                scenario_name,
                "--scenario_location",
                self.scenario_location,
                "--quiet",
                "--mute_solver_output",
            ]
        )
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="Horizon found that spans periods"
            )
            _, instance = run_scenario.create_problem(
                scenario_directory=os.path.join(self.scenario_location, scenario_name),
                weather_iteration="",
                hydro_iteration="",
                availability_iteration="",
                subproblem="",
                stage="",
                multi_stage=False,
                parsed_arguments=parsed_arguments,
            )
        run_scenario.solve(instance, parsed_arguments)
        return instance

    def test_cap_binds(self):
        instance = self.build_and_solve(EXAMPLE)

        # The map: the Zone1 CTs in both zones with the cap on Zone2, the
        # Zone2 CCGT local only
        self.assertEqual(
            sorted(instance.LF_RESERVES_UP_MULTI_BA_PRJS), sorted(CAPPED_PROJECTS)
        )
        self.assertEqual(
            sorted(instance.LF_RESERVES_UP_PRJS_BY_BA["Zone2"]),
            sorted(CAPPED_PROJECTS + [BACKSTOP_PROJECT]),
        )
        self.assertEqual(
            sorted(instance.LF_RESERVES_UP_PRJS_BY_BA["Zone1"]),
            sorted(CAPPED_PROJECTS),
        )
        for prj in CAPPED_PROJECTS:
            self.assertEqual(
                instance.lf_reserves_up_max_fraction_of_provision[prj, "Zone2"], CAP
            )
        # Only the capped pairs build the cap constraint
        self.assertEqual(
            {
                (prj, ba)
                for (
                    prj,
                    ba,
                    tmp,
                ) in instance.LF_Reserves_Up_Max_Fraction_to_BA_Constraint
            },
            {(prj, "Zone2") for prj in CAPPED_PROJECTS},
        )

        # Allocations sum to the total for every multi-BA project-timepoint
        for prj, tmp in instance.LF_RESERVES_UP_PRJ_OPR_TMPS:
            if prj not in instance.LF_RESERVES_UP_MULTI_BA_PRJS:
                continue
            total = value(instance.Provide_LF_Reserves_Up_MW[prj, tmp])
            allocated = sum(
                value(instance.Provide_LF_Reserves_Up_by_BA_MW[prj, ba, tmp])
                for ba in instance.LF_RESERVES_UP_BAS_BY_PRJ[prj]
            )
            self.assertAlmostEqual(total, allocated, delta=TOLERANCE)

        # The cap holds and binds with a nonzero dual in every timepoint
        n_binding = 0
        for prj, ba, tmp in instance.LF_Reserves_Up_Max_Fraction_to_BA_Constraint:
            to_ba = value(instance.Provide_LF_Reserves_Up_by_BA_MW[prj, ba, tmp])
            total = value(instance.Provide_LF_Reserves_Up_MW[prj, tmp])
            self.assertLessEqual(to_ba, CAP * total + TOLERANCE)
            dual = instance.dual[
                instance.LF_Reserves_Up_Max_Fraction_to_BA_Constraint[prj, ba, tmp]
            ]
            if abs(dual) > TOLERANCE:
                self.assertAlmostEqual(to_ba, CAP * total, delta=TOLERANCE)
                n_binding += 1
        self.assertGreater(n_binding, 0)

        # Lifting the cap is strictly better (the objective is maximized)
        twin = self.build_and_solve(UNCAPPED_TWIN)
        self.assertGreater(
            value(twin.NPV) - value(instance.NPV), 1e-3 * abs(value(instance.NPV))
        )


if __name__ == "__main__":
    unittest.main()
