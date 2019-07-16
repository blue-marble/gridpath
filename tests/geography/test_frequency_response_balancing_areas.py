#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from importlib import import_module
import os.path
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "test_data")

# No prerequisite modules
NAME_OF_MODULE_BEING_TESTED = "geography.frequency_response_balancing_areas"

try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")

class TestLoadFollowingUpBAs(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=[],
                              module_to_test=MODULE_BEING_TESTED,
                              test_data_dir=TEST_DATA_DIRECTORY,
                              subproblem="",
                              stage=""
                              )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=[],
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
                                     )

    def test_frequency_response_zones_data_loads_correctly(self):
        """
        Create set and load data; check resulting set is as expected
        :return:
        """
        m, data = \
            add_components_and_load_data(prereq_modules=[],
                                         module_to_test=MODULE_BEING_TESTED,
                                         test_data_dir=TEST_DATA_DIRECTORY,
                                         subproblem="",
                                         stage="")
        instance = m.create_instance(data)
        expected = sorted(["Zone1", "Zone2"])
        actual = sorted([z for z in instance.FREQUENCY_RESPONSE_BAS])
        self.assertListEqual(expected, actual,
                             msg="FREQUENCY_RESPONSE_BAS set data does not "
                                 "load correctly."
                             )

if __name__ == "__main__":
    unittest.main()
