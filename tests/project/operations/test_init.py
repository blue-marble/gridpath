#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest
import numpy as np
import pandas as pd

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data
from tests.project.operations.common_functions import \
    get_project_operational_timepoints

from gridpath.project.operations import calculate_slope_intercept, \
    get_slopes_intercept_by_project_period_segment

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity", "project.availability.availability",
    "project.fuels"
]
NAME_OF_MODULE_BEING_TESTED = "project.operations"
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


class TestOperationsInit(unittest.TestCase):
    """

    """

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


if __name__ == "__main__":
    unittest.main()
