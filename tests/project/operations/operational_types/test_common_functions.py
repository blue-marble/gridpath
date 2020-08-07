#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from importlib import import_module
import numpy as np
import os.path
import pandas as pd
import sys
import unittest

from tests.common_functions import add_components_and_load_data

from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, calculate_slope_intercept, \
    get_slopes_intercept_by_project_period_segment

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
            actual_list, actual_linked_tmps = determine_relevant_timepoints(
                mod=instance,
                g=test_cases[test_case]["g"],
                tmp=test_cases[test_case]["tmp"],
                min_time=test_cases[test_case]["min_time"]
            )

            self.assertListEqual(expected_list, actual_list)
            # No linked timepoints, so check that the list is empty in every
            # test case
            self.assertListEqual([], actual_linked_tmps)

    def test_determine_relevant_linked_timepoints(self):
        """
        Check that the lists of relevant timepoints and relevant linked
        timepoints are as expected based on the current timepoint and the
        minimum up/down time (and, on the data side, the duration of other
        timepoints).
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=None,  # No need to name since not adding components
            test_data_dir=os.path.join(TEST_DATA_DIRECTORY, "subproblems"),
            subproblem="202002",
            stage=""
        )
        instance = m.create_instance(data)

        test_cases = {
            1: {"min_time": 4, "g": "Gas_CCGT", "tmp": 20200203,
                "relevant_timepoints": [20200203, 20200202, 20200201],
                "relevant_linked_timepoints": [0]},
            2: {"min_time": 5, "g": "Gas_CCGT", "tmp": 20200203,
                "relevant_timepoints": [20200203, 20200202, 20200201],
                "relevant_linked_timepoints": [0, -1]},
            # Stop at the last included linked timepoint if the min time is
            # longer than the total duration of the current timepoint to the
            # last linked timepoint
            3: {"min_time": 24, "g": "Gas_CCGT", "tmp": 20200203,
                "relevant_timepoints": [20200203, 20200202, 20200201],
                "relevant_linked_timepoints": [0, -1, -2, -3, -4, -5, -6,
                                               -7, -8, -9, -10, -11]},
            # No linked timepoint if min time does not reach them
            4: {"min_time": 1, "g": "Gas_CCGT", "tmp": 20200203,
                "relevant_timepoints": [20200203],
                "relevant_linked_timepoints": []},
            # Starting in the first timepoint of the horizon
            5: {"min_time": 4, "g": "Gas_CCGT", "tmp": 20200201,
                "relevant_timepoints": [20200201],
                "relevant_linked_timepoints": [0, -1, -2]},
        }

        for test_case in test_cases.keys():
            expected_rel_tmp_list = test_cases[test_case][
                "relevant_timepoints"]
            expected_rel_linked_tmp_list = test_cases[test_case][
                "relevant_linked_timepoints"]
            actual_rel_tmp_list, actual_rel_linked_tmp_list = \
                determine_relevant_timepoints(
                    mod=instance,
                    g=test_cases[test_case]["g"],
                    tmp=test_cases[test_case]["tmp"],
                    min_time=test_cases[test_case]["min_time"]
                )

            self.assertListEqual(expected_rel_tmp_list, actual_rel_tmp_list)
            self.assertListEqual(actual_rel_linked_tmp_list,
                                 expected_rel_linked_tmp_list)

    def test_get_slopes_intercept_by_project_period_segment(self):
        """
        Check that slope and intercept dictionaries are correctly constructed
        from the input data frames
        :return:
        """
        hr_columns = ["project", "period", "load_point_fraction",
                      "average_heat_rate_mmbtu_per_mwh"]
        vom_columns = ["project", "period", "load_point_fraction",
                       "average_variable_om_cost_per_mwh"]
        test_cases = {
            # Check heat rates curves
            1: {"df": pd.DataFrame(
                columns=hr_columns,
                data=[["gas_ct", 2020, 0.5, 10],
                      ["gas_ct", 2020, 1, 7],
                      ["coal_plant", 2020, 1, 10]
                      ]),
                "input_col": "average_heat_rate_mmbtu_per_mwh",
                "projects": ["gas_ct", "coal_plant"],
                "periods": {2020},
                "slope_dict": {("gas_ct", 2020, 0): 4,
                               ("coal_plant", 2020, 0): 10},
                "intercept_dict": {("gas_ct", 2020, 0): 3,
                                   ("coal_plant", 2020, 0): 0}
                },
            # Check VOM curves
            2: {"df": pd.DataFrame(
                columns=vom_columns,
                data=[["gas_ct", 2020, 0.5, 2],
                      ["gas_ct", 2020, 1, 1.5],
                      ["coal_plant", 2020, 1, 3]
                      ]),
                "input_col": "average_variable_om_cost_per_mwh",
                "projects": ["gas_ct", "coal_plant"],
                "periods": {2020},
                "slope_dict": {("gas_ct", 2020, 0): 1,
                               ("coal_plant", 2020, 0): 3},
                "intercept_dict": {("gas_ct", 2020, 0): 0.5,
                                   ("coal_plant", 2020, 0): 0}
                },
            # Check that "0" input for period results in same inputs for all
            3: {"df": pd.DataFrame(
                columns=hr_columns,
                data=[["gas_ct", 0, 0.5, 10],
                      ["gas_ct", 0, 1, 7],
                      ["coal_plant", 0, 1, 10]
                      ]),
                "input_col": "average_heat_rate_mmbtu_per_mwh",
                "projects": ["gas_ct", "coal_plant"],
                "periods": {2020, 2030},
                "slope_dict": {("gas_ct", 2020, 0): 4,
                               ("gas_ct", 2030, 0): 4,
                               ("coal_plant", 2020, 0): 10,
                               ("coal_plant", 2030, 0): 10},
                "intercept_dict": {("gas_ct", 2020, 0): 3,
                                   ("gas_ct", 2030, 0): 3,
                                   ("coal_plant", 2020, 0): 0,
                                   ("coal_plant", 2030, 0): 0}
                }
        }
        for test_case in test_cases.keys():
            expected_slope_dict = test_cases[test_case]["slope_dict"]
            expected_intercept_dict = test_cases[test_case]["intercept_dict"]
            actual_slope_dict, actual_intercept_dict = \
                get_slopes_intercept_by_project_period_segment(
                    df=test_cases[test_case]["df"],
                    input_col=test_cases[test_case]["input_col"],
                    projects=test_cases[test_case]["projects"],
                    periods=test_cases[test_case]["periods"]
                )

            self.assertDictEqual(expected_slope_dict, actual_slope_dict)
            self.assertDictEqual(expected_intercept_dict,
                                 actual_intercept_dict)

    # TODO: re-scale load points to fractions
    def test_calculate_slope_intercept(self):
        """
        Check that slope and intercept calculation gives expected
        results for examples with different number of load points
        """
        test_cases = {
            1: {"project": "test1",
                "load_points": np.array([10]),
                "heat_rates": np.array([8]),
                "slopes": np.array([8]),
                "intercepts": np.array([0])},
            2: {"project": "test2",
                "load_points": np.array([5, 10]),
                "heat_rates": np.array([10, 7]),
                "slopes": np.array([4]),
                "intercepts": np.array([30])},
            3: {"project": "test3",
                "load_points": np.array([5, 10, 20]),
                "heat_rates": np.array([10, 7, 6]),
                "slopes": np.array([4, 5]),
                "intercepts": np.array([30, 20])}
        }
        for test_case in test_cases.keys():
            expected_slopes = test_cases[test_case]["slopes"]
            expected_intercepts = test_cases[test_case]["intercepts"]
            actual_slopes, actual_intercepts = \
                calculate_slope_intercept(
                    project=test_cases[test_case]["project"],
                    load_points=test_cases[test_case]["load_points"],
                    heat_rates=test_cases[test_case]["heat_rates"]
                )

            self.assertListEqual(expected_slopes.tolist(),
                                 actual_slopes.tolist())
            self.assertListEqual(expected_intercepts.tolist(),
                                 actual_intercepts.tolist())
