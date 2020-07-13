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
    "project.operations.operational_types.gen_always_on"
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


class TestGenAlwaysOn(unittest.TestCase):
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
        Test components initialized with data as expected
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

        # Set: GEN_ALWAYS_ON
        expected_always_on_gen_set = sorted([
            "Nuclear_Flexible"
        ])
        actual_always_on_gen_set = sorted([
            prj for prj in instance.GEN_ALWAYS_ON
        ])
        self.assertListEqual(expected_always_on_gen_set,
                             actual_always_on_gen_set)

        # Set: GEN_ALWAYS_ON_OPR_TMPS
        expected_operational_timpoints_by_project = sorted(
            get_project_operational_timepoints(expected_always_on_gen_set)
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.GEN_ALWAYS_ON_OPR_TMPS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_timepoints_by_project)

        # Set: GEN_ALWAYS_ON_VOM_PRJS_PRDS_SGMS
        expected_vom_project_period_segments = sorted([
        ])
        actual_vom_project_period_segments = sorted([
            (prj, p, s)
            for (prj, p, s) in instance.GEN_ALWAYS_ON_VOM_PRJS_PRDS_SGMS
            ])
        self.assertListEqual(expected_vom_project_period_segments,
                             actual_vom_project_period_segments)

        # Set: GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS
        expected_prj_opr_tmps = sorted(
            get_project_operational_timepoints([])
        )
        expected_vom_project_segments_operational_timepoints = sorted([
            (g, tmp, 0) for (g, tmp) in expected_prj_opr_tmps
        ])
        actual_vom_project_segments_operational_timepoints = sorted([
            (prj, tmp, s) for (prj, tmp, s) in
            instance.GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS
        ])

        self.assertListEqual(
            expected_vom_project_segments_operational_timepoints,
            actual_vom_project_segments_operational_timepoints
        )

        # Param: gen_always_on_unit_size_mw
        expected_unit_size = {
            "Nuclear_Flexible": 584
        }
        actual_unit_size = {
            prj: instance.gen_always_on_unit_size_mw[prj]
            for prj in instance.GEN_ALWAYS_ON
        }
        self.assertDictEqual(expected_unit_size,
                             actual_unit_size)

        # Param: gen_always_on_min_stable_level_fraction
        expected_min_stable_fraction = {
            "Nuclear_Flexible": 0.72
        }
        actual_min_stable_fraction = {
            prj: instance.gen_always_on_min_stable_level_fraction[prj]
            for prj in instance.GEN_ALWAYS_ON
        }
        self.assertDictEqual(expected_min_stable_fraction,
                             actual_min_stable_fraction
                             )

        # Params: gen_always_on_variable_om_cost_per_mwh
        expected_var_om_cost = {"Nuclear_Flexible": 1}
        actual_var_om_cost = {
            prj: instance.gen_always_on_variable_om_cost_per_mwh[prj]
            for prj in instance.GEN_ALWAYS_ON
        }

        self.assertDictEqual(expected_var_om_cost, actual_var_om_cost)

        # Param: gen_always_on_vom_slope_cost_per_mwh
        expected_vom_slope = {}
        actual_vom_slope = {
            (prj, p, s):
                instance.gen_always_on_vom_slope_cost_per_mwh[(prj, p, s)]
             for (prj, p, s) in instance.GEN_ALWAYS_ON_VOM_PRJS_PRDS_SGMS
        }

        self.assertDictAlmostEqual(expected_vom_slope,
                                   actual_vom_slope,
                                   places=5)

        # Param: gen_always_on_vom_intercept_cost_per_mw_hour
        expected_vom_intercept = {}
        actual_vom_intercept = {
            (prj, p, s):
                instance.gen_always_on_vom_intercept_cost_per_mw_hr[(prj,p, s)]
             for (prj, p, s) in
             instance.GEN_ALWAYS_ON_VOM_PRJS_PRDS_SGMS
        }

        # Param: gen_always_on_ramp_up_when_on_rate
        expected_ramp_up_when_on_rate = {
            "Nuclear_Flexible": 0.18
        }
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_always_on_ramp_up_when_on_rate[prj]
            for prj in instance.GEN_ALWAYS_ON
        }
        self.assertDictEqual(expected_ramp_up_when_on_rate,
                             actual_ramp_down_when_on_rate
                             )

        # Param: gen_always_on_ramp_down_when_on_rate
        expected_ramp_down_when_on_rate = {
            "Nuclear_Flexible": 0.18
        }
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_always_on_ramp_down_when_on_rate[
                prj]
            for prj in instance.GEN_ALWAYS_ON
        }
        self.assertDictEqual(expected_ramp_down_when_on_rate,
                             actual_ramp_down_when_on_rate
                             )


if __name__ == "__main__":
    unittest.main()
