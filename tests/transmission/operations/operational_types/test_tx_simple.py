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
     "temporal.investment.periods", "geography.load_zones", "transmission",
     "transmission.capacity",
     "transmission.capacity.capacity"]
NAME_OF_MODULE_BEING_TESTED = \
    "transmission.operations.operational_types.tx_simple"

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


class TestTxOperations(unittest.TestCase):
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

        :return:
        """
        m, data = \
            add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                         module_to_test=MODULE_BEING_TESTED,
                                         test_data_dir=TEST_DATA_DIRECTORY,
                                         subproblem="",
                                         stage="")
        instance = m.create_instance(data)

        # Set: TRANSMISSION_LINES_SIMPLE
        expected_tx = sorted(["Tx_New"])
        actual_tx = sorted(
            instance.TRANSMISSION_LINES_SIMPLE
        )
        self.assertListEqual(expected_tx, actual_tx)
        
        # Set: TX_SIMPLE_OPERATIONAL_TIMEPOINTS
        expect_tx_op_tmp = sorted(
            [
                ("Tx_New", 20200101), ("Tx_New", 20200102),
                ("Tx_New", 20200103), ("Tx_New", 20200104),
                ("Tx_New", 20200105), ("Tx_New", 20200106),
                ("Tx_New", 20200107), ("Tx_New", 20200108),
                ("Tx_New", 20200109), ("Tx_New", 20200110),
                ("Tx_New", 20200111), ("Tx_New", 20200112),
                ("Tx_New", 20200113), ("Tx_New", 20200114),
                ("Tx_New", 20200115), ("Tx_New", 20200116),
                ("Tx_New", 20200117), ("Tx_New", 20200118),
                ("Tx_New", 20200119), ("Tx_New", 20200120),
                ("Tx_New", 20200121), ("Tx_New", 20200122),
                ("Tx_New", 20200123), ("Tx_New", 20200124),
                ("Tx_New", 20200201), ("Tx_New", 20200202),
                ("Tx_New", 20200203), ("Tx_New", 20200204),
                ("Tx_New", 20200205), ("Tx_New", 20200206),
                ("Tx_New", 20200207), ("Tx_New", 20200208),
                ("Tx_New", 20200209), ("Tx_New", 20200210),
                ("Tx_New", 20200211), ("Tx_New", 20200212),
                ("Tx_New", 20200213), ("Tx_New", 20200214),
                ("Tx_New", 20200215), ("Tx_New", 20200216),
                ("Tx_New", 20200217), ("Tx_New", 20200218),
                ("Tx_New", 20200219), ("Tx_New", 20200220),
                ("Tx_New", 20200221), ("Tx_New", 20200222),
                ("Tx_New", 20200223), ("Tx_New", 20200224),
                ("Tx_New", 20300101), ("Tx_New", 20300102),
                ("Tx_New", 20300103), ("Tx_New", 20300104),
                ("Tx_New", 20300105), ("Tx_New", 20300106),
                ("Tx_New", 20300107), ("Tx_New", 20300108),
                ("Tx_New", 20300109), ("Tx_New", 20300110),
                ("Tx_New", 20300111), ("Tx_New", 20300112),
                ("Tx_New", 20300113), ("Tx_New", 20300114),
                ("Tx_New", 20300115), ("Tx_New", 20300116),
                ("Tx_New", 20300117), ("Tx_New", 20300118),
                ("Tx_New", 20300119), ("Tx_New", 20300120),
                ("Tx_New", 20300121), ("Tx_New", 20300122),
                ("Tx_New", 20300123), ("Tx_New", 20300124),
                ("Tx_New", 20300201), ("Tx_New", 20300202),
                ("Tx_New", 20300203), ("Tx_New", 20300204),
                ("Tx_New", 20300205), ("Tx_New", 20300206),
                ("Tx_New", 20300207), ("Tx_New", 20300208),
                ("Tx_New", 20300209), ("Tx_New", 20300210),
                ("Tx_New", 20300211), ("Tx_New", 20300212),
                ("Tx_New", 20300213), ("Tx_New", 20300214),
                ("Tx_New", 20300215), ("Tx_New", 20300216),
                ("Tx_New", 20300217), ("Tx_New", 20300218),
                ("Tx_New", 20300219), ("Tx_New", 20300220),
                ("Tx_New", 20300221), ("Tx_New", 20300222),
                ("Tx_New", 20300223), ("Tx_New", 20300224)
            ]
        )
        actual_tx_op_tmp = sorted(
            [(tx, tmp) for (tx, tmp)
             in instance.TX_SIMPLE_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expect_tx_op_tmp, actual_tx_op_tmp)


if __name__ == "__main__":
    unittest.main()
