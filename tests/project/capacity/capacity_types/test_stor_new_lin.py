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
    "project.capacity.capacity_types.stor_new_lin"
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


class TestNewBuildStorage(unittest.TestCase):
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

        # Set: NEW_BUILD_STORAGE_PROJECTS
        expected_stor_new_lin_project_set = ["Battery"]
        actual_stor_new_lin_project_set = sorted(
            [prj for prj in instance.NEW_BUILD_STORAGE_PROJECTS]
        )
        self.assertListEqual(expected_stor_new_lin_project_set,
                             actual_stor_new_lin_project_set)

        # Param: minimum_duration_hours
        expected_min_duration = OrderedDict(
            sorted({"Battery": 1}.items())
        )
        actual_min_duration = OrderedDict(
            sorted(
                {prj:
                    instance.minimum_duration_hours[prj]
                 for prj in instance.NEW_BUILD_STORAGE_PROJECTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_duration, actual_min_duration)

        # Set: NEW_BUILD_STORAGE_VINTAGES
        expected_storage_vintage_set = sorted([
            ("Battery", 2020), ("Battery", 2030)
        ])
        actual_storage_vintage_set = sorted(
            [(prj, period)
             for (prj, period) in instance.NEW_BUILD_STORAGE_VINTAGES
             ]
        )
        self.assertListEqual(expected_storage_vintage_set,
                             actual_storage_vintage_set)

        # Params: lifetime_yrs_by_stor_new_lin_vintage
        expected_lifetime = OrderedDict(
            sorted({("Battery", 2020): 10, ("Battery", 2030): 10}.items())
        )
        actual_lifetime = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.lifetime_yrs_by_stor_new_lin_vintage[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_BUILD_STORAGE_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: stor_new_lin_annualized_real_cost_per_mw_yr
        expected_mw_yr_cost = OrderedDict(
            sorted({("Battery", 2020): 1, ("Battery", 2030): 1}.items())
        )
        actual_mw_yr_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.stor_new_lin_annualized_real_cost_per_mw_yr[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_BUILD_STORAGE_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_mw_yr_cost, actual_mw_yr_cost)

        # Params: stor_new_lin_annualized_real_cost_per_mw_yr
        expected_mwh_yr_cost = OrderedDict(
            sorted({("Battery", 2020): 1, ("Battery", 2030): 1}.items())
        )
        actual_mwh_yr_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.stor_new_lin_annualized_real_cost_per_mwh_yr[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_BUILD_STORAGE_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_mwh_yr_cost, actual_mwh_yr_cost)

        # Set: NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT
        expected_storage_vintage_min_capacity_set = sorted([
            ("Battery", 2030)
        ])
        actual_storage_vintage_min_capacity_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_min_capacity_set,
                             actual_storage_vintage_min_capacity_set)

        # Params: min_storage_cumulative_new_build_mw
        expected_min_capacity = OrderedDict(
            sorted({("Battery", 2030): 7}.items())
        )
        actual_min_capacity = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.min_storage_cumulative_new_build_mw[
                        prj, vintage]
                 for (prj, vintage) in
                 instance.
                 NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_capacity, actual_min_capacity)
        
        # Set: NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT
        expected_storage_vintage_min_energy_set = sorted([
            ("Battery", 2030)
        ])
        actual_storage_vintage_min_energy_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_min_energy_set,
                             actual_storage_vintage_min_energy_set)

        # Params: min_storage_cumulative_new_build_mw
        expected_min_energy = OrderedDict(
            sorted({("Battery", 2030): 10}.items())
        )
        actual_min_energy = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.min_storage_cumulative_new_build_mwh[
                        prj, vintage]
                 for (prj, vintage) in
                 instance.
                 NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_energy, actual_min_energy)

        # Set: NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT
        expected_storage_vintage_max_capacity_set = sorted([
            ("Battery", 2020)
        ])
        actual_storage_vintage_max_capacity_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_max_capacity_set,
                             actual_storage_vintage_max_capacity_set)

        # Params: max_storage_cumulative_new_build_mw
        expected_max_capacity = OrderedDict(
            sorted({("Battery", 2020): 6}.items())
        )
        actual_max_capacity = OrderedDict(
            sorted(
                {(prj, vintage):
                     instance.max_storage_cumulative_new_build_mw[
                         prj, vintage]
                 for (prj, vintage) in
                 instance.
                     NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_capacity, actual_max_capacity)

        # Set: NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT
        expected_storage_vintage_max_energy_set = sorted([
            ("Battery", 2020)
        ])
        actual_storage_vintage_max_energy_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_max_energy_set,
                             actual_storage_vintage_max_energy_set)

        # Params: max_storage_cumulative_new_build_mw
        expected_max_energy = OrderedDict(
            sorted({("Battery", 2020): 7}.items())
        )
        actual_max_energy = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.max_storage_cumulative_new_build_mwh[
                         prj, vintage]
                 for (prj, vintage) in
                 instance.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_energy, actual_max_energy)

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

        # Sets: OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE
        expected_op_periods_by_stor_vintage = {
            ("Battery", 2020): [2020], ("Battery", 2030): [2030]
        }
        actual_periods_by_stor_vintage = {
            (prj, vintage):
                [period for period in
                 instance.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE[
                    prj, vintage]]
            for (prj, vintage) in
                instance.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE
        }
        self.assertDictEqual(expected_op_periods_by_stor_vintage,
                             actual_periods_by_stor_vintage)

        # Sets: NEW_BUILD_STORAGE_OPERATIONAL_PERIODS
        expected_stor_op_periods = sorted([
            ("Battery", 2020), ("Battery", 2030)
        ])
        actual_stor_op_periods = sorted([
            (prj, period) for (prj, period) in
            instance.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_stor_op_periods, actual_stor_op_periods)

        # Sets: NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD
        expected_stor_vintage_op_in_period = {
            2020: [("Battery", 2020)], 2030: [("Battery", 2030)]
        }
        actual_stor_vintage_op_in_period = {
            p: [(g, v) for (g, v) in
                instance.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                ] for p in instance.PERIODS
        }
        self.assertDictEqual(expected_stor_vintage_op_in_period,
                             actual_stor_vintage_op_in_period)

if __name__ == "__main__":
    unittest.main()
