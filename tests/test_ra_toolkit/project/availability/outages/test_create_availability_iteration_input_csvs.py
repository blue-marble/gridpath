# Copyright 2016-2024 Blue Marble Analytics LLC.
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

import filecmp
import os
import pandas as pd
import sqlite3
import tempfile
import unittest

from db.create_database import main as create_database_main
from ra_toolkit.load_raw_data import main as load_raw_data_main
from ra_toolkit.project.availability.outages.create_availability_iteration_input_csvs import (
    main as create_availability_iteration_input_csvs_main,
)
from ra_toolkit.temporal.create_monte_carlo_weather_draws import (
    main as create_monte_carlo_weather_draws_main,
)
from ra_toolkit.temporal.create_monte_carlo_weather_draw_profiles import (
    main as create_monte_carlo_weather_draw_profiles_main,
)

PROJECTS = ["Batteries", "Gas", "Hybrid", "TestOnes"]
# The unit whose forced outage rate the tests make vary by weather (its
# hourly profile is in the raw data fixture); it belongs to Gas
WEATHER_VARYING_UNIT = "GasCC1"
N_ITERATIONS = 4
# Monte Carlo weather iterations of the draws; sync weather iterations are
# the years of the forced outage rate profiles
MONTE_CARLO_WEATHER_ITERATIONS = [1, 2]
SYNC_WEATHER_ITERATIONS = [2010, 2011]


def build_raw_db(db_path):
    """
    Create a raw database with the RA toolkit fixture data, GasCC1's forced
    outage rate flagged to vary by weather, and two Monte Carlo weather
    iterations with their draw days.
    """
    create_database_main(
        [
            "--database",
            db_path,
            "--db_schema",
            "../ra_toolkit/raw_data_db_schema.sql",
            "--quiet",
        ]
    )
    load_raw_data_main(
        [
            "--database",
            db_path,
            "--csv_location",
            "./csvs_test_examples/raw_data_ra_toolkit/",
            "--quiet",
        ]
    )
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE raw_data_unit_availability_params "
        "SET unit_for_varies_by_weather = 1 WHERE unit = ?;",
        (WEATHER_VARYING_UNIT,),
    )
    conn.commit()
    conn.close()
    create_monte_carlo_weather_draws_main(
        [
            "--database",
            db_path,
            "--weather_draws_seed",
            "0",
            "--n_iterations",
            str(len(MONTE_CARLO_WEATHER_ITERATIONS)),
            "--study_year",
            "2026",
            "--quiet",
        ]
    )
    create_monte_carlo_weather_draw_profiles_main(
        [
            "--database",
            db_path,
            "--study_year",
            "2026",
            "--timeseries_iteration_draw_initial_seed",
            "0",
            "--quiet",
        ]
    )


def outage_step_args(db_path, output_directory, scenario_id, scenario_name):
    return [
        "--database",
        db_path,
        "--n_iterations",
        str(N_ITERATIONS),
        "--project_availability_scenario_id",
        str(scenario_id),
        "--project_availability_scenario_name",
        scenario_name,
        "--output_directory",
        output_directory,
        "--quiet",
        "--overwrite",
        "--sort",
        "--user_provided_seeding",
        "--starting_project_iteration_seed",
        "1",
    ]


def read_outputs(output_directory, scenario_id, scenario_name):
    """
    :return: ({project: outages DataFrame}, {project: (varies_by_weather,)})
    """
    outages = {}
    flags = {}
    for project in PROJECTS:
        filename = f"{project}-{scenario_id}-{scenario_name}.csv"
        outages[project] = pd.read_csv(os.path.join(output_directory, filename))
        sidecar = pd.read_csv(os.path.join(output_directory, "iterations", filename))
        flags[project] = tuple(sidecar.iloc[0].astype(int))

    return outages, flags


def iteration_keys(df):
    return sorted(
        set(
            zip(
                df["weather_iteration"],
                df["availability_iteration"],
            )
        )
    )


class TestCreateAvailabilityIterationInputCsvs(unittest.TestCase):
    """
    Test create_availability_iteration_input_csvs script
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        os.chdir(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "db")
        )
        # The scratch DB lives in a per-class temp dir: a shared
        # CWD-relative DB file caused flaky lock/disk-I/O errors and stale
        # WAL state across test modules
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "step_test_temp.db")
        build_raw_db(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cls.tmp_dir.cleanup()

    def test_monte_carlo_weather_mode(self):
        """Gas (GasCC1 varies by weather) is simulated once per Monte Carlo
        weather iteration and flagged in the iterations sidecar; the other
        projects are written once at weather_iteration 0. Writes the
        committed id-3 fixtures."""
        output_directory = "./csvs_test_examples/project/availability/exogenous_outage"
        create_availability_iteration_input_csvs_main(
            outage_step_args(
                self.db_path, output_directory, 3, "ra_toolkit_module_tests"
            )
            + ["--weather_mode", "monte_carlo"]
        )
        outages, flags = read_outputs(output_directory, 3, "ra_toolkit_module_tests")

        for project in PROJECTS:
            df = outages[project]
            self.assertTrue(df["timepoint"].between(1, 8760).all(), project)
            if project == "Gas":
                self.assertEqual(
                    iteration_keys(df),
                    [
                        (w, a)
                        for w in MONTE_CARLO_WEATHER_ITERATIONS
                        for a in range(1, N_ITERATIONS + 1)
                    ],
                )
                self.assertEqual(flags[project], (1,))
            else:
                self.assertEqual(
                    iteration_keys(df), [(0, a) for a in range(1, N_ITERATIONS + 1)]
                )
                self.assertEqual(flags[project], (0,))

        # Each weather iteration draws its own outages
        gas = outages["Gas"]
        self.assertFalse(
            gas[(gas["weather_iteration"] == 1) & (gas["availability_iteration"] == 1)]
            .set_index("timepoint")["availability_derate_outage"]
            .equals(
                gas[
                    (gas["weather_iteration"] == 2)
                    & (gas["availability_iteration"] == 1)
                ].set_index("timepoint")["availability_derate_outage"]
            )
        )

    def test_sync_weather_mode(self):
        """Under sync mode the weather iterations are the years of the
        forced outage rate profiles."""
        with tempfile.TemporaryDirectory() as output_directory:
            create_availability_iteration_input_csvs_main(
                outage_step_args(self.db_path, output_directory, 1, "sync")
                + ["--weather_mode", "sync"]
            )
            outages, flags = read_outputs(output_directory, 1, "sync")

        self.assertEqual(
            iteration_keys(outages["Gas"]),
            [
                (w, a)
                for w in SYNC_WEATHER_ITERATIONS
                for a in range(1, N_ITERATIONS + 1)
            ],
        )
        self.assertEqual(flags["Gas"], (1,))
        self.assertEqual(
            iteration_keys(outages["Batteries"]),
            [(0, a) for a in range(1, N_ITERATIONS + 1)],
        )
        self.assertEqual(flags["Batteries"], (0,))

    def test_weather_varying_unit_under_weather_mode_none_raises(self):
        """A flagged unit is an error rather than silently simulated with
        its constant unit_for."""
        with tempfile.TemporaryDirectory() as output_directory:
            with self.assertRaises(ValueError) as context:
                create_availability_iteration_input_csvs_main(
                    outage_step_args(self.db_path, output_directory, 1, "none")
                )
        self.assertIn("['Gas']", str(context.exception))

    def test_constant_profile_reproduces_weather_independent_outages(self):
        """Proof of the weather-mode plumbing and seed layout: with GasCC1's
        hourly forced outage rate profile set to its constant unit_for, the
        first weather iteration's Gas timelines under monte_carlo mode are
        exactly the weather-independent ones (same seeds, same forced outage
        rates), and the other projects' files are byte-identical. Then, a
        drawn day without profile rows is a loud error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "constant_profile.db")
            build_raw_db(db_path)
            conn = sqlite3.connect(db_path)
            unit_for = conn.execute(
                "SELECT unit_for FROM raw_data_unit_availability_params "
                "WHERE unit = ?;",
                (WEATHER_VARYING_UNIT,),
            ).fetchone()[0]
            conn.execute(
                "UPDATE raw_data_unit_forced_outage_rate_profiles SET value = ? "
                "WHERE unit = ?;",
                (unit_for, WEATHER_VARYING_UNIT),
            )
            conn.commit()
            conn.close()

            weather_dir = os.path.join(tmp_dir, "weather")
            create_availability_iteration_input_csvs_main(
                outage_step_args(db_path, weather_dir, 1, "test")
                + ["--weather_mode", "monte_carlo"]
            )

            conn = sqlite3.connect(db_path)
            conn.execute(
                "UPDATE raw_data_unit_availability_params "
                "SET unit_for_varies_by_weather = 0;"
            )
            conn.commit()
            conn.close()
            independent_dir = os.path.join(tmp_dir, "independent")
            create_availability_iteration_input_csvs_main(
                outage_step_args(db_path, independent_dir, 1, "test")
            )

            weather_outages, weather_flags = read_outputs(weather_dir, 1, "test")
            independent_outages, independent_flags = read_outputs(
                independent_dir, 1, "test"
            )
            for project in PROJECTS:
                if project == "Gas":
                    continue
                self.assertTrue(
                    filecmp.cmp(
                        os.path.join(weather_dir, f"{project}-1-test.csv"),
                        os.path.join(independent_dir, f"{project}-1-test.csv"),
                        shallow=False,
                    ),
                    project,
                )
            gas_weather = weather_outages["Gas"]
            first_weather_iteration = (
                gas_weather[
                    gas_weather["weather_iteration"]
                    == MONTE_CARLO_WEATHER_ITERATIONS[0]
                ]
                .drop(columns="weather_iteration")
                .reset_index(drop=True)
            )
            pd.testing.assert_frame_equal(
                first_weather_iteration,
                independent_outages["Gas"].drop(columns="weather_iteration"),
            )
            self.assertEqual(weather_flags["Gas"], (1,))
            self.assertEqual(independent_flags["Gas"], (0,))

            # A drawn day without profile rows
            conn = sqlite3.connect(db_path)
            conn.execute(
                "UPDATE raw_data_unit_availability_params "
                "SET unit_for_varies_by_weather = 1 WHERE unit = ?;",
                (WEATHER_VARYING_UNIT,),
            )
            year, month, day_of_month = conn.execute(
                "SELECT thermal_year, thermal_month, thermal_day_of_month "
                "FROM aux_weather_iterations WHERE weather_iteration = ? "
                "ORDER BY draw_number LIMIT 1;",
                (MONTE_CARLO_WEATHER_ITERATIONS[-1],),
            ).fetchone()
            conn.execute(
                "DELETE FROM raw_data_unit_forced_outage_rate_profiles "
                "WHERE unit = ? AND year = ? AND month = ? AND day_of_month = ?;",
                (WEATHER_VARYING_UNIT, year, month, day_of_month),
            )
            conn.commit()
            conn.close()
            with self.assertRaises(ValueError) as context:
                create_availability_iteration_input_csvs_main(
                    outage_step_args(db_path, weather_dir, 1, "test")
                    + ["--weather_mode", "monte_carlo", "--n_parallel_projects", "1"]
                )
            self.assertIn(WEATHER_VARYING_UNIT, str(context.exception))
            self.assertIn(
                f", {year}, {month}, {day_of_month}, 0)", str(context.exception)
            )


if __name__ == "__main__":
    unittest.main()
