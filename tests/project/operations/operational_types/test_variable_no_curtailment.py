#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
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
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity", "project.fuels", "project.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.variable_no_curtailment"
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


class TestVariableOperationalType(unittest.TestCase):
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

        # Set: VARIABLE_NO_CURTAILMENT_GENERATORS
        expected_gen_set = sorted([
            "Customer_PV"
        ])
        actual_gen_set = sorted([
            prj for prj in instance.VARIABLE_NO_CURTAILMENT_GENERATORS
            ])
        self.assertListEqual(expected_gen_set,
                             actual_gen_set)

        # Set: VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS
        expected_operational_timepoints_by_project = sorted([
            ("Customer_PV", 20200101), ("Customer_PV", 20200102),
            ("Customer_PV", 20200103), ("Customer_PV", 20200104),
            ("Customer_PV", 20200105), ("Customer_PV", 20200106),
            ("Customer_PV", 20200107), ("Customer_PV", 20200108),
            ("Customer_PV", 20200109), ("Customer_PV", 20200110),
            ("Customer_PV", 20200111), ("Customer_PV", 20200112),
            ("Customer_PV", 20200113), ("Customer_PV", 20200114),
            ("Customer_PV", 20200115), ("Customer_PV", 20200116),
            ("Customer_PV", 20200117), ("Customer_PV", 20200118),
            ("Customer_PV", 20200119), ("Customer_PV", 20200120),
            ("Customer_PV", 20200121), ("Customer_PV", 20200122),
            ("Customer_PV", 20200123), ("Customer_PV", 20200124),
            ("Customer_PV", 20200201), ("Customer_PV", 20200202),
            ("Customer_PV", 20200203), ("Customer_PV", 20200204),
            ("Customer_PV", 20200205), ("Customer_PV", 20200206),
            ("Customer_PV", 20200207), ("Customer_PV", 20200208),
            ("Customer_PV", 20200209), ("Customer_PV", 20200210),
            ("Customer_PV", 20200211), ("Customer_PV", 20200212),
            ("Customer_PV", 20200213), ("Customer_PV", 20200214),
            ("Customer_PV", 20200215), ("Customer_PV", 20200216),
            ("Customer_PV", 20200217), ("Customer_PV", 20200218),
            ("Customer_PV", 20200219), ("Customer_PV", 20200220),
            ("Customer_PV", 20200221), ("Customer_PV", 20200222),
            ("Customer_PV", 20200223), ("Customer_PV", 20200224),
            ("Customer_PV", 20300101), ("Customer_PV", 20300102),
            ("Customer_PV", 20300103), ("Customer_PV", 20300104),
            ("Customer_PV", 20300105), ("Customer_PV", 20300106),
            ("Customer_PV", 20300107), ("Customer_PV", 20300108),
            ("Customer_PV", 20300109), ("Customer_PV", 20300110),
            ("Customer_PV", 20300111), ("Customer_PV", 20300112),
            ("Customer_PV", 20300113), ("Customer_PV", 20300114),
            ("Customer_PV", 20300115), ("Customer_PV", 20300116),
            ("Customer_PV", 20300117), ("Customer_PV", 20300118),
            ("Customer_PV", 20300119), ("Customer_PV", 20300120),
            ("Customer_PV", 20300121), ("Customer_PV", 20300122),
            ("Customer_PV", 20300123), ("Customer_PV", 20300124),
            ("Customer_PV", 20300201), ("Customer_PV", 20300202),
            ("Customer_PV", 20300203), ("Customer_PV", 20300204),
            ("Customer_PV", 20300205), ("Customer_PV", 20300206),
            ("Customer_PV", 20300207), ("Customer_PV", 20300208),
            ("Customer_PV", 20300209), ("Customer_PV", 20300210),
            ("Customer_PV", 20300211), ("Customer_PV", 20300212),
            ("Customer_PV", 20300213), ("Customer_PV", 20300214),
            ("Customer_PV", 20300215), ("Customer_PV", 20300216),
            ("Customer_PV", 20300217), ("Customer_PV", 20300218),
            ("Customer_PV", 20300219), ("Customer_PV", 20300220),
            ("Customer_PV", 20300221), ("Customer_PV", 20300222),
            ("Customer_PV", 20300223), ("Customer_PV", 20300224)
        ])
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.
                VARIABLE_NO_CURTAILMENT_GENERATOR_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timepoints_by_project,
                             actual_operational_timepoints_by_project)

        # Param: cap_factor_no_curtailment
        expected_cap_factor = {
            ("Customer_PV", 20200101): 0.5, ("Customer_PV", 20200102): 0.5,
            ("Customer_PV", 20200103): 0.5, ("Customer_PV", 20200104): 0.5,
            ("Customer_PV", 20200105): 0.5, ("Customer_PV", 20200106): 0.5,
            ("Customer_PV", 20200107): 0.5, ("Customer_PV", 20200108): 0.5,
            ("Customer_PV", 20200109): 0.5, ("Customer_PV", 20200110): 0.5,
            ("Customer_PV", 20200111): 0.5, ("Customer_PV", 20200112): 0.5,
            ("Customer_PV", 20200113): 0.5, ("Customer_PV", 20200114): 0.5,
            ("Customer_PV", 20200115): 0.5, ("Customer_PV", 20200116): 0.5,
            ("Customer_PV", 20200117): 0.5, ("Customer_PV", 20200118): 0.5,
            ("Customer_PV", 20200119): 0.5, ("Customer_PV", 20200120): 0.5,
            ("Customer_PV", 20200121): 0.5, ("Customer_PV", 20200122): 0.5,
            ("Customer_PV", 20200123): 0.5, ("Customer_PV", 20200124): 0.5,
            ("Customer_PV", 20200201): 0.5, ("Customer_PV", 20200202): 0.5,
            ("Customer_PV", 20200203): 0.5, ("Customer_PV", 20200204): 0.5,
            ("Customer_PV", 20200205): 0.5, ("Customer_PV", 20200206): 0.5,
            ("Customer_PV", 20200207): 0.5, ("Customer_PV", 20200208): 0.5,
            ("Customer_PV", 20200209): 0.5, ("Customer_PV", 20200210): 0.5,
            ("Customer_PV", 20200211): 0.5, ("Customer_PV", 20200212): 0.5,
            ("Customer_PV", 20200213): 0.5, ("Customer_PV", 20200214): 0.5,
            ("Customer_PV", 20200215): 0.5, ("Customer_PV", 20200216): 0.5,
            ("Customer_PV", 20200217): 0.5, ("Customer_PV", 20200218): 0.5,
            ("Customer_PV", 20200219): 0.5, ("Customer_PV", 20200220): 0.5,
            ("Customer_PV", 20200221): 0.5, ("Customer_PV", 20200222): 0.5,
            ("Customer_PV", 20200223): 0.5, ("Customer_PV", 20200224): 0.5,
            ("Customer_PV", 20300101): 0.5, ("Customer_PV", 20300102): 0.5,
            ("Customer_PV", 20300103): 0.5, ("Customer_PV", 20300104): 0.5,
            ("Customer_PV", 20300105): 0.5, ("Customer_PV", 20300106): 0.5,
            ("Customer_PV", 20300107): 0.5, ("Customer_PV", 20300108): 0.5,
            ("Customer_PV", 20300109): 0.5, ("Customer_PV", 20300110): 0.5,
            ("Customer_PV", 20300111): 0.5, ("Customer_PV", 20300112): 0.5,
            ("Customer_PV", 20300113): 0.5, ("Customer_PV", 20300114): 0.5,
            ("Customer_PV", 20300115): 0.5, ("Customer_PV", 20300116): 0.5,
            ("Customer_PV", 20300117): 0.5, ("Customer_PV", 20300118): 0.5,
            ("Customer_PV", 20300119): 0.5, ("Customer_PV", 20300120): 0.5,
            ("Customer_PV", 20300121): 0.5, ("Customer_PV", 20300122): 0.5,
            ("Customer_PV", 20300123): 0.5, ("Customer_PV", 20300124): 0.5,
            ("Customer_PV", 20300201): 0.5, ("Customer_PV", 20300202): 0.5,
            ("Customer_PV", 20300203): 0.5, ("Customer_PV", 20300204): 0.5,
            ("Customer_PV", 20300205): 0.5, ("Customer_PV", 20300206): 0.5,
            ("Customer_PV", 20300207): 0.5, ("Customer_PV", 20300208): 0.5,
            ("Customer_PV", 20300209): 0.5, ("Customer_PV", 20300210): 0.5,
            ("Customer_PV", 20300211): 0.5, ("Customer_PV", 20300212): 0.5,
            ("Customer_PV", 20300213): 0.5, ("Customer_PV", 20300214): 0.5,
            ("Customer_PV", 20300215): 0.5, ("Customer_PV", 20300216): 0.5,
            ("Customer_PV", 20300217): 0.5, ("Customer_PV", 20300218): 0.5,
            ("Customer_PV", 20300219): 0.5, ("Customer_PV", 20300220): 0.5,
            ("Customer_PV", 20300221): 0.5, ("Customer_PV", 20300222): 0.5,
            ("Customer_PV", 20300223): 0.5, ("Customer_PV", 20300224): 0.5
        }
        actual_cap_factor = {
            (g, tmp): instance.cap_factor_no_curtailment[g, tmp]
            for (g, tmp) in
            instance.VARIABLE_NO_CURTAILMENT_GENERATOR_OPERATIONAL_TIMEPOINTS
        }
        self.assertDictEqual(expected_cap_factor, actual_cap_factor)

if __name__ == "__main__":
    unittest.main()
