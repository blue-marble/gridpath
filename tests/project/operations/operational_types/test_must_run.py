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
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.must_run"
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


class TestMustRunOperationalType(unittest.TestCase):
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

        # Set: MUST_RUN_GENERATORS
        expected_must_run_gen_set = sorted([
            "Nuclear", "Nuclear_z2"
        ])
        actual_must_run_gen_set = sorted([
            prj for prj in instance.MUST_RUN_GENERATORS
            ])
        self.assertListEqual(expected_must_run_gen_set,
                             actual_must_run_gen_set)

        # Set: MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS
        expected_operational_timpoints_by_project = sorted([
            ("Nuclear", 20200101), ("Nuclear", 20200102),
            ("Nuclear", 20200103), ("Nuclear", 20200104),
            ("Nuclear", 20200105), ("Nuclear", 20200106),
            ("Nuclear", 20200107), ("Nuclear", 20200108),
            ("Nuclear", 20200109), ("Nuclear", 20200110),
            ("Nuclear", 20200111), ("Nuclear", 20200112),
            ("Nuclear", 20200113), ("Nuclear", 20200114),
            ("Nuclear", 20200115), ("Nuclear", 20200116),
            ("Nuclear", 20200117), ("Nuclear", 20200118),
            ("Nuclear", 20200119), ("Nuclear", 20200120),
            ("Nuclear", 20200121), ("Nuclear", 20200122),
            ("Nuclear", 20200123), ("Nuclear", 20200124),
            ("Nuclear", 20200201), ("Nuclear", 20200202),
            ("Nuclear", 20200203), ("Nuclear", 20200204),
            ("Nuclear", 20200205), ("Nuclear", 20200206),
            ("Nuclear", 20200207), ("Nuclear", 20200208),
            ("Nuclear", 20200209), ("Nuclear", 20200210),
            ("Nuclear", 20200211), ("Nuclear", 20200212),
            ("Nuclear", 20200213), ("Nuclear", 20200214),
            ("Nuclear", 20200215), ("Nuclear", 20200216),
            ("Nuclear", 20200217), ("Nuclear", 20200218),
            ("Nuclear", 20200219), ("Nuclear", 20200220),
            ("Nuclear", 20200221), ("Nuclear", 20200222),
            ("Nuclear", 20200223), ("Nuclear", 20200224),
            ("Nuclear", 20300101), ("Nuclear", 20300102),
            ("Nuclear", 20300103), ("Nuclear", 20300104),
            ("Nuclear", 20300105), ("Nuclear", 20300106),
            ("Nuclear", 20300107), ("Nuclear", 20300108),
            ("Nuclear", 20300109), ("Nuclear", 20300110),
            ("Nuclear", 20300111), ("Nuclear", 20300112),
            ("Nuclear", 20300113), ("Nuclear", 20300114),
            ("Nuclear", 20300115), ("Nuclear", 20300116),
            ("Nuclear", 20300117), ("Nuclear", 20300118),
            ("Nuclear", 20300119), ("Nuclear", 20300120),
            ("Nuclear", 20300121), ("Nuclear", 20300122),
            ("Nuclear", 20300123), ("Nuclear", 20300124),
            ("Nuclear", 20300201), ("Nuclear", 20300202),
            ("Nuclear", 20300203), ("Nuclear", 20300204),
            ("Nuclear", 20300205), ("Nuclear", 20300206),
            ("Nuclear", 20300207), ("Nuclear", 20300208),
            ("Nuclear", 20300209), ("Nuclear", 20300210),
            ("Nuclear", 20300211), ("Nuclear", 20300212),
            ("Nuclear", 20300213), ("Nuclear", 20300214),
            ("Nuclear", 20300215), ("Nuclear", 20300216),
            ("Nuclear", 20300217), ("Nuclear", 20300218),
            ("Nuclear", 20300219), ("Nuclear", 20300220),
            ("Nuclear", 20300221), ("Nuclear", 20300222),
            ("Nuclear", 20300223), ("Nuclear", 20300224),
            ("Nuclear_z2", 20200101), ("Nuclear_z2", 20200102),
            ("Nuclear_z2", 20200103), ("Nuclear_z2", 20200104),
            ("Nuclear_z2", 20200105), ("Nuclear_z2", 20200106),
            ("Nuclear_z2", 20200107), ("Nuclear_z2", 20200108),
            ("Nuclear_z2", 20200109), ("Nuclear_z2", 20200110),
            ("Nuclear_z2", 20200111), ("Nuclear_z2", 20200112),
            ("Nuclear_z2", 20200113), ("Nuclear_z2", 20200114),
            ("Nuclear_z2", 20200115), ("Nuclear_z2", 20200116),
            ("Nuclear_z2", 20200117), ("Nuclear_z2", 20200118),
            ("Nuclear_z2", 20200119), ("Nuclear_z2", 20200120),
            ("Nuclear_z2", 20200121), ("Nuclear_z2", 20200122),
            ("Nuclear_z2", 20200123), ("Nuclear_z2", 20200124),
            ("Nuclear_z2", 20200201), ("Nuclear_z2", 20200202),
            ("Nuclear_z2", 20200203), ("Nuclear_z2", 20200204),
            ("Nuclear_z2", 20200205), ("Nuclear_z2", 20200206),
            ("Nuclear_z2", 20200207), ("Nuclear_z2", 20200208),
            ("Nuclear_z2", 20200209), ("Nuclear_z2", 20200210),
            ("Nuclear_z2", 20200211), ("Nuclear_z2", 20200212),
            ("Nuclear_z2", 20200213), ("Nuclear_z2", 20200214),
            ("Nuclear_z2", 20200215), ("Nuclear_z2", 20200216),
            ("Nuclear_z2", 20200217), ("Nuclear_z2", 20200218),
            ("Nuclear_z2", 20200219), ("Nuclear_z2", 20200220),
            ("Nuclear_z2", 20200221), ("Nuclear_z2", 20200222),
            ("Nuclear_z2", 20200223), ("Nuclear_z2", 20200224),
            ("Nuclear_z2", 20300101), ("Nuclear_z2", 20300102),
            ("Nuclear_z2", 20300103), ("Nuclear_z2", 20300104),
            ("Nuclear_z2", 20300105), ("Nuclear_z2", 20300106),
            ("Nuclear_z2", 20300107), ("Nuclear_z2", 20300108),
            ("Nuclear_z2", 20300109), ("Nuclear_z2", 20300110),
            ("Nuclear_z2", 20300111), ("Nuclear_z2", 20300112),
            ("Nuclear_z2", 20300113), ("Nuclear_z2", 20300114),
            ("Nuclear_z2", 20300115), ("Nuclear_z2", 20300116),
            ("Nuclear_z2", 20300117), ("Nuclear_z2", 20300118),
            ("Nuclear_z2", 20300119), ("Nuclear_z2", 20300120),
            ("Nuclear_z2", 20300121), ("Nuclear_z2", 20300122),
            ("Nuclear_z2", 20300123), ("Nuclear_z2", 20300124),
            ("Nuclear_z2", 20300201), ("Nuclear_z2", 20300202),
            ("Nuclear_z2", 20300203), ("Nuclear_z2", 20300204),
            ("Nuclear_z2", 20300205), ("Nuclear_z2", 20300206),
            ("Nuclear_z2", 20300207), ("Nuclear_z2", 20300208),
            ("Nuclear_z2", 20300209), ("Nuclear_z2", 20300210),
            ("Nuclear_z2", 20300211), ("Nuclear_z2", 20300212),
            ("Nuclear_z2", 20300213), ("Nuclear_z2", 20300214),
            ("Nuclear_z2", 20300215), ("Nuclear_z2", 20300216),
            ("Nuclear_z2", 20300217), ("Nuclear_z2", 20300218),
            ("Nuclear_z2", 20300219), ("Nuclear_z2", 20300220),
            ("Nuclear_z2", 20300221), ("Nuclear_z2", 20300222),
            ("Nuclear_z2", 20300223), ("Nuclear_z2", 20300224)
        ])
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.
                 MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_timepoints_by_project)
