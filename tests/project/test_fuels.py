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
    os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods"
]
NAME_OF_MODULE_BEING_TESTED = "project.fuels"
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


class TestFuels(unittest.TestCase):
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

        # Set: FUELS
        expected_fuels = sorted(["Uranium", "Coal", "Gas"])
        actual_fuels = sorted([fuel for fuel in instance.FUELS])
        self.assertListEqual(expected_fuels, actual_fuels)

        # Param: co2_intensity_tons_per_mmbtu
        expected_co2 = OrderedDict(sorted(
            {"Uranium": 0, "Coal": 0.09552, "Gas": 0.05306}.items()
                                            )
                                     )
        actual_co2 = OrderedDict(sorted(
            {f: instance.co2_intensity_tons_per_mmbtu[f]
             for f in instance.FUELS}.items()
                                            )
                                     )
        self.assertDictEqual(expected_co2, actual_co2)

        # Param: fuel_price_per_mmbtu
        expected_price = OrderedDict(sorted(
            {("Uranium", 2020, 1): 2,
             ("Uranium", 2020, 2): 2,
             ("Uranium", 2020, 3): 2,
             ("Uranium", 2020, 4): 2,
             ("Uranium", 2020, 5): 2,
             ("Uranium", 2020, 6): 2,
             ("Uranium", 2020, 7): 2,
             ("Uranium", 2020, 8): 2,
             ("Uranium", 2020, 9): 2,
             ("Uranium", 2020, 10): 2,
             ("Uranium", 2020, 11): 2,
             ("Uranium", 2020, 12): 2,
             ("Uranium", 2030, 1): 2,
             ("Uranium", 2030, 2): 2,
             ("Uranium", 2030, 3): 2,
             ("Uranium", 2030, 4): 2,
             ("Uranium", 2030, 5): 2,
             ("Uranium", 2030, 6): 2,
             ("Uranium", 2030, 7): 2,
             ("Uranium", 2030, 8): 2,
             ("Uranium", 2030, 9): 2,
             ("Uranium", 2030, 10): 2,
             ("Uranium", 2030, 11): 2,
             ("Uranium", 2030, 12): 2,
             ("Coal", 2020, 1): 4,
             ("Coal", 2020, 2): 4,
             ("Coal", 2020, 3): 4,
             ("Coal", 2020, 4): 4,
             ("Coal", 2020, 5): 4,
             ("Coal", 2020, 6): 4,
             ("Coal", 2020, 7): 4,
             ("Coal", 2020, 8): 4,
             ("Coal", 2020, 9): 4,
             ("Coal", 2020, 10): 4,
             ("Coal", 2020, 11): 4,
             ("Coal", 2020, 12): 4,
             ("Coal", 2030, 1): 4,
             ("Coal", 2030, 2): 4,
             ("Coal", 2030, 3): 4,
             ("Coal", 2030, 4): 4,
             ("Coal", 2030, 5): 4,
             ("Coal", 2030, 6): 4,
             ("Coal", 2030, 7): 4,
             ("Coal", 2030, 8): 4,
             ("Coal", 2030, 9): 4,
             ("Coal", 2030, 10): 4,
             ("Coal", 2030, 11): 4,
             ("Coal", 2030, 12): 4,
             ("Gas", 2020, 1): 5,
             ("Gas", 2020, 2): 5,
             ("Gas", 2020, 3): 5,
             ("Gas", 2020, 4): 5,
             ("Gas", 2020, 5): 5,
             ("Gas", 2020, 6): 5,
             ("Gas", 2020, 7): 5,
             ("Gas", 2020, 8): 5,
             ("Gas", 2020, 9): 5,
             ("Gas", 2020, 10): 5,
             ("Gas", 2020, 11): 5,
             ("Gas", 2020, 12): 5,
             ("Gas", 2030, 1): 5,
             ("Gas", 2030, 2): 5,
             ("Gas", 2030, 3): 5,
             ("Gas", 2030, 4): 5,
             ("Gas", 2030, 5): 5,
             ("Gas", 2030, 6): 5,
             ("Gas", 2030, 7): 5,
             ("Gas", 2030, 8): 5,
             ("Gas", 2030, 9): 5,
             ("Gas", 2030, 10): 5,
             ("Gas", 2030, 11): 5,
             ("Gas", 2030, 12): 5
             }.items()
                                            )
                                     )
        actual_price = OrderedDict(sorted(
            {(f, p, m): instance.fuel_price_per_mmbtu[f, p, m]
             for f in instance.FUELS
             for p in instance.PERIODS
             for m in instance.MONTHS}.items()
                                            )
                                     )
        self.assertDictEqual(expected_price, actual_price)

if __name__ == "__main__":
    unittest.main()
