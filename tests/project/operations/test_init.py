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

        # Params: variable_om_cost_per_mwh
        projects_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "projects.tab"),
                sep="\t", usecols=[
                    'project', "variable_om_cost_per_mwh"
                ]
            )
        expected_var_om_cost = OrderedDict(
            sorted(
                projects_df.set_index('project').to_dict()[
                    'variable_om_cost_per_mwh'].items()
            )
        )
        actual_var_om_cost = OrderedDict(
            sorted(
                {prj: instance.variable_om_cost_per_mwh[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_var_om_cost, actual_var_om_cost)

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

        # Set: FUEL_PRJ_PRD_SGMS

        expected_fuel_project_period_segments = sorted([
            ("Nuclear", 2020, 0),
            ("Gas_CCGT", 2020, 0),
            ("Coal", 2020, 0),
            ("Gas_CT", 2020, 0),
            ("Gas_CCGT_New", 2020, 0),
            ("Gas_CCGT_New_Binary", 2020, 0),
            ("Nuclear_z2", 2020, 0),
            ("Gas_CCGT_z2", 2020, 0),
            ("Coal_z2", 2020, 0),
            ("Gas_CT_z2", 2020, 0),
            ("Gas_CT_New", 2020, 0),
            ("Disp_Binary_Commit", 2020, 0),
            ("Disp_Cont_Commit", 2020, 0),
            ("Disp_No_Commit", 2020, 0),
            ("Clunky_Old_Gen", 2020, 0),
            ("Clunky_Old_Gen2", 2020, 0),
            ("Nuclear_Flexible", 2020, 0),
            ("Nuclear", 2030, 0),
            ("Gas_CCGT", 2030, 0),
            ("Coal", 2030, 0),
            ("Gas_CT", 2030, 0),
            ("Gas_CCGT_New", 2030, 0),
            ("Gas_CCGT_New_Binary", 2030, 0),
            ("Nuclear_z2", 2030, 0),
            ("Gas_CCGT_z2", 2030, 0),
            ("Coal_z2", 2030, 0),
            ("Gas_CT_z2", 2030, 0),
            ("Gas_CT_New", 2030, 0),
            ("Disp_Binary_Commit", 2030, 0),
            ("Disp_Cont_Commit", 2030, 0),
            ("Disp_No_Commit", 2030, 0),
            ("Clunky_Old_Gen", 2030, 0),
            ("Clunky_Old_Gen2", 2030, 0),
            ("Nuclear_Flexible", 2030, 0)
        ])
        actual_fuel_project_period_segments = sorted([
            (prj, p, s) for (prj, p, s) in instance.FUEL_PRJ_PRD_SGMS
            ])
        self.assertListEqual(expected_fuel_project_period_segments,
                             actual_fuel_project_period_segments)

        # Set: FUEL_PRJ_SGMS_OPR_TMPS
        timepoints_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
            sep="\t",
            usecols=['timepoint', 'period']
        )

        expected_period_param = \
            timepoints_df.set_index('timepoint').to_dict()['period']

        expected_fuel_project_segments_operational_timepoints = sorted([
            (g, tmp, s) for (g, tmp) in expected_tmps_by_fuel_project
            for _g, p, s in expected_fuel_project_period_segments
            if g in expected_fuel_projects and g == _g
            and expected_period_param[tmp] == p
        ])
        actual_fuel_project_segments_operational_timepoints = sorted([
            (prj, tmp, s) for (prj, tmp, s) in
            instance.FUEL_PRJ_SGMS_OPR_TMPS
        ])

        self.assertListEqual(
            expected_fuel_project_segments_operational_timepoints,
            actual_fuel_project_segments_operational_timepoints
        )

        # Set: VOM_PRJS_PRDS_SGMS
        expected_vom_project_period_segments = sorted([
            ("Disp_Binary_Commit", 2020, 0),
            ("Disp_Binary_Commit", 2030, 0),
            ("Disp_Cont_Commit", 2020, 0),
            ("Disp_Cont_Commit", 2030, 0),
        ])
        actual_vom_project_period_segments = sorted([
            (prj, p, s) for (prj, p, s) in instance.VOM_PRJS_PRDS_SGMS
            ])
        self.assertListEqual(expected_vom_project_period_segments,
                             actual_vom_project_period_segments)

        # Set: VOM_PRJS_OPR_TMPS_SGMS
        expected_prj_opr_tmps = sorted(
            get_project_operational_timepoints(["Disp_Binary_Commit",
                                                "Disp_Cont_Commit"])
        )
        expected_vom_project_segments_operational_timepoints = sorted([
            (g, tmp, 0) for (g, tmp) in expected_prj_opr_tmps
        ])
        actual_vom_project_segments_operational_timepoints = sorted([
            (prj, tmp, s) for (prj, tmp, s) in
            instance.VOM_PRJS_OPR_TMPS_SGMS
        ])

        self.assertListEqual(
            expected_vom_project_segments_operational_timepoints,
            actual_vom_project_segments_operational_timepoints
        )

        # Param: fuel_burn_slope_mmbtu_per_mwh
        expected_fuel_burn_slope = OrderedDict(sorted({
            ("Nuclear", 2020, 0): 1666.67,
            ("Gas_CCGT", 2020, 0): 6,
            ("Coal", 2020, 0): 10,
            ("Gas_CT", 2020, 0): 8,
            ("Gas_CCGT_New", 2020, 0): 6,
            ("Gas_CCGT_New_Binary", 2020, 0): 6,
            ("Nuclear_z2", 2020, 0): 1666.67,
            ("Gas_CCGT_z2", 2020, 0): 6,
            ("Coal_z2", 2020, 0): 10,
            ("Gas_CT_z2", 2020, 0): 8,
            ("Gas_CT_New", 2020, 0): 8,
            ("Disp_Binary_Commit", 2020, 0): 8,
            ("Disp_Cont_Commit", 2020, 0): 8,
            ("Disp_No_Commit", 2020, 0): 8,
            ("Clunky_Old_Gen", 2020, 0): 15,
            ("Clunky_Old_Gen2", 2020, 0): 15,
            ("Nuclear_Flexible", 2020, 0): 10,
            ("Nuclear", 2030, 0): 1666.67,
            ("Gas_CCGT", 2030, 0): 6,
            ("Coal", 2030, 0): 10,
            ("Gas_CT", 2030, 0): 8,
            ("Gas_CCGT_New", 2030, 0): 6,
            ("Gas_CCGT_New_Binary", 2030, 0): 6,
            ("Nuclear_z2", 2030, 0): 1666.67,
            ("Gas_CCGT_z2", 2030, 0): 6,
            ("Coal_z2", 2030, 0): 10,
            ("Gas_CT_z2", 2030, 0): 8,
            ("Gas_CT_New", 2030, 0): 8,
            ("Disp_Binary_Commit", 2030, 0): 8,
            ("Disp_Cont_Commit", 2030, 0): 8,
            ("Disp_No_Commit", 2030, 0): 8,
            ("Clunky_Old_Gen", 2030, 0): 15,
            ("Clunky_Old_Gen2", 2030, 0): 15,
            ("Nuclear_Flexible", 2030, 0): 9,
        }.items()))
        actual_fuel_burn_slope = OrderedDict(sorted(
            {(prj, p, s): instance.fuel_burn_slope_mmbtu_per_mwh[(prj, p, s)]
             for (prj, p, s) in instance.FUEL_PRJ_PRD_SGMS}.items()
            )
        )

        self.assertDictAlmostEqual(expected_fuel_burn_slope,
                                   actual_fuel_burn_slope,
                                   places=5)

        # Param: fuel_burn_intercept_mmbtu_per_mw_hour
        expected_fuel_burn_intercept = OrderedDict(sorted({
            ("Nuclear", 2020, 0): 0,
            ("Gas_CCGT", 2020, 0): 250,
            ("Coal", 2020, 0): 496,
            ("Gas_CT", 2020, 0): 80.13333,
            ("Gas_CCGT_New", 2020, 0): 250,
            ("Gas_CCGT_New_Binary", 2020, 0): 250,
            ("Nuclear_z2", 2020, 0): 0,
            ("Gas_CCGT_z2", 2020, 0): 250,
            ("Coal_z2", 2020, 0): 496,
            ("Gas_CT_z2", 2020, 0): 80.13333,
            ("Gas_CT_New", 2020, 0): 80.13333,
            ("Disp_Binary_Commit", 2020, 0): 80.13333,
            ("Disp_Cont_Commit", 2020, 0): 80.13333,
            ("Disp_No_Commit", 2020, 0): 0,
            ("Clunky_Old_Gen", 2020, 0): 827.33333,
            ("Clunky_Old_Gen2", 2020, 0): 827.33333,
            ("Nuclear_Flexible", 2020, 0): 0,
            ("Nuclear", 2030, 0): 0,
            ("Gas_CCGT", 2030, 0): 250,
            ("Coal", 2030, 0): 496,
            ("Gas_CT", 2030, 0): 80.13333,
            ("Gas_CCGT_New", 2030, 0): 250,
            ("Gas_CCGT_New_Binary", 2030, 0): 250,
            ("Nuclear_z2", 2030, 0): 0,
            ("Gas_CCGT_z2", 2030, 0): 250,
            ("Coal_z2", 2030, 0): 496,
            ("Gas_CT_z2", 2030, 0): 80.13333,
            ("Gas_CT_New", 2030, 0): 80.13333,
            ("Disp_Binary_Commit", 2030, 0): 80.13333,
            ("Disp_Cont_Commit", 2030, 0): 80.13333,
            ("Disp_No_Commit", 2030, 0): 0,
            ("Clunky_Old_Gen", 2030, 0): 827.33333,
            ("Clunky_Old_Gen2", 2030, 0): 827.33333,
            ("Nuclear_Flexible", 2030, 0): 0
        }.items()))
        actual_fuel_burn_intercept = OrderedDict(sorted(
            {(prj, p, s): instance.fuel_burn_intercept_mmbtu_per_mw_hr[
                (prj, p, s)]
             for (prj, p, s) in instance.FUEL_PRJ_PRD_SGMS}.items()
            )
        )

        self.assertDictAlmostEqual(expected_fuel_burn_intercept,
                                   actual_fuel_burn_intercept,
                                   places=5)

        # Param: vom_slope_cost_per_mwh
        expected_vom_slope = OrderedDict(sorted({
            ("Disp_Binary_Commit", 2020, 0): 1,
            ("Disp_Binary_Commit", 2030, 0): 1,
            ("Disp_Cont_Commit", 2020, 0): 1,
            ("Disp_Cont_Commit", 2030, 0): 1,
        }.items()))
        actual_vom_slope = OrderedDict(sorted(
            {(prj, p, s): instance.vom_slope_cost_per_mwh[(prj, p, s)]
             for (prj, p, s) in instance.VOM_PRJS_PRDS_SGMS}.items()
            )
        )

        self.assertDictAlmostEqual(expected_vom_slope,
                                   actual_vom_slope,
                                   places=5)

        # Param: vom_intercept_cost_per_mw_hour
        expected_vom_intercept = OrderedDict(sorted({
            ("Disp_Binary_Commit", 2020, 0): 0.5,
            ("Disp_Binary_Commit", 2030, 0): 0.5,
            ("Disp_Cont_Commit", 2020, 0): 0,
            ("Disp_Cont_Commit", 2030, 0): 0,
        }.items()))
        actual_vom_intercept = OrderedDict(sorted(
            {(prj, p, s): instance.vom_intercept_cost_per_mw_hr[(prj, p, s)]
             for (prj, p, s) in instance.VOM_PRJS_PRDS_SGMS}.items()
            )
        )

        self.assertDictAlmostEqual(expected_vom_intercept,
                                   actual_vom_intercept,
                                   places=5)

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
                MODULE_BEING_TESTED.get_slopes_intercept_by_project_period_segment(
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
                MODULE_BEING_TESTED.calculate_slope_intercept(
                    project=test_cases[test_case]["project"],
                    load_points=test_cases[test_case]["load_points"],
                    heat_rates=test_cases[test_case]["heat_rates"]
                )

            self.assertListEqual(expected_slopes.tolist(),
                                 actual_slopes.tolist())
            self.assertListEqual(expected_intercepts.tolist(),
                                 actual_intercepts.tolist())

    def test_project_validations(self):
        cols = ["project", "min_stable_level"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.5]
                          ]),
                "min_stable_level_error": [],
                },
            # Make sure invalid min_stable_level is flagged
            2: {"df": pd.DataFrame(
                columns=cols,
                data=[["gas_ct1", 1.5],
                      ["gas_ct2", 0]
                      ]),
                "min_stable_level_error": ["Project(s) 'gas_ct1, gas_ct2': expected 0 < min_stable_level <= 1"],
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["min_stable_level_error"]
            actual_list = MODULE_BEING_TESTED.validate_min_stable_level(
                df=test_cases[test_case]["df"]
            )
            self.assertListEqual(expected_list, actual_list)

    # TODO: add periods column for completeness
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
