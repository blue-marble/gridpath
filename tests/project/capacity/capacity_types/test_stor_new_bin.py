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
    "project.capacity.capacity_types.stor_new_bin"
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


class TestNewBinaryBuildStorage(unittest.TestCase):
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

        # Set: NEW_BINARY_BUILD_STORAGE_PROJECTS
        expected_stor_new_bin_project_set = ["Battery_Binary"]
        actual_stor_new_bin_project_set = sorted(
            [prj for prj in instance.NEW_BINARY_BUILD_STORAGE_PROJECTS]
        )
        self.assertListEqual(expected_stor_new_bin_project_set,
                             actual_stor_new_bin_project_set)

        # Param: binary_build_size_storage_mw
        expected_binary_build_size_storage_mw = OrderedDict(
            sorted({"Battery_Binary": 10}.items())
        )
        actual_binary_build_size_storage_mw = OrderedDict(
            sorted(
                {prj:
                    instance.binary_build_size_storage_mw[prj]
                 for prj in instance.NEW_BINARY_BUILD_STORAGE_PROJECTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_binary_build_size_storage_mw,
                             actual_binary_build_size_storage_mw)

        # Param: binary_build_size_storage_mwh
        expected_binary_build_size_storage_mwh = OrderedDict(
            sorted({"Battery_Binary": 40}.items())
        )
        actual_binary_build_size_storage_mwh = OrderedDict(
            sorted(
                {prj:
                    instance.binary_build_size_storage_mwh[prj]
                 for prj in instance.NEW_BINARY_BUILD_STORAGE_PROJECTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_binary_build_size_storage_mwh,
                             actual_binary_build_size_storage_mwh)

        # Set: NEW_BINARY_BUILD_STORAGE_VINTAGES
        expected_storage_vintage_set = sorted([
            ("Battery_Binary", 2020),
            ("Battery_Binary", 2030)
        ])
        actual_storage_vintage_set = sorted(
            [(prj, period)
             for (prj, period) in instance.NEW_BINARY_BUILD_STORAGE_VINTAGES
             ]
        )
        self.assertListEqual(expected_storage_vintage_set,
                             actual_storage_vintage_set)

        # Params: lifetime_yrs_by_new_binary_build_storage_vintage
        expected_lifetime = OrderedDict(
            sorted({("Battery_Binary", 2020): 10,
                    ("Battery_Binary", 2030): 10}.items())
        )
        actual_lifetime = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.lifetime_yrs_by_new_binary_build_storage_vintage[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_BINARY_BUILD_STORAGE_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: new_binary_build_storage_annualized_real_cost_per_mw_yr
        expected_mw_yr_cost = OrderedDict(
            sorted({("Battery_Binary", 2020): 1,
                    ("Battery_Binary", 2030): 1}.items())
        )
        actual_mw_yr_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_binary_build_storage_annualized_real_cost_per_mw_yr[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_BINARY_BUILD_STORAGE_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_mw_yr_cost, actual_mw_yr_cost)

        # Params: new_binary_build_storage_annualized_real_cost_per_mw_yr
        expected_mwh_yr_cost = OrderedDict(
            sorted({("Battery_Binary", 2020): 1,
                    ("Battery_Binary", 2030): 1}.items())
        )
        actual_mwh_yr_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_binary_build_storage_annualized_real_cost_per_mwh_yr[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_BINARY_BUILD_STORAGE_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_mwh_yr_cost, actual_mwh_yr_cost)

    def test_derived_data(self):
        """
        Calculations
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

        # Sets: OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE
        expected_op_periods_by_stor_vintage = {
            ("Battery_Binary", 2020): [2020],
            ("Battery_Binary", 2030): [2030]
        }
        actual_periods_by_stor_vintage = {
            (prj, vintage):
                [period for period in
                 instance.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE[
                    prj, vintage]]
            for (prj, vintage) in
                instance.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE
        }
        self.assertDictEqual(expected_op_periods_by_stor_vintage,
                             actual_periods_by_stor_vintage)

        # Sets: NEW_BINARY_BUILD_STORAGE_OPERATIONAL_PERIODS
        expected_stor_op_periods = sorted([
            ("Battery_Binary", 2020),
            ("Battery_Binary", 2030)
        ])
        actual_stor_op_periods = sorted([
            (prj, period) for (prj, period) in
            instance.NEW_BINARY_BUILD_STORAGE_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_stor_op_periods, actual_stor_op_periods)

        # Sets: NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD
        expected_stor_vintage_op_in_period = {
            2020: [("Battery_Binary", 2020)],
            2030: [("Battery_Binary", 2030)]
        }
        actual_stor_vintage_op_in_period = {
            p: [(g, v) for (g, v) in
                instance.NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                ] for p in instance.PERIODS
        }
        self.assertDictEqual(expected_stor_vintage_op_in_period,
                             actual_stor_vintage_op_in_period)


if __name__ == "__main__":
    unittest.main()
