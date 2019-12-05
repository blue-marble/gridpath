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
    "project.capacity.capacity_types.gen_ret_bin"
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


class TestExistingGenBinaryEconRet(unittest.TestCase):
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

        # Set: EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        expected_gen_set = [("Clunky_Old_Gen2", 2020), ("Clunky_Old_Gen2", 2030)]
        actual_gen_set = sorted([
            (g, p) for (g, p) in
            instance.
            EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_gen_set, actual_gen_set)

        # Param: existing_bin_econ_ret_capacity_mw
        expected_cap = {
            ("Clunky_Old_Gen2", 2020): 10, ("Clunky_Old_Gen2", 2030): 10
        }
        actual_cap = {
            (g, p): instance.existing_bin_econ_ret_capacity_mw[g, p]
            for (g, p) in
            instance.
            EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        }
        self.assertDictEqual(expected_cap, actual_cap)

        # Set: EXISTING_BINARY_ECON_RETRMNT_GENERATORS
        expected_gens = ["Clunky_Old_Gen2"]
        actual_gens = [
            g for g in instance.EXISTING_BINARY_ECON_RETRMNT_GENERATORS
        ]
        self.assertListEqual(expected_gens, actual_gens)

        # Set: OPRTNL_PERIODS_BY_EX_BIN_ECON_RETRMNT_GENERATORS
        expected_periods_by_generator = {
            "Clunky_Old_Gen2": [2020, 2030]
        }
        actual_periods_by_generator = {
            g: [p for p in
                instance.OPRTNL_PERIODS_BY_EX_BIN_ECON_RETRMNT_GENERATORS[g]
                ] for g in instance.EXISTING_BINARY_ECON_RETRMNT_GENERATORS
        }
        self.assertDictEqual(expected_periods_by_generator,
                             actual_periods_by_generator)

        # Param: ex_gen_bin_econ_ret_gen_first_period
        expected_first_period = {
            "Clunky_Old_Gen2": 2020
        }
        actual_first_period = {
            g: instance.ex_gen_bin_econ_ret_gen_first_period[g]
            for g in instance.EXISTING_BINARY_ECON_RETRMNT_GENERATORS
            }
        self.assertDictEqual(expected_first_period, actual_first_period)

        # Param: existing_bin_econ_ret_capacity_mw
        expected_cap = {
            ("Clunky_Old_Gen2", 2020): 10, ("Clunky_Old_Gen2", 2030): 10
        }
        actual_cap = {
            (g, p): instance.existing_bin_econ_ret_capacity_mw[g, p]
            for (g, p) in
            instance.
                EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        }
        self.assertDictEqual(expected_cap, actual_cap)

        # Param: existing_bin_econ_ret_fixed_cost_per_mw_yr
        expected_cost = {
            ("Clunky_Old_Gen2", 2020): 1000, ("Clunky_Old_Gen2", 2030): 1000
        }
        actual_cost = {
            (g, p): instance.existing_bin_econ_ret_fixed_cost_per_mw_yr[g, p]
            for (g, p) in
            instance.
            EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
            }
        self.assertDictEqual(expected_cost, actual_cost)


if __name__ == "__main__":
    unittest.main()
