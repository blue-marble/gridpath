#!/usr/bin/env python
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
Create a test database by calling create_database, port_csvs_to_db, and scenario scripts.

This script automates the process of:
1. Creating a new GridPath database
2. Loading CSV data into the database
3. Loading scenarios from the scenarios.csv file
"""

import os
import sys

# Add parent directory to path to import GridPath modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from db.create_database import main as create_database_main
from db.utilities.port_csvs_to_db import main as port_csvs_main
from db.utilities.scenario import main as scenario_main


def main():
    """
    Create a test database with CSV data and scenarios.
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define paths relative to the csvs_test_examples directory
    db_path = os.path.join(script_dir, "test.db")
    csv_location = script_dir
    scenarios_csv_path = os.path.join(script_dir, "scenarios.csv")

    print("=" * 80)
    print("Creating database...")
    print("=" * 80)
    create_database_main(args=["--database", db_path])

    print("\n" + "=" * 80)
    print("Loading CSV data into database...")
    print("=" * 80)
    port_csvs_main(args=["--database", db_path, "--csv_location", csv_location])

    print("\n" + "=" * 80)
    print("Loading scenarios...")
    print("=" * 80)
    scenario_main(args=["--database", db_path, "--csv_path", scenarios_csv_path])

    print("\n" + "=" * 80)
    print("Test database created successfully at:", db_path)
    print("=" * 80)


if __name__ == "__main__":
    main()
