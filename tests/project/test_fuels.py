#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import pandas as pd
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

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Load test data
        fuels_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "fuels.tab"),
                sep="\t"
            )
        fuel_prices_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "fuel_prices.tab"),
                sep="\t"
            )

        # Set: FUELS
        expected_fuels = sorted(fuels_df['FUELS'].tolist())
        actual_fuels = sorted([fuel for fuel in instance.FUELS])
        self.assertListEqual(expected_fuels, actual_fuels)

        # Param: co2_intensity_tons_per_mmbtu
        # Rounding to 5 digits here to avoid precision-related error
        expected_co2 = OrderedDict(
            sorted(
                fuels_df.round(5).set_index('FUELS').to_dict()[
                    'co2_intensity_tons_per_mmbtu'
                ].items()
            )
        )
        actual_co2 = OrderedDict(
            sorted(
                {f: instance.co2_intensity_tons_per_mmbtu[f]
                 for f in instance.FUELS}.items()
            )
        )
        self.assertDictEqual(expected_co2, actual_co2)

        # Param: fuel_price_per_mmbtu
        expected_price = OrderedDict(
            sorted(
                fuel_prices_df.set_index(
                    ['fuel', 'period', 'month']
                ).to_dict()['fuel_price_per_mmbtu'].items()
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
