#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import add_components_and_load_data

from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, determine_startup_elapsed_time

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "geography.load_zones",
    "project.__init__"
]
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='gridpath')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)


class TestOperationalTypeCommonFunctions(unittest.TestCase):
    """
    Test the common_functions module in the operational types package.
    """
    def test_determine_relevant_timepoints(self):
        """
        Check that the list of relevant timepoints is as expected based on
        the current timepoint and the minimum up/down time (and, on the data
        side, the duration of other timepoints). Add any other cases to
        check that the 'determine_relevant_timepoints' function gives the
        expected results.
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=None,  # No need to name since not adding components
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        test_cases = {
            1: {"min_time": 4, "g": "Gas_CCGT", "tmp": 20200103,
                "relevant_timepoints": [20200103, 20200102]},
            2: {"min_time": 5, "g": "Gas_CCGT", "tmp": 20200103,
                "relevant_timepoints":
                    [20200103, 20200102, 20200101, 20200124, 20200123]},
            3: {"min_time": 8, "g": "Gas_CCGT", "tmp": 20200103,
                "relevant_timepoints":
                    [20200103, 20200102, 20200101, 20200124, 20200123,
                     20200122, 20200121]},
            4: {"min_time": 1, "g": "Gas_CCGT", "tmp": 20200120,
                "relevant_timepoints": [20200120, 20200119, 20200118]},
            5: {"min_time": 2, "g": "Gas_CCGT", "tmp": 20200120,
                "relevant_timepoints":
                    [20200120, 20200119, 20200118, 20200117]},
            6: {"min_time": 3, "g": "Gas_CCGT", "tmp": 20200120,
                "relevant_timepoints":
                    [20200120, 20200119, 20200118, 20200117, 20200116]},
            # Test min times of longer duration than the horizon in a
            # 'circular' horizon setting
            7: {"min_time": 100, "g": "Gas_CCGT", "tmp": 20200101,
                "relevant_timepoints":
                    [20200101, 20200124, 20200123, 20200122, 20200121,
                     20200120, 20200119, 20200118, 20200117, 20200116,
                     20200115, 20200114, 20200113, 20200112, 20200111,
                     20200110, 20200109, 20200108, 20200107, 20200106,
                     20200105, 20200104, 20200103, 20200102, 20200101]},
            # If we're in the first timepoint of a linear horizon, test that
            # we only get that timepoint (i.e. that we break out of the loop
            # before adding any more timepoints)
            8: {"min_time": 100, "g": "Gas_CCGT", "tmp": 20200201,
                "relevant_timepoints": [20200201]},
            # Test that we break out of the loop with min times that reach the
            # first horizon timepoint in a 'linear' horizon setting
            9: {"min_time": 100, "g": "Gas_CCGT", "tmp": 20200202,
                "relevant_timepoints": [20200202, 20200201]}
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["relevant_timepoints"]
            actual_list = determine_relevant_timepoints(
                mod=instance,
                g=test_cases[test_case]["g"],
                tmp=test_cases[test_case]["tmp"],
                min_time=test_cases[test_case]["min_time"]
            )

            self.assertListEqual(expected_list, actual_list)

    def test_determine_startup_elapsed_time(self):
        """
        Check that the calculated of the elapsed time into the startup is
        as expected
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=None,  # No need to name since not adding components
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        test_cases = {
            1: {"startup_duration": 4, "g": "Gas_CCGT",
                "tmp1": 20200103, "tmp2": 20200105, "elapsed_time": 2},
            # Test tmp1 = tmp2
            2: {"startup_duration": 4, "g": "Gas_CCGT",
                "tmp1": 20200103, "tmp2": 20200103, "elapsed_time": 4},
            # Test variable timepoint duration
            3: {"startup_duration": 4, "g": "Gas_CCGT",
                "tmp1": 20200102, "tmp2": 20200103, "elapsed_time": 1},
            # Test variable timepoint duration
            4: {"startup_duration": 4, "g": "Gas_CCGT",
                "tmp1": 20200113, "tmp2": 20200115, "elapsed_time": 1.61},
            # Test that zero is returned when time between tmps is larger than
            # the startup_duration.
            5: {"startup_duration": 4, "g": "Gas_CCGT",
                "tmp1": 20200101, "tmp2": 20200110, "elapsed_time": 0}
        }

        for test_case in test_cases.keys():
            expected = test_cases[test_case]["elapsed_time"]
            actual = determine_startup_elapsed_time(
                mod=instance,
                g=test_cases[test_case]["g"],
                tmp1=test_cases[test_case]["tmp1"],
                tmp2=test_cases[test_case]["tmp2"],
                startup_duration=test_cases[test_case]["startup_duration"]
            )

            self.assertAlmostEqual(expected, actual, 3)


if __name__ == "__main__":
    unittest.main()
