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
import unittest

from db.utilities.ra_toolkit import run_ra_toolkit

SETTINGS_CSV = "../tests/test_data/ra_toolkit_settings.csv"


class TestRAToolkit(unittest.TestCase):
    """
    Check if the database is created with no errors.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the testing database
        :return:
        """
        # TODO: get from the settings file
        os.chdir(os.path.join(os.path.dirname(__file__), "..", "db"))
        print(os.getcwd())
        temp_db_path = os.path.join(os.getcwd(), "ra_toolkit_test.db")

        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

    def test_ra_toolkit(self):
        # TODO: get from the settings file
        os.chdir(os.path.join(os.path.dirname(__file__), "..", "db"))
        print(os.getcwd())
        run_ra_toolkit.main(["--settings_csv", SETTINGS_CSV])

    @classmethod
    def tearDownClass(cls):
        # TODO: get from the settings file
        temp_db_path = os.path.join(os.getcwd(), "ra_toolkit_test_temp.db")
        os.remove(temp_db_path)
        for temp_file_ext in ["-shm", "-wal"]:
            temp_file = "{}{}".format(temp_db_path, temp_file_ext)
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()
