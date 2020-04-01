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

    def assertDictAlmostEqual(self, d1, d2, msg=None, places=7):

        # check if both inputs are dicts
        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')

        # check if both inputs have the same keys
        self.assertEqual(d1.keys(), d2.keys())

        # check each key
        for key, value in d1.items():
            if isinstance(value, dict):
                self.assertDictAlmostEqual(d1[key], d2[key], msg=msg)
            else:
                self.assertAlmostEqual(d1[key], d2[key], places=places, msg=msg)

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

        # Set: FUEL_COST_PROJECTS
        expected_fuel_projects = sorted([
            "Nuclear", "Gas_CCGT", "Coal", "Gas_CT", "Gas_CCGT_New",
            "Gas_CCGT_New_Binary",
            "Nuclear_z2", "Gas_CCGT_z2", "Coal_z2", "Gas_CT_z2", "Gas_CT_New",
            "Disp_Binary_Commit", "Disp_Cont_Commit", "Disp_No_Commit",
            "Clunky_Old_Gen", "Clunky_Old_Gen2", "Nuclear_Flexible"
        ])
        actual_fuel_projects = sorted([
            prj for prj in instance.FUEL_PRJS
            ])
        self.assertListEqual(expected_fuel_projects,
                             actual_fuel_projects)

        # Param: fuel
        expected_fuel = OrderedDict(sorted({
            "Nuclear": "Uranium",
            "Gas_CCGT": "Gas",
            "Coal": "Coal",
            "Gas_CT": "Gas",
            "Gas_CCGT_New": "Gas",
            "Gas_CCGT_New_Binary": "Gas",
            "Nuclear_z2": "Uranium",
            "Gas_CCGT_z2": "Gas",
            "Coal_z2": "Coal",
            "Gas_CT_z2": "Gas",
            "Gas_CT_New": "Gas",
            "Disp_Binary_Commit": "Gas",
            "Disp_Cont_Commit": "Gas",
            "Disp_No_Commit": "Gas",
            "Clunky_Old_Gen": "Coal",
            "Clunky_Old_Gen2": "Coal",
            "Nuclear_Flexible": "Uranium"
                                           }.items()
                                           )
                                    )
        actual_fuel = OrderedDict(sorted(
            {prj: instance.fuel[prj] for prj in instance.FUEL_PRJS}.items()
        )
        )
        self.assertDictEqual(expected_fuel, actual_fuel)

        # Set: FUEL_PRJ_OPR_TMPS
        expected_tmps_by_fuel_project = sorted(
            get_project_operational_timepoints(expected_fuel_projects)
        )
        actual_tmps_by_fuel_project = sorted([
            (prj, tmp) for (prj, tmp) in
            instance.FUEL_PRJ_OPR_TMPS
                                                 ])
        self.assertListEqual(expected_tmps_by_fuel_project,
                             actual_tmps_by_fuel_project)

        # Set: FUEL_PRJ_SGMS

        expected_fuel_project_segments = sorted([
            ("Nuclear", 0),
            ("Gas_CCGT", 0),
            ("Coal", 0),
            ("Gas_CT", 0),
            ("Gas_CCGT_New", 0),
            ("Gas_CCGT_New_Binary", 0),
            ("Nuclear_z2", 0),
            ("Gas_CCGT_z2", 0),
            ("Coal_z2", 0),
            ("Gas_CT_z2", 0),
            ("Gas_CT_New", 0),
            ("Disp_Binary_Commit", 0),
            ("Disp_Cont_Commit", 0),
            ("Disp_No_Commit", 0),
            ("Clunky_Old_Gen", 0),
            ("Clunky_Old_Gen2", 0),
            ("Nuclear_Flexible", 0)
        ])
        actual_fuel_project_segments = sorted([
            (prj, s) for (prj, s) in instance.FUEL_PRJ_SGMS
            ])
        self.assertListEqual(expected_fuel_project_segments,
                             actual_fuel_project_segments)

        # Set: FUEL_PRJ_SGMS_OPR_TMPS
        expected_fuel_project_segments_operational_timepoints = sorted([
            (g, tmp, s) for (g, tmp) in expected_tmps_by_fuel_project
            for _g, s in expected_fuel_project_segments
            if g in expected_fuel_projects and g == _g
        ])
        actual_fuel_project_segments_operational_timepoints = sorted([
            (prj, tmp, s) for (prj, tmp, s) in
            instance.FUEL_PRJ_SGMS_OPR_TMPS
        ])

        self.assertListEqual(
            expected_fuel_project_segments_operational_timepoints,
            actual_fuel_project_segments_operational_timepoints
        )

        # Param: fuel_burn_slope_mmbtu_per_mwh
        expected_fuel_burn_slope = OrderedDict(sorted({
            ("Nuclear", 0): 1666.67,
            ("Gas_CCGT", 0): 6,
            ("Coal", 0): 10,
            ("Gas_CT", 0): 8,
            ("Gas_CCGT_New", 0): 6,
            ("Gas_CCGT_New_Binary", 0): 6,
            ("Nuclear_z2", 0): 1666.67,
            ("Gas_CCGT_z2", 0): 6,
            ("Coal_z2", 0): 10,
            ("Gas_CT_z2", 0): 8,
            ("Gas_CT_New", 0): 8,
            ("Disp_Binary_Commit", 0): 8,
            ("Disp_Cont_Commit", 0): 8,
            ("Disp_No_Commit", 0): 8,
            ("Clunky_Old_Gen", 0): 15,
            ("Clunky_Old_Gen2", 0): 15,
            ("Nuclear_Flexible", 0): 10
        }.items()))
        actual_fuel_burn_slope = OrderedDict(sorted(
            {(prj, s): instance.fuel_burn_slope_mmbtu_per_mwh[(prj, s)]
             for (prj, s) in instance.FUEL_PRJ_SGMS}.items()
            )
        )

        self.assertDictAlmostEqual(expected_fuel_burn_slope,
                                   actual_fuel_burn_slope,
                                   places=5)

        # Param: fuel_burn_intercept_mmbtu_per_mw_hour
        expected_fuel_burn_intercept = OrderedDict(sorted({
            ("Nuclear", 0): 0,
            ("Gas_CCGT", 0): 250,
            ("Coal", 0): 496,
            ("Gas_CT", 0): 80.13333,
            ("Gas_CCGT_New", 0): 250,
            ("Gas_CCGT_New_Binary", 0): 250,
            ("Nuclear_z2", 0): 0,
            ("Gas_CCGT_z2", 0): 250,
            ("Coal_z2", 0): 496,
            ("Gas_CT_z2", 0): 80.13333,
            ("Gas_CT_New", 0): 80.13333,
            ("Disp_Binary_Commit", 0): 80.13333,
            ("Disp_Cont_Commit", 0): 80.13333,
            ("Disp_No_Commit", 0): 0,
            ("Clunky_Old_Gen", 0): 827.33333,
            ("Clunky_Old_Gen2", 0): 827.33333,
            ("Nuclear_Flexible", 0): 0
        }.items()))
        actual_fuel_burn_intercept = OrderedDict(sorted(
            {(prj, s): instance.fuel_burn_intercept_mmbtu_per_mw_hr[(prj, s)]
             for (prj, s) in instance.FUEL_PRJ_SGMS}.items()
            )
        )

        self.assertDictAlmostEqual(expected_fuel_burn_intercept,
                                   actual_fuel_burn_intercept,
                                   places=5)


    def test_calculate_heat_rate_slope_intercept(self):
        """
        Check that heat rate slope and intercept calculation gives expected
        results for examples with different number of load points
        """
        test_cases = {
            1: {"project": "test1",
                "load_points": np.array([10]),
                "heat_rates": np.array([8]),
                "slopes": {("test1", 0): 8},
                "intercepts": {("test1", 0): 0}},
            2: {"project": "test2",
                "load_points": np.array([5, 10]),
                "heat_rates": np.array([10, 7]),
                "slopes": {("test2", 0): 4},
                "intercepts": {("test2", 0): 30}},
            3: {"project": "test3",
                "load_points": np.array([5, 10, 20]),
                "heat_rates": np.array([10, 7, 6]),
                "slopes": {("test3", 0): 4, ("test3", 1): 5},
                "intercepts": {("test3", 0): 30, ("test3", 1): 20}}
        }
        for test_case in test_cases.keys():
            expected_slopes = test_cases[test_case]["slopes"]
            expected_intercepts = test_cases[test_case]["intercepts"]
            actual_slopes, actual_intercepts = \
                MODULE_BEING_TESTED.calculate_heat_rate_slope_intercept(
                    project=test_cases[test_case]["project"],
                    load_points=test_cases[test_case]["load_points"],
                    heat_rates=test_cases[test_case]["heat_rates"]
                )

            self.assertDictEqual(expected_slopes, actual_slopes)
            self.assertDictEqual(expected_intercepts, actual_intercepts)

    def test_heat_rate_validations(self):
        hr_columns = ["project", "fuel", "heat_rate_curves_scenario_id",
                      "load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"hr_df": pd.DataFrame(
                    columns=hr_columns,
                    data=[["gas_ct", "gas", 1, 10, 10.5],
                          ["gas_ct", "gas", 1, 20, 9],
                          ["coal_plant", "coal", 1, 100, 10]
                          ]),
                "fuel_vs_hr_error": [],
                "hr_curves_error": []
                },
            # Check fuel vs heat rate curve errors
            2: {"hr_df": pd.DataFrame(
                columns=hr_columns,
                data=[["gas_ct", "gas", None, None, None],
                      ["coal_plant", None, 1, 100, 10]
                      ]),
                "fuel_vs_hr_error": ["Project(s) 'gas_ct': Missing heat_rate_curves_scenario_id",
                                     "Project(s) 'coal_plant': No fuel specified so no heat rate expected"],
                "hr_curves_error": []
                },
            # Check heat rate curves validations
            3: {"hr_df": pd.DataFrame(
                columns=hr_columns,
                data=[["gas_ct1", "gas", 1, None, None],
                      ["gas_ct2", "gas", 1, 10, 11],
                      ["gas_ct2", "gas", 1, 10, 12],
                      ["gas_ct3", "gas", 1, 10, 11],
                      ["gas_ct3", "gas", 1, 20, 5],
                      ["gas_ct4", "gas", 1, 10, 11],
                      ["gas_ct4", "gas", 1, 20, 10],
                      ["gas_ct4", "gas", 1, 30, 9]
                      ]),
                "fuel_vs_hr_error": [],
                "hr_curves_error": ["Project(s) 'gas_ct1': Expected at least one load point",
                                    "Project(s) 'gas_ct2': load points can not be identical",
                                    "Project(s) 'gas_ct3': Total fuel burn should increase with increasing load",
                                    "Project(s) 'gas_ct4': Fuel burn should be convex, i.e. marginal heat rate should increase with increading load"]
                },

        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["fuel_vs_hr_error"]
            actual_list = MODULE_BEING_TESTED.validate_fuel_vs_heat_rates(
                hr_df=test_cases[test_case]["hr_df"]
            )
            self.assertListEqual(expected_list, actual_list)

            expected_list = test_cases[test_case]["hr_curves_error"]
            actual_list = MODULE_BEING_TESTED.validate_heat_rate_curves(
                hr_df=test_cases[test_case]["hr_df"]
            )
            self.assertListEqual(expected_list, actual_list)


if __name__ == "__main__":
    unittest.main()
