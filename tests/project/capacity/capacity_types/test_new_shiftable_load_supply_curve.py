#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "project"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.capacity.capacity_types.new_shiftable_load_supply_curve"
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


class TestNewShiftableLoadSupplyCurve(unittest.TestCase):
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

        # Set: NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS
        expected_projects = ["Shift_DR"]
        actual_projects = sorted(
            [prj for prj in instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS]
        )
        self.assertListEqual(expected_projects,
                             actual_projects)

        # Param: shiftable_load_supply_curve_min_duration
        expected_duration = OrderedDict(
            sorted({"Shift_DR": 6}.items())
        )
        actual_duration = OrderedDict(
            sorted(
                {prj: instance.shiftable_load_supply_curve_min_duration[prj]
                 for prj in instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_duration, actual_duration)

        # Param: new_shiftable_load_supply_curve_min_cumulative_new_build_mwh
        expected_min_build = OrderedDict(
            sorted({("Shift_DR", 2020): 1,
                    ("Shift_DR", 2030): 2}.items())
        )
        actual_min_build = OrderedDict(
            sorted(
                {(prj, p): instance.
                new_shiftable_load_supply_curve_min_cumulative_new_build_mwh[
                    prj, p]
                 for prj in
                 instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS
                 for p in instance.PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_build, actual_min_build)

        # Param: new_shiftable_load_supply_curve_max_cumulative_new_build_mwh
        expected_potential = OrderedDict(
            sorted({("Shift_DR", 2020): 10,
                    ("Shift_DR", 2030): 20}.items())
        )
        actual_potential = OrderedDict(
            sorted(
                {(prj, p): instance.
                new_shiftable_load_supply_curve_max_cumulative_new_build_mwh[
                    prj, p]
                 for prj in
                 instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS
                 for p in instance.PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_potential, actual_potential)

        # Set: NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS
        expected_proj_points = [
            ("Shift_DR", 1), ("Shift_DR", 2), ("Shift_DR", 3)
        ]
        actual_proj_points = sorted([
            (prj, pnt) for (prj, pnt)
            in instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS
        ])
        self.assertListEqual(expected_proj_points, actual_proj_points)

        # Param: new_shiftable_load_supply_curve_slope
        expected_slopes = {
            ("Shift_DR", 1): 25000,
            ("Shift_DR", 2): 50000,
            ("Shift_DR", 3): 75000
        }
        actual_slopes = {
            (prj, pnt):
                instance.new_shiftable_load_supply_curve_slope[prj, pnt]
            for (prj, pnt)
            in instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS
        }
        self.assertDictEqual(expected_slopes, actual_slopes)

        # Param: new_shiftable_load_supply_curve_intercept
        expected_intercepts = {
            ("Shift_DR", 1): 0,
            ("Shift_DR", 2): -256987769,
            ("Shift_DR", 3): -616885503
        }
        actual_intercepts = {
            (prj, pnt):
                instance.new_shiftable_load_supply_curve_intercept[prj, pnt]
            for (prj, pnt)
            in instance.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS
        }
        self.assertDictEqual(expected_intercepts, actual_intercepts)

        # Set: NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS
        expected_op_per = sorted([
            ("Shift_DR", 2020), ("Shift_DR", 2030)
        ])
        actual_op_per = sorted([
            (prj, per) for (prj, per)
            in instance.
                NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_op_per, actual_op_per)


if __name__ == "__main__":
    unittest.main()
