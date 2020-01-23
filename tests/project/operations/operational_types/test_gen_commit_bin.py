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
    "project.operations.operational_types.gen_commit_bin"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='gridpath')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestDispatchableBinaryCommitOperationalType(unittest.TestCase):
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

    def test_data_loaded_correctly(self):
        """
        Test that the data loaded are as expected
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

        # Set: DISPATCHABLE_BINARY_COMMIT_GENERATORS
        expected_disp_bin_commit_gen_set = sorted([
            "Disp_Binary_Commit"
        ])
        actual_disp_bin_commit_gen_set = sorted([
            prj for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
            ])
        self.assertListEqual(expected_disp_bin_commit_gen_set,
                             actual_disp_bin_commit_gen_set)

        # Set: DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS
        expected_operational_timepoints_by_project = sorted(
            get_project_operational_timepoints(
                expected_disp_bin_commit_gen_set
            )
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.
                DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timepoints_by_project,
                             actual_operational_timepoints_by_project)

        # Param: disp_binary_commit_min_stable_level_fraction
        expected_min_stable_fraction = {"Disp_Binary_Commit": 0.4}
        actual_min_stable_fraction = {
            prj: instance.disp_binary_commit_min_stable_level_fraction[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_min_stable_fraction,
                             actual_min_stable_fraction)

        # Param: dispbincommit_startup_plus_ramp_up_rate
        expected_startup_plus_ramp_up_rate = {"Disp_Binary_Commit": 0.6}
        actual_startup_plus_ramp_up_rate = {
            prj: instance.dispbincommit_startup_plus_ramp_up_rate[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_startup_plus_ramp_up_rate,
                             actual_startup_plus_ramp_up_rate)

        # Param: dispbincommit_shutdown_plus_ramp_down_rate
        expected_shutdown_plus_ramp_down_rate = {"Disp_Binary_Commit": 0.6}
        actual_shutdown_plus_ramp_down_rate = {
            prj: instance.dispbincommit_shutdown_plus_ramp_down_rate[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_shutdown_plus_ramp_down_rate,
                             actual_shutdown_plus_ramp_down_rate)

        # Param: dispbincommit_ramp_up_when_on_rate
        expected_ramp_up_when_on_rate = {"Disp_Binary_Commit": 0.3}
        actual_ramp_down_when_on_rate = {
            prj: instance.dispbincommit_ramp_up_when_on_rate[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_ramp_up_when_on_rate,
                             actual_ramp_down_when_on_rate)

        # Param: dispbincommit_ramp_down_when_on_rate
        expected_ramp_down_when_on_rate = {"Disp_Binary_Commit": 0.5}
        actual_ramp_down_when_on_rate = {
            prj: instance.dispbincommit_ramp_down_when_on_rate[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_ramp_down_when_on_rate,
                             actual_ramp_down_when_on_rate)

        # Param: dispbincommit_min_up_time_hours
        expected_min_up_time = {"Disp_Binary_Commit": 3}
        actual_min_up_time = {
            prj: instance.dispbincommit_min_up_time_hours[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }

        self.assertDictEqual(expected_min_up_time,
                             actual_min_up_time)

        # Param: dispbincommit_min_down_time_hours
        expected_min_down_time = {"Disp_Binary_Commit": 7}
        actual_min_down_time = {
            prj: instance.dispbincommit_min_down_time_hours[prj]
            for prj in instance.DISPATCHABLE_BINARY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_min_down_time,
                             actual_min_down_time)


if __name__ == "__main__":
    unittest.main()
