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
Differential test: the operational periods of the new-build projects that
the model inputs are written for (get_new_build_operational_periods, from
the database) are the model's operational periods (the
OPR_PRDS_BY_{prefix}_VINTAGE sets), project-vintage by project-vintage. The
examples cover every new-build capacity type, a three-stage scenario tree,
and a financial lifetime that differs from the operational one.

The inputs are written to a temporary directory so that the committed
example directories are not touched.
"""

from argparse import Namespace
import os
import shutil
import sqlite3
import tempfile
import unittest
import warnings

from db import create_database
from db.utilities import port_csvs_to_db, scenario
from gridpath import get_scenario_inputs
from gridpath.auxiliary.scenario_chars import SubScenarios
from gridpath.project.capacity.capacity_types.common_methods import (
    get_new_build_operational_periods,
)
from gridpath.run_scenario import create_problem

REPO_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_TEMPLATE_ENV_VAR = "GRIDPATH_TEST_EXAMPLES_DB_TEMPLATE"

# Set name prefixes of the new-build capacity types
NEW_BUILD_SET_PREFIXES = [
    "ENERGY_NEW_LIN",
    "FUEL_PROD_NEW",
    "GEN_NEW_BIN",
    "GEN_NEW_LIN",
    "STOR_NEW_BIN",
    "STOR_NEW_LIN",
]

EXAMPLES = [
    "3stage_new_build_2zones_new_build_transmission_stochastic_tree",
    "2periods_new_build_fin_lifetime",
    "test_w_energy_products",
    "test_new_solar_carbon_cap_2zones_tx_hydrogen_prod_new",
    "test_new_binary_solar",
    "test_new_binary_build_storage",
    "generic_policy_sod_test",
]


class TestNewBuildOperationalPeriods(unittest.TestCase):
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

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def test_inputs_side_periods_are_the_model_periods(self):
        covered_prefixes = set()
        for scenario_name in EXAMPLES:
            with self.subTest(scenario=scenario_name):
                get_scenario_inputs.main(
                    [
                        "--database",
                        self.db_path,
                        "--scenario",
                        scenario_name,
                        "--scenario_location",
                        self.scenario_location,
                        "--quiet",
                    ]
                )
                # generic_policy_sod_test has a year horizon spanning periods
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", message="Horizon found that spans periods"
                    )
                    _, instance = create_problem(
                        scenario_directory=os.path.join(
                            self.scenario_location, scenario_name
                        ),
                        weather_iteration="",
                        hydro_iteration="",
                        availability_iteration="",
                        subproblem="",
                        stage="",
                        multi_stage=False,
                        parsed_arguments=Namespace(
                            quiet=True, report_timing=False, skip_duals=True
                        ),
                    )
                model_periods = {}
                for prefix in NEW_BUILD_SET_PREFIXES:
                    by_vintage = getattr(
                        instance, f"OPR_PRDS_BY_{prefix}_VINTAGE", None
                    )
                    if by_vintage is None:
                        continue
                    covered_prefixes.add(prefix)
                    for prj_vintage in by_vintage:
                        model_periods[prj_vintage] = list(by_vintage[prj_vintage])

                conn = sqlite3.connect(self.db_path)
                self.addCleanup(conn.close)
                (scenario_id,) = conn.execute(
                    "SELECT scenario_id FROM scenarios WHERE scenario_name = ?",
                    (scenario_name,),
                ).fetchone()
                _, _, inputs_periods = get_new_build_operational_periods(
                    conn=conn,
                    subscenarios=SubScenarios(conn=conn, scenario_id=scenario_id),
                    subproblem=1,
                    stage=1,
                )
                self.assertTrue(model_periods)
                self.assertDictEqual(model_periods, inputs_periods)

        self.assertSetEqual(set(NEW_BUILD_SET_PREFIXES), covered_prefixes)


if __name__ == "__main__":
    unittest.main()
