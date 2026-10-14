# Copyright 2016-2024 Blue Marble Analytics LLC.
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
import tempfile
import unittest

from db.create_database import main as create_database_main
from ra_toolkit.load_raw_data import main as load_raw_data_main
from ra_toolkit.temporal.create_monte_carlo_weather_draws import (
    main as create_monte_carlo_weather_draws_main,
)
from ra_toolkit.temporal.create_monte_carlo_weather_draw_profiles import (
    main as create_monte_carlo_weather_draw_profiles_main,
)


class TestCreateMonteCarloWeatherDrawProfiles(unittest.TestCase):
    """
    Test create_monte_carlo_weather_draw_profiles script
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        os.chdir(os.path.join(os.path.dirname(__file__), "..", "..", "..", "db"))
        # The scratch DB lives in a per-class temp dir: a shared
        # CWD-relative DB file caused flaky lock/disk-I/O errors and stale
        # WAL state across test modules
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "step_test_temp.db")

        # Create database first
        create_db_args = [
            "--database",
            cls.db_path,
            "--db_schema",
            "../ra_toolkit/raw_data_db_schema.sql",
            "--quiet",
        ]
        create_database_main(create_db_args)

        # Load the raw data (weather bins, the Monte Carlo timeseries
        # definitions and the load, variable-profile and availability data
        # the draw profiles are matched against)
        load_raw_data_args = [
            "--database",
            cls.db_path,
            "--csv_location",
            "./csvs_test_examples/raw_data_ra_toolkit/",
            "--quiet",
        ]
        load_raw_data_main(load_raw_data_args)

        # Create monte carlo weather draws (prerequisite for this test)
        weather_draws_args = [
            "--database",
            cls.db_path,
            "--weather_draws_seed",
            "0",
            "--n_iterations",
            "2",
            "--study_year",
            "2026",
            "--quiet",
        ]
        create_monte_carlo_weather_draws_main(weather_draws_args)

    def test_create_monte_carlo_weather_draw_profiles(self):
        """Test create_monte_carlo_weather_draw_profiles with hardcoded arguments"""
        args = [
            "--database",
            self.db_path,
            "--study_year",
            "2026",
            "--timeseries_iteration_draw_initial_seed",
            "0",
            "--quiet",
        ]
        create_monte_carlo_weather_draw_profiles_main(args)

        # Every draw of every timeseries in user_defined_monte_carlo_timeseries
        # (load, solar, wind, thermal) must have been matched to a historical
        # day; the step is a silent no-op when no timeseries are loaded
        conn = sqlite3.connect(self.db_path)
        n_draws, n_unmatched = conn.execute("""SELECT COUNT(*),
            SUM(load_year IS NULL OR solar_year IS NULL
                OR wind_year IS NULL OR thermal_year IS NULL)
            FROM aux_weather_iterations;""").fetchone()
        conn.close()
        self.assertEqual(n_draws, 2 * 365)
        self.assertEqual(n_unmatched, 0)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cls.tmp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
