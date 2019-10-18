#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data
from tests.project.operations.common_functions import \
    get_project_operational_timepoints

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
     "temporal.operations.timepoints", "temporal.operations.horizons",
     "temporal.investment.periods", "geography.load_zones", "project",
     "project.capacity.capacity", "project.availability.availability",
    "project.fuels", "project.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.storage_generic"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package="gridpath")
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package="gridpath")
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestStorageGenericOperationalType(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=IMPORTED_PREREQ_MODULES,
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
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
                                     )

    def test_capacity_data_load_correctly(self):
        """
        Test that are data loaded are as expected
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Sets: STORAGE_GENERIC_PROJECTS
        expected_projects = ["Battery", "Battery_Binary", "Battery_Specified"]
        actual_projects = sorted(
            [p for p in instance.STORAGE_GENERIC_PROJECTS]
        )
        self.assertListEqual(expected_projects, actual_projects)

        # STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps = sorted(
            get_project_operational_timepoints(expected_projects)
        )
        actual_tmps = sorted([
            tmp for tmp in
            instance.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS
            ])
        self.assertListEqual(expected_tmps, actual_tmps)

        # Param: storage_generic_charging_efficiency
        expected_charging_efficiency = {
            "Battery": 0.8, "Battery_Binary": 0.8, "Battery_Specified": 0.8
        }
        actual_charging_efficiency = {
            prj: instance.storage_generic_charging_efficiency[prj]
            for prj in instance.STORAGE_GENERIC_PROJECTS
        }
        self.assertDictEqual(expected_charging_efficiency,
                             actual_charging_efficiency)

        # Param: storage_generic_discharging_efficiency
        expected_discharging_efficiency = {
            "Battery": 0.8, "Battery_Binary": 0.8, "Battery_Specified": 0.8
        }
        actual_discharging_efficiency = {
            prj: instance.storage_generic_discharging_efficiency[prj]
            for prj in instance.STORAGE_GENERIC_PROJECTS
        }
        self.assertDictEqual(expected_discharging_efficiency,
                             actual_discharging_efficiency)


if __name__ == "__main__":
    unittest.main()
