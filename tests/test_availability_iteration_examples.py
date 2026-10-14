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
Independent availability derates keyed by weather iteration, proven on the
examples database: in ``ra_toolkit_monte_carlo_w_weather_dependent_outages``
the Gas project's derates (subscenario 4) are flagged to vary by weather
iteration and hold one outage timeline per Monte Carlo draw, (weather 1,
availability 1) and (weather 2, availability 2). The first is the
weather-independent iteration-1 timeline of ``ra_toolkit_monte_carlo``
(subscenario 1), the second is that subscenario's iteration-3 timeline. Each
draw must read its own slice, and the other projects, which do not vary by
weather, must read what they read in ``ra_toolkit_monte_carlo``.
"""

import os
import shutil
import sqlite3
import tempfile
import unittest

from db import create_database
from db.utilities import port_csvs_to_db, scenario
from gridpath.auxiliary.scenario_chars import SubScenarios
from gridpath.project.availability.availability_types.exogenous import (
    get_inputs_from_database,
)

REPO_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_TEMPLATE_ENV_VAR = "GRIDPATH_TEST_EXAMPLES_DB_TEMPLATE"

BASE = "ra_toolkit_monte_carlo"
WEATHER_DEPENDENT = "ra_toolkit_monte_carlo_w_weather_dependent_outages"

# The Monte Carlo draws (weather, hydro, availability iteration) and the
# availability iteration of the base example's Gas timeline that the
# weather-dependent example's Gas rows are a copy of
DRAWS = {(1, 2010, 1): 1, (2, 2011, 2): 3}


class TestAvailabilityIterationExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "examples.db")

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
                    "--quiet",
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

        cls.conn = sqlite3.connect(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp_dir.cleanup()

    def get_outage_derates(self, scenario_name, weather, hydro, availability):
        """
        :return: {project: {timepoint: derate}} of the scenario's outage
            derates in subproblem 1, stage 1 of the draw
        """
        scenario_id = self.conn.execute(
            "SELECT scenario_id FROM scenarios WHERE scenario_name = ?;",
            (scenario_name,),
        ).fetchone()[0]
        outage_availabilities = get_inputs_from_database(
            scenario_id=scenario_id,
            subscenarios=SubScenarios(conn=self.conn, scenario_id=scenario_id),
            weather_iteration=weather,
            hydro_iteration=hydro,
            availability_iteration=availability,
            subproblem=1,
            stage=1,
            conn=self.conn,
        )[0]

        derates = {}
        for project, timepoint, derate, _ in outage_availabilities:
            derates.setdefault(project, {})[timepoint] = derate

        return derates

    def test_each_draw_reads_its_own_weather_slice(self):
        base = {
            availability: self.get_outage_derates(BASE, 1, 2010, availability)
            for availability in [1, 2, 3]
        }
        # The three base timelines differ, so matching one is a real check
        self.assertNotEqual(base[1]["Gas"], base[2]["Gas"])
        self.assertNotEqual(base[1]["Gas"], base[3]["Gas"])
        self.assertNotEqual(base[2]["Gas"], base[3]["Gas"])

        for (weather, hydro, availability), base_availability in DRAWS.items():
            derates = self.get_outage_derates(
                WEATHER_DEPENDENT, weather, hydro, availability
            )
            # Gas reads the slice of its weather iteration ...
            self.assertDictEqual(
                derates["Gas"], base[base_availability]["Gas"], (weather, hydro)
            )
            # ... and the other projects read what they do in the base example
            self.assertDictEqual(
                {prj: d for prj, d in derates.items() if prj != "Gas"},
                {prj: d for prj, d in base[availability].items() if prj != "Gas"},
                (weather, hydro),
            )

    def test_slice_of_another_weather_iteration_is_empty(self):
        """Gas has no rows at (weather 2, availability 1): the slice is
        empty rather than falling back to another iteration."""
        derates = self.get_outage_derates(WEATHER_DEPENDENT, 2, 2011, 1)
        self.assertNotIn("Gas", derates)
        self.assertIn("Batteries", derates)


if __name__ == "__main__":
    unittest.main()
