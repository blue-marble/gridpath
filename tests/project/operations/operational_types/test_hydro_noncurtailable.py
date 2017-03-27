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
     "project.capacity.capacity"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.hydro_noncurtailable"
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


class TestHydroCurtailable(unittest.TestCase):
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

        # Sets: HYDRO_NONCURTAILABLE_PROJECTS
        expected_projects = ["Hydro_NonCurtailable"]
        actual_projects = [p for p in instance.HYDRO_NONCURTAILABLE_PROJECTS]
        self.assertListEqual(expected_projects, actual_projects)

        # Sets: HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
        expected_operational_horizons = sorted(
            [("Hydro_NonCurtailable", 202001),
             ("Hydro_NonCurtailable", 202002),
             ("Hydro_NonCurtailable", 203001),
             ("Hydro_NonCurtailable", 203002)]
        )
        actual_operational_horizons = sorted(
            [p for p in instance.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
             ]
            )
        self.assertListEqual(expected_operational_horizons,
                             actual_operational_horizons)

        # Param: hydro_noncurtailable_average_power_mwa
        expected_average_power = OrderedDict(
            sorted({("Hydro_NonCurtailable", 202001): 3,
                    ("Hydro_NonCurtailable", 202002): 3,
                    ("Hydro_NonCurtailable", 203001): 3,
                    ("Hydro_NonCurtailable", 203002): 3}.items())
        )
        actual_average_power = OrderedDict(
            sorted(
                {(prj, period):
                    instance.hydro_noncurtailable_average_power_mwa[prj, period]
                 for (prj, period) in
                 instance.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_average_power, actual_average_power)

        # Param: hydro_noncurtailable_min_power_mw
        expected_min_power = OrderedDict(
            sorted({("Hydro_NonCurtailable", 202001): 1,
                    ("Hydro_NonCurtailable", 202002): 1,
                    ("Hydro_NonCurtailable", 203001): 1,
                    ("Hydro_NonCurtailable", 203002): 1}.items())
        )
        actual_min_power = OrderedDict(
            sorted(
                {(prj, period):
                    instance.hydro_noncurtailable_min_power_mw[prj, period]
                 for (prj, period) in
                 instance.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_power, actual_min_power)

        # Param: hydro_noncurtailable_max_power_mw
        expected_max_power = OrderedDict(
            sorted({("Hydro_NonCurtailable", 202001): 6,
                    ("Hydro_NonCurtailable", 202002): 6,
                    ("Hydro_NonCurtailable", 203001): 6,
                    ("Hydro_NonCurtailable", 203002): 6}.items())
        )
        actual_max_power = OrderedDict(
            sorted(
                {(prj, period):
                    instance.hydro_noncurtailable_max_power_mw[prj, period]
                 for (prj, period) in
                 instance.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_power, actual_max_power)

        # HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps = sorted([
            ("Hydro_NonCurtailable", 20200101),
            ("Hydro_NonCurtailable", 20200102),
            ("Hydro_NonCurtailable", 20200103),
            ("Hydro_NonCurtailable", 20200104),
            ("Hydro_NonCurtailable", 20200105),
            ("Hydro_NonCurtailable", 20200106),
            ("Hydro_NonCurtailable", 20200107),
            ("Hydro_NonCurtailable", 20200108),
            ("Hydro_NonCurtailable", 20200109),
            ("Hydro_NonCurtailable", 20200110),
            ("Hydro_NonCurtailable", 20200111),
            ("Hydro_NonCurtailable", 20200112),
            ("Hydro_NonCurtailable", 20200113),
            ("Hydro_NonCurtailable", 20200114),
            ("Hydro_NonCurtailable", 20200115),
            ("Hydro_NonCurtailable", 20200116),
            ("Hydro_NonCurtailable", 20200117),
            ("Hydro_NonCurtailable", 20200118),
            ("Hydro_NonCurtailable", 20200119),
            ("Hydro_NonCurtailable", 20200120),
            ("Hydro_NonCurtailable", 20200121),
            ("Hydro_NonCurtailable", 20200122),
            ("Hydro_NonCurtailable", 20200123),
            ("Hydro_NonCurtailable", 20200124),
            ("Hydro_NonCurtailable", 20200201),
            ("Hydro_NonCurtailable", 20200202),
            ("Hydro_NonCurtailable", 20200203),
            ("Hydro_NonCurtailable", 20200204),
            ("Hydro_NonCurtailable", 20200205),
            ("Hydro_NonCurtailable", 20200206),
            ("Hydro_NonCurtailable", 20200207),
            ("Hydro_NonCurtailable", 20200208),
            ("Hydro_NonCurtailable", 20200209),
            ("Hydro_NonCurtailable", 20200210),
            ("Hydro_NonCurtailable", 20200211),
            ("Hydro_NonCurtailable", 20200212),
            ("Hydro_NonCurtailable", 20200213),
            ("Hydro_NonCurtailable", 20200214),
            ("Hydro_NonCurtailable", 20200215),
            ("Hydro_NonCurtailable", 20200216),
            ("Hydro_NonCurtailable", 20200217),
            ("Hydro_NonCurtailable", 20200218),
            ("Hydro_NonCurtailable", 20200219),
            ("Hydro_NonCurtailable", 20200220),
            ("Hydro_NonCurtailable", 20200221),
            ("Hydro_NonCurtailable", 20200222),
            ("Hydro_NonCurtailable", 20200223),
            ("Hydro_NonCurtailable", 20200224),
            ("Hydro_NonCurtailable", 20300101),
            ("Hydro_NonCurtailable", 20300102),
            ("Hydro_NonCurtailable", 20300103),
            ("Hydro_NonCurtailable", 20300104),
            ("Hydro_NonCurtailable", 20300105),
            ("Hydro_NonCurtailable", 20300106),
            ("Hydro_NonCurtailable", 20300107),
            ("Hydro_NonCurtailable", 20300108),
            ("Hydro_NonCurtailable", 20300109),
            ("Hydro_NonCurtailable", 20300110),
            ("Hydro_NonCurtailable", 20300111),
            ("Hydro_NonCurtailable", 20300112),
            ("Hydro_NonCurtailable", 20300113),
            ("Hydro_NonCurtailable", 20300114),
            ("Hydro_NonCurtailable", 20300115),
            ("Hydro_NonCurtailable", 20300116),
            ("Hydro_NonCurtailable", 20300117),
            ("Hydro_NonCurtailable", 20300118),
            ("Hydro_NonCurtailable", 20300119),
            ("Hydro_NonCurtailable", 20300120),
            ("Hydro_NonCurtailable", 20300121),
            ("Hydro_NonCurtailable", 20300122),
            ("Hydro_NonCurtailable", 20300123),
            ("Hydro_NonCurtailable", 20300124),
            ("Hydro_NonCurtailable", 20300201),
            ("Hydro_NonCurtailable", 20300202),
            ("Hydro_NonCurtailable", 20300203),
            ("Hydro_NonCurtailable", 20300204),
            ("Hydro_NonCurtailable", 20300205),
            ("Hydro_NonCurtailable", 20300206),
            ("Hydro_NonCurtailable", 20300207),
            ("Hydro_NonCurtailable", 20300208),
            ("Hydro_NonCurtailable", 20300209),
            ("Hydro_NonCurtailable", 20300210),
            ("Hydro_NonCurtailable", 20300211),
            ("Hydro_NonCurtailable", 20300212),
            ("Hydro_NonCurtailable", 20300213),
            ("Hydro_NonCurtailable", 20300214),
            ("Hydro_NonCurtailable", 20300215),
            ("Hydro_NonCurtailable", 20300216),
            ("Hydro_NonCurtailable", 20300217),
            ("Hydro_NonCurtailable", 20300218),
            ("Hydro_NonCurtailable", 20300219),
            ("Hydro_NonCurtailable", 20300220),
            ("Hydro_NonCurtailable", 20300221),
            ("Hydro_NonCurtailable", 20300222),
            ("Hydro_NonCurtailable", 20300223),
            ("Hydro_NonCurtailable", 20300224)
        ])
        actual_tmps = sorted([
            tmp for tmp in
            instance.HYDRO_NONCURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS
            ])
        self.assertListEqual(expected_tmps, actual_tmps)

if __name__ == "__main__":
    unittest.main()
