#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.investment.periods",
    "transmission"
]
NAME_OF_MODULE_BEING_TESTED = \
    "transmission.capacity.capacity_types.new_build_transmission"
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


class TestSpecifiedTransmission(unittest.TestCase):
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

        # Set: NEW_BUILD_TRANSMISSION_VINTAGES
        expected_tx_vintages = sorted([("Tx_New", 2020), ("Tx_New", 2030)])
        actual_tx_vintages = sorted(
            [(tx, v) for (tx, v) in instance.NEW_BUILD_TRANSMISSION_VINTAGES]
            )
        self.assertListEqual(expected_tx_vintages, actual_tx_vintages)

        # Param: tx_lifetime_yrs_by_new_build_vintage
        expected_lifetime = OrderedDict(sorted({
            ("Tx_New", 2020): 35, ("Tx_New", 2030): 35
                                               }.items()
                                               )
                                        )
        actual_lifetime = OrderedDict(sorted({
            (tx, v): instance.tx_lifetime_yrs_by_new_build_vintage[tx, v]
            for (tx, v) in instance.NEW_BUILD_TRANSMISSION_VINTAGES
                                               }.items()
                                               )
                                        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Param: tx_annualized_real_cost_per_mw_yr
        expected_cost = OrderedDict(sorted({
            ("Tx_New", 2020): 10, ("Tx_New", 2030): 10
                                               }.items()
                                               )
                                        )
        actual_cost = OrderedDict(sorted({
            (tx, v): instance.tx_annualized_real_cost_per_mw_yr[tx, v]
            for (tx, v) in instance.NEW_BUILD_TRANSMISSION_VINTAGES
                                               }.items()
                                               )
                                        )
        self.assertDictEqual(expected_cost, actual_cost)

    def test_derived_data(self):
        """
        Test in-model operations and calculations
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

        # Set: OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE
        expected_op_p_by_tx_v = OrderedDict(sorted({
            ("Tx_New", 2020): [2020, 2030], ("Tx_New", 2030): [2030]
                                                   }.items()
                                                   )
                                            )
        actual_op_p_by_tx_v = OrderedDict(sorted({
            (tx, v):
                [p for p
                 in instance.
                    OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE[tx, v]
                 ]
            for (tx, v) in instance.NEW_BUILD_TRANSMISSION_VINTAGES
                                                   }.items()
                                                   )
                                            )
        self.assertDictEqual(expected_op_p_by_tx_v, actual_op_p_by_tx_v)

        # Set: NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS
        expected_tx_op_periods = sorted([
            ("Tx_New", 2020), ("Tx_New", 2030)
        ])
        actual_tx_op_periods = sorted([
            (tx, p) for (tx, p)
            in instance.NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_tx_op_periods, actual_tx_op_periods)

        # Set: NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD
        expected_tx_v_by_period = OrderedDict(sorted({
            2020: sorted([("Tx_New", 2020)]),
            2030: sorted([("Tx_New", 2020), ("Tx_New", 2030)])
                                                     }.items()
                                                     )
                                              )
        actual_tx_v_by_period = OrderedDict(sorted({
            p: sorted(
                [(tx, v) for (tx, v) in
                 instance.
                 NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                 ]
            ) for p in instance.PERIODS
                                                     }.items()
                                                     )
                                              )
        self.assertDictEqual(expected_tx_v_by_period, actual_tx_v_by_period)

if __name__ == "__main__":
    unittest.main()
