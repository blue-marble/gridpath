#!/usr/bin/env python

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
    "project.capacity.capacity_types.existing_gen_linear_economic_retirement"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='modules')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='modules')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestExistingGenLinearEconRet(unittest.TestCase):
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
                              horizon="",
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
                                     horizon="",
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
            horizon="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: EXISTING_LINEAR_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        expected_gen_set = [("Clunky_Old_Gen", 2020), ("Clunky_Old_Gen", 2030)]
        actual_gen_set = [
            (g, p) for (g, p) in
            instance.
            EXISTING_LINEAR_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
            ]
        self.assertListEqual(expected_gen_set, actual_gen_set)

        # Param: existing_lin_econ_ret_capacity_mw
        expected_cap = {
            ("Clunky_Old_Gen", 2020): 10, ("Clunky_Old_Gen", 2030): 10
        }
        actual_cap = {
            (g, p): instance.existing_lin_econ_ret_capacity_mw[g, p]
            for (g, p) in
            instance.
            EXISTING_LINEAR_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
    }
        self.assertDictEqual(expected_cap, actual_cap)

        # Param: existing_lin_econ_ret_fixed_cost_per_mw_yr
        expected_cost = {
            ("Clunky_Old_Gen", 2020): 1000, ("Clunky_Old_Gen", 2030): 1000
        }
        actual_cost = {
            (g, p): instance.existing_lin_econ_ret_fixed_cost_per_mw_yr[g, p]
            for (g, p) in
            instance.
            EXISTING_LINEAR_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
            }
        self.assertDictEqual(expected_cost, actual_cost)

    def test_derived_data(self):
        """
        Calculations
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            horizon="",
            stage=""
        )
        instance = m.create_instance(data)

if __name__ == "__main__":
    unittest.main()
