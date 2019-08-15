#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import os
import unittest

from db import create_database

# Change directory to 'db,' as it's what create_database.py expects
os.chdir(os.path.join(os.path.dirname(__file__), "..", "db"))


class TestCreateDatabase(unittest.TestCase):
    """
    Check if the database is created with no errors.
    """
    create_database.main(["--in_memory_db"])
