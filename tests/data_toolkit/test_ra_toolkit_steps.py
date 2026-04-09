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
import pandas as pd
import unittest

from db.create_database import main as create_database_main
from data_toolkit.load_raw_data import main as load_raw_data_main
from data_toolkit.system.create_sync_load_input_csvs import main as create_sync_load_input_csvs_main
from data_toolkit.project.opchar.var_profiles.create_sync_var_gen_input_csvs import main as create_sync_var_gen_input_csvs_main
from data_toolkit.temporal.create_monte_carlo_weather_draws import main as create_monte_carlo_weather_draws_main
from data_toolkit.temporal.create_monte_carlo_weather_draw_profiles import main as create_monte_carlo_weather_draw_profiles_main
from data_toolkit.system.create_monte_carlo_load_input_csvs import main as create_monte_carlo_load_input_csvs_main
from data_toolkit.project.opchar.var_profiles.create_monte_carlo_var_gen_input_csvs import main as create_monte_carlo_var_gen_input_csvs_main
from data_toolkit.project.opchar.hydro.create_hydro_iteration_input_csvs import main as create_hydro_iteration_input_csvs_main
from data_toolkit.project.availability.outages.create_availability_iteration_input_csvs import main as create_availability_iteration_input_csvs_main
from data_toolkit.project.availability.weather_derates.create_sync_gen_weather_derate_input_csvs import main as create_sync_gen_weather_derate_input_csvs_main
from data_toolkit.project.availability.weather_derates.create_monte_carlo_gen_weather_derate_input_csvs import main as create_monte_carlo_gen_weather_derate_input_csvs_main
from data_toolkit.temporal.create_temporal_scenarios import main as create_temporal_scenarios_main

RA_SETTINGS_STEPS_CSV = "../tests/test_data/data_toolkit_ra_settings_steps.csv"


class TestRAToolkitSteps(unittest.TestCase):
    """
    Test individual RA toolkit scripts with their specific arguments.
    """

    @classmethod
    def setUpClass(cls):
        """
        Load settings and prepare for tests
        """
        os.chdir(os.path.join(os.path.dirname(__file__), "..", "..", "db"))
        cls.settings_df = pd.read_csv(RA_SETTINGS_STEPS_CSV)
        
        # Clean up temp database if it exists
        db_path = cls._get_setting("create_database", "database")
        if os.path.exists(db_path):
            os.remove(db_path)

    @classmethod
    def _get_setting(cls, script, setting):
        """Get a setting value from the settings CSV"""
        row = cls.settings_df[(cls.settings_df['script'] == script) & (cls.settings_df['setting'] == setting)]
        if not row.empty:
            return row.iloc[0]['value']
        return None

    @classmethod
    def _get_args_for_script(cls, script_name):
        """Build argument list for a script from settings CSV"""
        script_settings = cls.settings_df[cls.settings_df['script'] == script_name]
        args = []
        
        for _, row in script_settings.iterrows():
            setting = row['setting']
            value = row['value']
            script_true_false_arg = row['script_true_false_arg']
            reverse_default = row['reverse_default_behavior']
            
            # Convert setting name to argument format
            arg_name = f"--{setting}"
            
            # Handle true/false arguments
            if pd.notna(script_true_false_arg) and script_true_false_arg == 1:
                if pd.notna(reverse_default) and reverse_default == 1:
                    # Don't include the flag (reversed default behavior)
                    continue
                else:
                    # Include the flag
                    args.append(arg_name)
            elif pd.notna(value):
                # Regular setting with value
                args.append(arg_name)
                args.append(str(value))
        
        return args

    def test_create_database(self):
        """Test create_database script"""
        args = self._get_args_for_script("create_database")
        create_database_main(args)

    def test_load_raw_data(self):
        """Test load_raw_data script"""
        args = self._get_args_for_script("load_raw_data")
        load_raw_data_main(args)

    def test_create_sync_load_input_csvs(self):
        """Test create_sync_load_input_csvs script"""
        args = self._get_args_for_script("create_sync_load_input_csvs")
        create_sync_load_input_csvs_main(args)

    def test_create_sync_var_gen_input_csvs(self):
        """Test create_sync_var_gen_input_csvs script"""
        args = self._get_args_for_script("create_sync_var_gen_input_csvs")
        create_sync_var_gen_input_csvs_main(args)

    def test_create_monte_carlo_weather_draws(self):
        """Test create_monte_carlo_weather_draws script"""
        args = self._get_args_for_script("create_monte_carlo_weather_draws")
        create_monte_carlo_weather_draws_main(args)

    def test_create_monte_carlo_weather_draw_profiles(self):
        """Test create_monte_carlo_weather_draw_profiles script"""
        args = self._get_args_for_script("create_monte_carlo_weather_draw_profiles")
        create_monte_carlo_weather_draw_profiles_main(args)

    def test_create_monte_carlo_load_input_csvs(self):
        """Test create_monte_carlo_load_input_csvs script"""
        args = self._get_args_for_script("create_monte_carlo_load_input_csvs")
        create_monte_carlo_load_input_csvs_main(args)

    def test_create_monte_carlo_var_gen_input_csvs(self):
        """Test create_monte_carlo_var_gen_input_csvs script"""
        args = self._get_args_for_script("create_monte_carlo_var_gen_input_csvs")
        create_monte_carlo_var_gen_input_csvs_main(args)

    def test_create_hydro_iteration_input_csvs(self):
        """Test create_hydro_iteration_input_csvs script"""
        args = self._get_args_for_script("create_hydro_iteration_input_csvs")
        create_hydro_iteration_input_csvs_main(args)

    def test_create_availability_iteration_input_csvs(self):
        """Test create_availability_iteration_input_csvs script"""
        args = self._get_args_for_script("create_availability_iteration_input_csvs")
        create_availability_iteration_input_csvs_main(args)

    def test_create_sync_gen_weather_derate_input_csvs(self):
        """Test create_sync_gen_weather_derate_input_csvs script"""
        args = self._get_args_for_script("create_sync_gen_weather_derate_input_csvs")
        create_sync_gen_weather_derate_input_csvs_main(args)

    def test_create_monte_carlo_gen_weather_derate_input_csvs(self):
        """Test create_monte_carlo_gen_weather_derate_input_csvs script"""
        args = self._get_args_for_script("create_monte_carlo_gen_weather_derate_input_csvs")
        create_monte_carlo_gen_weather_derate_input_csvs_main(args)

    def test_create_temporal_scenarios(self):
        """Test create_temporal_scenarios script"""
        args = self._get_args_for_script("create_temporal_scenarios")
        create_temporal_scenarios_main(args)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        db_path = cls._get_setting("create_database", "database")
        if os.path.exists(db_path):
            os.remove(db_path)
        for temp_file_ext in ["-shm", "-wal"]:
            temp_file = f"{db_path}{temp_file_ext}"
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()
