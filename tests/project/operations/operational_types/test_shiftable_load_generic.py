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
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity", "project.fuels", "project.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.shiftable_load_generic"
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


class TestAlwaysOnOperationalType(unittest.TestCase):
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

        # Set: SHIFTABLE_LOAD_GENERIC_PROJECTS
        expected_always_on_gen_set = sorted([
            "Shift_DR"
        ])
        actual_always_on_gen_set = sorted([
            prj for prj in instance.SHIFTABLE_LOAD_GENERIC_PROJECTS
        ])
        self.assertListEqual(expected_always_on_gen_set,
                             actual_always_on_gen_set)

        # Set: SHIFTABLE_LOAD_GENERIC_PROJECTS_OPERATIONAL_TIMEPOINTS
        expected_operational_timpoints_by_project = sorted([
            ("Shift_DR", 20200101), ("Shift_DR", 20200102),
            ("Shift_DR", 20200103), ("Shift_DR", 20200104),
            ("Shift_DR", 20200105), ("Shift_DR", 20200106),
            ("Shift_DR", 20200107), ("Shift_DR", 20200108),
            ("Shift_DR", 20200109), ("Shift_DR", 20200110),
            ("Shift_DR", 20200111), ("Shift_DR", 20200112),
            ("Shift_DR", 20200113), ("Shift_DR", 20200114),
            ("Shift_DR", 20200115), ("Shift_DR", 20200116),
            ("Shift_DR", 20200117), ("Shift_DR", 20200118),
            ("Shift_DR", 20200119), ("Shift_DR", 20200120),
            ("Shift_DR", 20200121), ("Shift_DR", 20200122),
            ("Shift_DR", 20200123), ("Shift_DR", 20200124),
            ("Shift_DR", 20200201), ("Shift_DR", 20200202),
            ("Shift_DR", 20200203), ("Shift_DR", 20200204),
            ("Shift_DR", 20200205), ("Shift_DR", 20200206),
            ("Shift_DR", 20200207), ("Shift_DR", 20200208),
            ("Shift_DR", 20200209), ("Shift_DR", 20200210),
            ("Shift_DR", 20200211), ("Shift_DR", 20200212),
            ("Shift_DR", 20200213), ("Shift_DR", 20200214),
            ("Shift_DR", 20200215), ("Shift_DR", 20200216),
            ("Shift_DR", 20200217), ("Shift_DR", 20200218),
            ("Shift_DR", 20200219), ("Shift_DR", 20200220),
            ("Shift_DR", 20200221), ("Shift_DR", 20200222),
            ("Shift_DR", 20200223), ("Shift_DR", 20200224),
            ("Shift_DR", 20300101), ("Shift_DR", 20300102),
            ("Shift_DR", 20300103), ("Shift_DR", 20300104),
            ("Shift_DR", 20300105), ("Shift_DR", 20300106),
            ("Shift_DR", 20300107), ("Shift_DR", 20300108),
            ("Shift_DR", 20300109), ("Shift_DR", 20300110),
            ("Shift_DR", 20300111), ("Shift_DR", 20300112),
            ("Shift_DR", 20300113), ("Shift_DR", 20300114),
            ("Shift_DR", 20300115), ("Shift_DR", 20300116),
            ("Shift_DR", 20300117), ("Shift_DR", 20300118),
            ("Shift_DR", 20300119), ("Shift_DR", 20300120),
            ("Shift_DR", 20300121), ("Shift_DR", 20300122),
            ("Shift_DR", 20300123), ("Shift_DR", 20300124),
            ("Shift_DR", 20300201), ("Shift_DR", 20300202),
            ("Shift_DR", 20300203), ("Shift_DR", 20300204),
            ("Shift_DR", 20300205), ("Shift_DR", 20300206),
            ("Shift_DR", 20300207), ("Shift_DR", 20300208),
            ("Shift_DR", 20300209), ("Shift_DR", 20300210),
            ("Shift_DR", 20300211), ("Shift_DR", 20300212),
            ("Shift_DR", 20300213), ("Shift_DR", 20300214),
            ("Shift_DR", 20300215), ("Shift_DR", 20300216),
            ("Shift_DR", 20300217), ("Shift_DR", 20300218),
            ("Shift_DR", 20300219), ("Shift_DR", 20300220),
            ("Shift_DR", 20300221), ("Shift_DR", 20300222),
            ("Shift_DR", 20300223), ("Shift_DR", 20300224)
        ])
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_timepoints_by_project)

        # Set: SHIFTABLE_LOAD_GENERIC_PROJECTS_OPERATIONAL_HORIZONS
        expected_operational_timpoints_by_project = sorted([
            ("Shift_DR", 202001), ("Shift_DR", 202002),
            ("Shift_DR", 203001), ("Shift_DR", 203002)
        ])
        actual_operational_horizons_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_HORIZONS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_horizons_by_project)
        

if __name__ == "__main__":
    unittest.main()
