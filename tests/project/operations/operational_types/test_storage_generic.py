#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

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
    "project.operations.operational_types.storage_generic"
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


class TestCapacity(unittest.TestCase):
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

    def test_capacity_data_load_correctly(self):
        """
        Test that are data loaded are as expected
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

        # Sets: STORAGE_GENERIC_PROJECTS
        expected_projects = ["Battery", "Battery_Specified"]
        actual_projects = [p for p in instance.STORAGE_GENERIC_PROJECTS]
        self.assertListEqual(expected_projects, actual_projects)

        # STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps = sorted([
            ("Battery", 20200101), ("Battery", 20200102),
            ("Battery", 20200103), ("Battery", 20200104),
            ("Battery", 20200105), ("Battery", 20200106),
            ("Battery", 20200107), ("Battery", 20200108),
            ("Battery", 20200109), ("Battery", 20200110),
            ("Battery", 20200111), ("Battery", 20200112),
            ("Battery", 20200113), ("Battery", 20200114),
            ("Battery", 20200115), ("Battery", 20200116),
            ("Battery", 20200117), ("Battery", 20200118),
            ("Battery", 20200119), ("Battery", 20200120),
            ("Battery", 20200121), ("Battery", 20200122),
            ("Battery", 20200123), ("Battery", 20200124),
            ("Battery", 20200201), ("Battery", 20200202),
            ("Battery", 20200203), ("Battery", 20200204),
            ("Battery", 20200205), ("Battery", 20200206),
            ("Battery", 20200207), ("Battery", 20200208),
            ("Battery", 20200209), ("Battery", 20200210),
            ("Battery", 20200211), ("Battery", 20200212),
            ("Battery", 20200213), ("Battery", 20200214),
            ("Battery", 20200215), ("Battery", 20200216),
            ("Battery", 20200217), ("Battery", 20200218),
            ("Battery", 20200219), ("Battery", 20200220),
            ("Battery", 20200221), ("Battery", 20200222),
            ("Battery", 20200223), ("Battery", 20200224),
            ("Battery", 20300101), ("Battery", 20300102),
            ("Battery", 20300103), ("Battery", 20300104),
            ("Battery", 20300105), ("Battery", 20300106),
            ("Battery", 20300107), ("Battery", 20300108),
            ("Battery", 20300109), ("Battery", 20300110),
            ("Battery", 20300111), ("Battery", 20300112),
            ("Battery", 20300113), ("Battery", 20300114),
            ("Battery", 20300115), ("Battery", 20300116),
            ("Battery", 20300117), ("Battery", 20300118),
            ("Battery", 20300119), ("Battery", 20300120),
            ("Battery", 20300121), ("Battery", 20300122),
            ("Battery", 20300123), ("Battery", 20300124),
            ("Battery", 20300201), ("Battery", 20300202),
            ("Battery", 20300203), ("Battery", 20300204),
            ("Battery", 20300205), ("Battery", 20300206),
            ("Battery", 20300207), ("Battery", 20300208),
            ("Battery", 20300209), ("Battery", 20300210),
            ("Battery", 20300211), ("Battery", 20300212),
            ("Battery", 20300213), ("Battery", 20300214),
            ("Battery", 20300215), ("Battery", 20300216),
            ("Battery", 20300217), ("Battery", 20300218),
            ("Battery", 20300219), ("Battery", 20300220),
            ("Battery", 20300221), ("Battery", 20300222),
            ("Battery", 20300223), ("Battery", 20300224),
            ("Battery_Specified", 20200101), ("Battery_Specified", 20200102),
            ("Battery_Specified", 20200103), ("Battery_Specified", 20200104),
            ("Battery_Specified", 20200105), ("Battery_Specified", 20200106),
            ("Battery_Specified", 20200107), ("Battery_Specified", 20200108),
            ("Battery_Specified", 20200109), ("Battery_Specified", 20200110),
            ("Battery_Specified", 20200111), ("Battery_Specified", 20200112),
            ("Battery_Specified", 20200113), ("Battery_Specified", 20200114),
            ("Battery_Specified", 20200115), ("Battery_Specified", 20200116),
            ("Battery_Specified", 20200117), ("Battery_Specified", 20200118),
            ("Battery_Specified", 20200119), ("Battery_Specified", 20200120),
            ("Battery_Specified", 20200121), ("Battery_Specified", 20200122),
            ("Battery_Specified", 20200123), ("Battery_Specified", 20200124),
            ("Battery_Specified", 20200201), ("Battery_Specified", 20200202),
            ("Battery_Specified", 20200203), ("Battery_Specified", 20200204),
            ("Battery_Specified", 20200205), ("Battery_Specified", 20200206),
            ("Battery_Specified", 20200207), ("Battery_Specified", 20200208),
            ("Battery_Specified", 20200209), ("Battery_Specified", 20200210),
            ("Battery_Specified", 20200211), ("Battery_Specified", 20200212),
            ("Battery_Specified", 20200213), ("Battery_Specified", 20200214),
            ("Battery_Specified", 20200215), ("Battery_Specified", 20200216),
            ("Battery_Specified", 20200217), ("Battery_Specified", 20200218),
            ("Battery_Specified", 20200219), ("Battery_Specified", 20200220),
            ("Battery_Specified", 20200221), ("Battery_Specified", 20200222),
            ("Battery_Specified", 20200223), ("Battery_Specified", 20200224)
        ])
        actual_tmps = sorted([
            tmp for tmp in
            instance.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS
            ])
        self.assertListEqual(expected_tmps, actual_tmps)

        # Param: storage_generic_charging_efficiency
        expected_charging_efficiency = {
            "Battery": 0.8, "Battery_Specified": 0.8
        }
        actual_charging_efficiency = {
            prj: instance.storage_generic_charging_efficiency[prj]
            for prj in instance.STORAGE_GENERIC_PROJECTS
        }
        self.assertDictEqual(expected_charging_efficiency,
                             actual_charging_efficiency)

        # Param: storage_generic_discharging_efficiency
        expected_discharging_efficiency = {
            "Battery": 0.8, "Battery_Specified": 0.8
        }
        actual_discharging_efficiency = {
            prj: instance.storage_generic_discharging_efficiency[prj]
            for prj in instance.STORAGE_GENERIC_PROJECTS
        }
        self.assertDictEqual(expected_discharging_efficiency,
                             actual_discharging_efficiency)

if __name__ == "__main__":
    unittest.main()
