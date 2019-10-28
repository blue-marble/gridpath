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
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "transmission",
    "transmission.capacity",
    "transmission.capacity.capacity",
    "transmission.operations.operational_types",
    "transmission.operations.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "transmission.operations.simultaneous_flow_limits"
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


class TestTxSimultaneousFlowLimits(unittest.TestCase):
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

        # Set: SIMULTANEOUS_FLOW_LIMIT_PERIODS
        expected_limit_periods = sorted(
            [("Zone1_Exports", 2020), ("Zone1_Exports", 2030),
             ("Zone1_Imports", 2030)]
        )
        actual_limit_periods = sorted(
            [(g, p) for (g, p) in
             instance.SIMULTANEOUS_FLOW_LIMIT_PERIODS]
        )
        self.assertListEqual(expected_limit_periods, actual_limit_periods)

        # Param: simultaneous_flow_limit_mw
        expected_sim_flow_lim = OrderedDict(
            sorted(
                {("Zone1_Exports", 2020): 5, ("Zone1_Exports", 2030): 10,
                 ("Zone1_Imports", 2030): 8}.items()
            )
        )
        actual_sim_flow_lim = OrderedDict(
            sorted(
                {(g, p): instance.simultaneous_flow_limit_mw[g, p]
                 for (g, p)
                 in instance.SIMULTANEOUS_FLOW_LIMIT_PERIODS}.items()
            )
        )
        self.assertDictEqual(expected_sim_flow_lim, actual_sim_flow_lim)

        # Set: SIMULTANEOUS_FLOW_LIMIT_TIMEPOINTS
        expected_limit_tmps = sorted(
            [("Zone1_Exports", 20200101), ("Zone1_Exports", 20200102),
             ("Zone1_Exports", 20200103), ("Zone1_Exports", 20200104),
             ("Zone1_Exports", 20200105), ("Zone1_Exports", 20200106),
             ("Zone1_Exports", 20200107), ("Zone1_Exports", 20200108),
             ("Zone1_Exports", 20200109), ("Zone1_Exports", 20200110),
             ("Zone1_Exports", 20200111), ("Zone1_Exports", 20200112),
             ("Zone1_Exports", 20200113), ("Zone1_Exports", 20200114),
             ("Zone1_Exports", 20200115), ("Zone1_Exports", 20200116),
             ("Zone1_Exports", 20200117), ("Zone1_Exports", 20200118),
             ("Zone1_Exports", 20200119), ("Zone1_Exports", 20200120),
             ("Zone1_Exports", 20200121), ("Zone1_Exports", 20200122),
             ("Zone1_Exports", 20200123), ("Zone1_Exports", 20200124),
             ("Zone1_Exports", 20200201), ("Zone1_Exports", 20200202),
             ("Zone1_Exports", 20200203), ("Zone1_Exports", 20200204),
             ("Zone1_Exports", 20200205), ("Zone1_Exports", 20200206),
             ("Zone1_Exports", 20200207), ("Zone1_Exports", 20200208),
             ("Zone1_Exports", 20200209), ("Zone1_Exports", 20200210),
             ("Zone1_Exports", 20200211), ("Zone1_Exports", 20200212),
             ("Zone1_Exports", 20200213), ("Zone1_Exports", 20200214),
             ("Zone1_Exports", 20200215), ("Zone1_Exports", 20200216),
             ("Zone1_Exports", 20200217), ("Zone1_Exports", 20200218),
             ("Zone1_Exports", 20200219), ("Zone1_Exports", 20200220),
             ("Zone1_Exports", 20200221), ("Zone1_Exports", 20200222),
             ("Zone1_Exports", 20200223), ("Zone1_Exports", 20200224),
             ("Zone1_Exports", 20300101), ("Zone1_Exports", 20300102),
             ("Zone1_Exports", 20300103), ("Zone1_Exports", 20300104),
             ("Zone1_Exports", 20300105), ("Zone1_Exports", 20300106),
             ("Zone1_Exports", 20300107), ("Zone1_Exports", 20300108),
             ("Zone1_Exports", 20300109), ("Zone1_Exports", 20300110),
             ("Zone1_Exports", 20300111), ("Zone1_Exports", 20300112),
             ("Zone1_Exports", 20300113), ("Zone1_Exports", 20300114),
             ("Zone1_Exports", 20300115), ("Zone1_Exports", 20300116),
             ("Zone1_Exports", 20300117), ("Zone1_Exports", 20300118),
             ("Zone1_Exports", 20300119), ("Zone1_Exports", 20300120),
             ("Zone1_Exports", 20300121), ("Zone1_Exports", 20300122),
             ("Zone1_Exports", 20300123), ("Zone1_Exports", 20300124),
             ("Zone1_Exports", 20300201), ("Zone1_Exports", 20300202),
             ("Zone1_Exports", 20300203), ("Zone1_Exports", 20300204),
             ("Zone1_Exports", 20300205), ("Zone1_Exports", 20300206),
             ("Zone1_Exports", 20300207), ("Zone1_Exports", 20300208),
             ("Zone1_Exports", 20300209), ("Zone1_Exports", 20300210),
             ("Zone1_Exports", 20300211), ("Zone1_Exports", 20300212),
             ("Zone1_Exports", 20300213), ("Zone1_Exports", 20300214),
             ("Zone1_Exports", 20300215), ("Zone1_Exports", 20300216),
             ("Zone1_Exports", 20300217), ("Zone1_Exports", 20300218),
             ("Zone1_Exports", 20300219), ("Zone1_Exports", 20300220),
             ("Zone1_Exports", 20300221), ("Zone1_Exports", 20300222),
             ("Zone1_Exports", 20300223), ("Zone1_Exports", 20300224),
             ("Zone1_Imports", 20300101), ("Zone1_Imports", 20300102),
             ("Zone1_Imports", 20300103), ("Zone1_Imports", 20300104),
             ("Zone1_Imports", 20300105), ("Zone1_Imports", 20300106),
             ("Zone1_Imports", 20300107), ("Zone1_Imports", 20300108),
             ("Zone1_Imports", 20300109), ("Zone1_Imports", 20300110),
             ("Zone1_Imports", 20300111), ("Zone1_Imports", 20300112),
             ("Zone1_Imports", 20300113), ("Zone1_Imports", 20300114),
             ("Zone1_Imports", 20300115), ("Zone1_Imports", 20300116),
             ("Zone1_Imports", 20300117), ("Zone1_Imports", 20300118),
             ("Zone1_Imports", 20300119), ("Zone1_Imports", 20300120),
             ("Zone1_Imports", 20300121), ("Zone1_Imports", 20300122),
             ("Zone1_Imports", 20300123), ("Zone1_Imports", 20300124),
             ("Zone1_Imports", 20300201), ("Zone1_Imports", 20300202),
             ("Zone1_Imports", 20300203), ("Zone1_Imports", 20300204),
             ("Zone1_Imports", 20300205), ("Zone1_Imports", 20300206),
             ("Zone1_Imports", 20300207), ("Zone1_Imports", 20300208),
             ("Zone1_Imports", 20300209), ("Zone1_Imports", 20300210),
             ("Zone1_Imports", 20300211), ("Zone1_Imports", 20300212),
             ("Zone1_Imports", 20300213), ("Zone1_Imports", 20300214),
             ("Zone1_Imports", 20300215), ("Zone1_Imports", 20300216),
             ("Zone1_Imports", 20300217), ("Zone1_Imports", 20300218),
             ("Zone1_Imports", 20300219), ("Zone1_Imports", 20300220),
             ("Zone1_Imports", 20300221), ("Zone1_Imports", 20300222),
             ("Zone1_Imports", 20300223), ("Zone1_Imports", 20300224)
             ]
        )
        actual_limit_tmps = sorted(
            (g, tmp) for (g, tmp)
            in instance.SIMULTANEOUS_FLOW_LIMIT_TIMEPOINTS
        )
        self.assertListEqual(expected_limit_tmps, actual_limit_tmps)

        # Set: SIMULTANEOUS_FLOW_LIMITS
        expected_limits = sorted(
            ["Zone1_Exports", "Zone1_Imports"]
        )
        actual_limits = sorted(
            [g for g in instance.SIMULTANEOUS_FLOW_LIMITS]
        )
        self.assertListEqual(expected_limits, actual_limits)

        # Set: SIMULTANEOUS_FLOW_LIMIT_LINES
        expected_limit_lines = sorted(
            [("Zone1_Exports", "Tx1"), ("Zone1_Exports", "Tx_New"),
             ("Zone1_Imports", "Tx1"), ("Zone1_Imports", "Tx_New")]
        )
        actual_limit_lines = sorted(
            [(g, tx) for (g, tx) in instance.SIMULTANEOUS_FLOW_LIMIT_LINES]
        )
        self.assertListEqual(expected_limit_lines, actual_limit_lines)

        # Param: simultaneous_flow_direction
        expected_dir = OrderedDict(
            sorted(
                {("Zone1_Exports", "Tx1"): 1,
                 ("Zone1_Exports", "Tx_New"): 1,
                 ("Zone1_Imports", "Tx1"): -1,
                 ("Zone1_Imports", "Tx_New"): -1}.items()
            )
        )
        actual_dir = OrderedDict(
            sorted(
                {(g, tx): instance.simultaneous_flow_direction[g, tx]
                 for (g, tx) in instance.SIMULTANEOUS_FLOW_LIMIT_LINES
                 }.items()
            )
        )
        self.assertDictEqual(expected_dir, actual_dir)

        # Set: TRANSMISSION_LINES_BY_SIMULTANEOUS_FLOW_LIMIT
        expected_tx_by_g = OrderedDict(
            sorted(
                {"Zone1_Exports": sorted(["Tx1", "Tx_New"]),
                 "Zone1_Imports": sorted(["Tx1", "Tx_New"])}.items()
            )
        )
        actual_tx_by_g = OrderedDict(
            sorted(
                {g: sorted(
                    [tx for tx in
                     instance.TRANSMISSION_LINES_BY_SIMULTANEOUS_FLOW_LIMIT[g]
                     ]
                ) for g in instance.SIMULTANEOUS_FLOW_LIMITS}.items()
            )
        )
        self.assertDictEqual(expected_tx_by_g, actual_tx_by_g)