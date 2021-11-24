# Copyright 2016-2020 Blue Marble Analytics LLC.
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

from db import create_database

# Change directory to 'db,' as it's what create_database.py expects
os.chdir(os.path.join(os.path.dirname(__file__), "..", "db"))


class TestCreateDatabase(unittest.TestCase):
    """
    Check if the database is created with no errors.
    """

    create_database.main(["--in_memory"])
