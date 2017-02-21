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
    "project.operations.operational_types.hydro_conventional"
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

        # Sets: HYDRO_CONVENTIONAL_PROJECTS
        expected_projects = ["Hydro"]
        actual_projects = [p for p in instance.HYDRO_CONVENTIONAL_PROJECTS]
        self.assertListEqual(expected_projects, actual_projects)

        # Sets: HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS
        expected_operational_horizons = sorted(
            [("Hydro", 202001), ("Hydro", 202002),
             ("Hydro", 203001), ("Hydro", 203002)]
        )
        actual_operational_horizons = sorted(
            [p for p in instance.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS
             ]
            )
        self.assertListEqual(expected_operational_horizons,
                             actual_operational_horizons)

        # Param: hydro_specified_average_power_mwa
        expected_average_power = OrderedDict(
            sorted({("Hydro", 202001): 3, ("Hydro", 202002): 3,
                    ("Hydro", 203001): 3, ("Hydro", 203002): 3}.items())
        )
        actual_average_power = OrderedDict(
            sorted(
                {(prj, period):
                    instance.hydro_specified_average_power_mwa[prj, period]
                 for (prj, period) in
                 instance.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_average_power, actual_average_power)

        # Param: hydro_specified_min_power_mw
        expected_min_power = OrderedDict(
            sorted({("Hydro", 202001): 1, ("Hydro", 202002): 1,
                    ("Hydro", 203001): 1, ("Hydro", 203002): 1}.items())
        )
        actual_min_power = OrderedDict(
            sorted(
                {(prj, period):
                    instance.hydro_specified_min_power_mw[prj, period]
                 for (prj, period) in
                 instance.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_power, actual_min_power)

        # Param: hydro_specified_max_power_mw
        expected_max_power = OrderedDict(
            sorted({("Hydro", 202001): 6, ("Hydro", 202002): 6,
                    ("Hydro", 203001): 6, ("Hydro", 203002): 6}.items())
        )
        actual_max_power = OrderedDict(
            sorted(
                {(prj, period):
                    instance.hydro_specified_max_power_mw[prj, period]
                 for (prj, period) in
                 instance.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_power, actual_max_power)

        # HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps = sorted([
            ("Hydro", 20200101), ("Hydro", 20200102),
            ("Hydro", 20200103), ("Hydro", 20200104),
            ("Hydro", 20200105), ("Hydro", 20200106),
            ("Hydro", 20200107), ("Hydro", 20200108),
            ("Hydro", 20200109), ("Hydro", 20200110),
            ("Hydro", 20200111), ("Hydro", 20200112),
            ("Hydro", 20200113), ("Hydro", 20200114),
            ("Hydro", 20200115), ("Hydro", 20200116),
            ("Hydro", 20200117), ("Hydro", 20200118),
            ("Hydro", 20200119), ("Hydro", 20200120),
            ("Hydro", 20200121), ("Hydro", 20200122),
            ("Hydro", 20200123), ("Hydro", 20200124),
            ("Hydro", 20200201), ("Hydro", 20200202),
            ("Hydro", 20200203), ("Hydro", 20200204),
            ("Hydro", 20200205), ("Hydro", 20200206),
            ("Hydro", 20200207), ("Hydro", 20200208),
            ("Hydro", 20200209), ("Hydro", 20200210),
            ("Hydro", 20200211), ("Hydro", 20200212),
            ("Hydro", 20200213), ("Hydro", 20200214),
            ("Hydro", 20200215), ("Hydro", 20200216),
            ("Hydro", 20200217), ("Hydro", 20200218),
            ("Hydro", 20200219), ("Hydro", 20200220),
            ("Hydro", 20200221), ("Hydro", 20200222),
            ("Hydro", 20200223), ("Hydro", 20200224),
            ("Hydro", 20300101), ("Hydro", 20300102),
            ("Hydro", 20300103), ("Hydro", 20300104),
            ("Hydro", 20300105), ("Hydro", 20300106),
            ("Hydro", 20300107), ("Hydro", 20300108),
            ("Hydro", 20300109), ("Hydro", 20300110),
            ("Hydro", 20300111), ("Hydro", 20300112),
            ("Hydro", 20300113), ("Hydro", 20300114),
            ("Hydro", 20300115), ("Hydro", 20300116),
            ("Hydro", 20300117), ("Hydro", 20300118),
            ("Hydro", 20300119), ("Hydro", 20300120),
            ("Hydro", 20300121), ("Hydro", 20300122),
            ("Hydro", 20300123), ("Hydro", 20300124),
            ("Hydro", 20300201), ("Hydro", 20300202),
            ("Hydro", 20300203), ("Hydro", 20300204),
            ("Hydro", 20300205), ("Hydro", 20300206),
            ("Hydro", 20300207), ("Hydro", 20300208),
            ("Hydro", 20300209), ("Hydro", 20300210),
            ("Hydro", 20300211), ("Hydro", 20300212),
            ("Hydro", 20300213), ("Hydro", 20300214),
            ("Hydro", 20300215), ("Hydro", 20300216),
            ("Hydro", 20300217), ("Hydro", 20300218),
            ("Hydro", 20300219), ("Hydro", 20300220),
            ("Hydro", 20300221), ("Hydro", 20300222),
            ("Hydro", 20300223), ("Hydro", 20300224)
        ])
        actual_tmps = sorted([
            tmp for tmp in
            instance.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS
            ])
        self.assertListEqual(expected_tmps, actual_tmps)

if __name__ == "__main__":
    unittest.main()
