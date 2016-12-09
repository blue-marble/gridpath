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
    "temporal.investment.periods", "geography.load_zones",
    "geography.regulation_up_balancing_areas", "project",
    "project.capacity.capacity"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.reserves.regulation_up"
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


class TestRegulationUpProvision(unittest.TestCase):
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

        # Set: REGULATION_UP_PROJECTS
        expected_projects = sorted([
            "Gas_CCGT", "Coal", "Gas_CCGT_New", "Gas_CCGT_z2", "Coal_z2",
            "Battery", "Battery_Specified", "Hydro"
        ])
        actual_projects = sorted([
            prj for prj in instance.REGULATION_UP_PROJECTS
        ])
        self.assertListEqual(expected_projects, actual_projects)

        # Param: regulation_up_zone
        expected_reserves_zone = OrderedDict(sorted(
            {"Gas_CCGT": "Zone1", "Coal": "Zone1", "Gas_CCGT_New": "Zone1",
             "Gas_CCGT_z2": "Zone2", "Coal_z2": "Zone2", "Battery": "Zone1",
             "Battery_Specified": "Zone1", "Hydro": "Zone1"}.items()
        )
        )
        actual_reserves_zone = OrderedDict(sorted(
            {prj: instance.regulation_up_zone[prj]
             for prj in instance.REGULATION_UP_PROJECTS}.items()
        )
        )
        self.assertDictEqual(expected_reserves_zone, actual_reserves_zone)

        # Set: REGULATION_UP_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_prj_op_tmps = sorted([
            ("Gas_CCGT", 20200101), ("Gas_CCGT", 20200102),
            ("Gas_CCGT", 20200103), ("Gas_CCGT", 20200104),
            ("Gas_CCGT", 20200105), ("Gas_CCGT", 20200106),
            ("Gas_CCGT", 20200107), ("Gas_CCGT", 20200108),
            ("Gas_CCGT", 20200109), ("Gas_CCGT", 20200110),
            ("Gas_CCGT", 20200111), ("Gas_CCGT", 20200112),
            ("Gas_CCGT", 20200113), ("Gas_CCGT", 20200114),
            ("Gas_CCGT", 20200115), ("Gas_CCGT", 20200116),
            ("Gas_CCGT", 20200117), ("Gas_CCGT", 20200118),
            ("Gas_CCGT", 20200119), ("Gas_CCGT", 20200120),
            ("Gas_CCGT", 20200121), ("Gas_CCGT", 20200122),
            ("Gas_CCGT", 20200123), ("Gas_CCGT", 20200124),
            ("Gas_CCGT", 20200201), ("Gas_CCGT", 20200202),
            ("Gas_CCGT", 20200203), ("Gas_CCGT", 20200204),
            ("Gas_CCGT", 20200205), ("Gas_CCGT", 20200206),
            ("Gas_CCGT", 20200207), ("Gas_CCGT", 20200208),
            ("Gas_CCGT", 20200209), ("Gas_CCGT", 20200210),
            ("Gas_CCGT", 20200211), ("Gas_CCGT", 20200212),
            ("Gas_CCGT", 20200213), ("Gas_CCGT", 20200214),
            ("Gas_CCGT", 20200215), ("Gas_CCGT", 20200216),
            ("Gas_CCGT", 20200217), ("Gas_CCGT", 20200218),
            ("Gas_CCGT", 20200219), ("Gas_CCGT", 20200220),
            ("Gas_CCGT", 20200221), ("Gas_CCGT", 20200222),
            ("Gas_CCGT", 20200223), ("Gas_CCGT", 20200224),
            ("Gas_CCGT", 20300101), ("Gas_CCGT", 20300102),
            ("Gas_CCGT", 20300103), ("Gas_CCGT", 20300104),
            ("Gas_CCGT", 20300105), ("Gas_CCGT", 20300106),
            ("Gas_CCGT", 20300107), ("Gas_CCGT", 20300108),
            ("Gas_CCGT", 20300109), ("Gas_CCGT", 20300110),
            ("Gas_CCGT", 20300111), ("Gas_CCGT", 20300112),
            ("Gas_CCGT", 20300113), ("Gas_CCGT", 20300114),
            ("Gas_CCGT", 20300115), ("Gas_CCGT", 20300116),
            ("Gas_CCGT", 20300117), ("Gas_CCGT", 20300118),
            ("Gas_CCGT", 20300119), ("Gas_CCGT", 20300120),
            ("Gas_CCGT", 20300121), ("Gas_CCGT", 20300122),
            ("Gas_CCGT", 20300123), ("Gas_CCGT", 20300124),
            ("Gas_CCGT", 20300201), ("Gas_CCGT", 20300202),
            ("Gas_CCGT", 20300203), ("Gas_CCGT", 20300204),
            ("Gas_CCGT", 20300205), ("Gas_CCGT", 20300206),
            ("Gas_CCGT", 20300207), ("Gas_CCGT", 20300208),
            ("Gas_CCGT", 20300209), ("Gas_CCGT", 20300210),
            ("Gas_CCGT", 20300211), ("Gas_CCGT", 20300212),
            ("Gas_CCGT", 20300213), ("Gas_CCGT", 20300214),
            ("Gas_CCGT", 20300215), ("Gas_CCGT", 20300216),
            ("Gas_CCGT", 20300217), ("Gas_CCGT", 20300218),
            ("Gas_CCGT", 20300219), ("Gas_CCGT", 20300220),
            ("Gas_CCGT", 20300221), ("Gas_CCGT", 20300222),
            ("Gas_CCGT", 20300223), ("Gas_CCGT", 20300224),
            ("Coal", 20200101), ("Coal", 20200102),
            ("Coal", 20200103), ("Coal", 20200104),
            ("Coal", 20200105), ("Coal", 20200106),
            ("Coal", 20200107), ("Coal", 20200108),
            ("Coal", 20200109), ("Coal", 20200110),
            ("Coal", 20200111), ("Coal", 20200112),
            ("Coal", 20200113), ("Coal", 20200114),
            ("Coal", 20200115), ("Coal", 20200116),
            ("Coal", 20200117), ("Coal", 20200118),
            ("Coal", 20200119), ("Coal", 20200120),
            ("Coal", 20200121), ("Coal", 20200122),
            ("Coal", 20200123), ("Coal", 20200124),
            ("Coal", 20200201), ("Coal", 20200202),
            ("Coal", 20200203), ("Coal", 20200204),
            ("Coal", 20200205), ("Coal", 20200206),
            ("Coal", 20200207), ("Coal", 20200208),
            ("Coal", 20200209), ("Coal", 20200210),
            ("Coal", 20200211), ("Coal", 20200212),
            ("Coal", 20200213), ("Coal", 20200214),
            ("Coal", 20200215), ("Coal", 20200216),
            ("Coal", 20200217), ("Coal", 20200218),
            ("Coal", 20200219), ("Coal", 20200220),
            ("Coal", 20200221), ("Coal", 20200222),
            ("Coal", 20200223), ("Coal", 20200224),
            ("Coal", 20300101), ("Coal", 20300102),
            ("Coal", 20300103), ("Coal", 20300104),
            ("Coal", 20300105), ("Coal", 20300106),
            ("Coal", 20300107), ("Coal", 20300108),
            ("Coal", 20300109), ("Coal", 20300110),
            ("Coal", 20300111), ("Coal", 20300112),
            ("Coal", 20300113), ("Coal", 20300114),
            ("Coal", 20300115), ("Coal", 20300116),
            ("Coal", 20300117), ("Coal", 20300118),
            ("Coal", 20300119), ("Coal", 20300120),
            ("Coal", 20300121), ("Coal", 20300122),
            ("Coal", 20300123), ("Coal", 20300124),
            ("Coal", 20300201), ("Coal", 20300202),
            ("Coal", 20300203), ("Coal", 20300204),
            ("Coal", 20300205), ("Coal", 20300206),
            ("Coal", 20300207), ("Coal", 20300208),
            ("Coal", 20300209), ("Coal", 20300210),
            ("Coal", 20300211), ("Coal", 20300212),
            ("Coal", 20300213), ("Coal", 20300214),
            ("Coal", 20300215), ("Coal", 20300216),
            ("Coal", 20300217), ("Coal", 20300218),
            ("Coal", 20300219), ("Coal", 20300220),
            ("Coal", 20300221), ("Coal", 20300222),
            ("Coal", 20300223), ("Coal", 20300224),
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
            ("Hydro", 20300223), ("Hydro", 20300224),
            ("Gas_CCGT_z2", 20200101), ("Gas_CCGT_z2", 20200102),
            ("Gas_CCGT_z2", 20200103), ("Gas_CCGT_z2", 20200104),
            ("Gas_CCGT_z2", 20200105), ("Gas_CCGT_z2", 20200106),
            ("Gas_CCGT_z2", 20200107), ("Gas_CCGT_z2", 20200108),
            ("Gas_CCGT_z2", 20200109), ("Gas_CCGT_z2", 20200110),
            ("Gas_CCGT_z2", 20200111), ("Gas_CCGT_z2", 20200112),
            ("Gas_CCGT_z2", 20200113), ("Gas_CCGT_z2", 20200114),
            ("Gas_CCGT_z2", 20200115), ("Gas_CCGT_z2", 20200116),
            ("Gas_CCGT_z2", 20200117), ("Gas_CCGT_z2", 20200118),
            ("Gas_CCGT_z2", 20200119), ("Gas_CCGT_z2", 20200120),
            ("Gas_CCGT_z2", 20200121), ("Gas_CCGT_z2", 20200122),
            ("Gas_CCGT_z2", 20200123), ("Gas_CCGT_z2", 20200124),
            ("Gas_CCGT_z2", 20200201), ("Gas_CCGT_z2", 20200202),
            ("Gas_CCGT_z2", 20200203), ("Gas_CCGT_z2", 20200204),
            ("Gas_CCGT_z2", 20200205), ("Gas_CCGT_z2", 20200206),
            ("Gas_CCGT_z2", 20200207), ("Gas_CCGT_z2", 20200208),
            ("Gas_CCGT_z2", 20200209), ("Gas_CCGT_z2", 20200210),
            ("Gas_CCGT_z2", 20200211), ("Gas_CCGT_z2", 20200212),
            ("Gas_CCGT_z2", 20200213), ("Gas_CCGT_z2", 20200214),
            ("Gas_CCGT_z2", 20200215), ("Gas_CCGT_z2", 20200216),
            ("Gas_CCGT_z2", 20200217), ("Gas_CCGT_z2", 20200218),
            ("Gas_CCGT_z2", 20200219), ("Gas_CCGT_z2", 20200220),
            ("Gas_CCGT_z2", 20200221), ("Gas_CCGT_z2", 20200222),
            ("Gas_CCGT_z2", 20200223), ("Gas_CCGT_z2", 20200224),
            ("Gas_CCGT_z2", 20300101), ("Gas_CCGT_z2", 20300102),
            ("Gas_CCGT_z2", 20300103), ("Gas_CCGT_z2", 20300104),
            ("Gas_CCGT_z2", 20300105), ("Gas_CCGT_z2", 20300106),
            ("Gas_CCGT_z2", 20300107), ("Gas_CCGT_z2", 20300108),
            ("Gas_CCGT_z2", 20300109), ("Gas_CCGT_z2", 20300110),
            ("Gas_CCGT_z2", 20300111), ("Gas_CCGT_z2", 20300112),
            ("Gas_CCGT_z2", 20300113), ("Gas_CCGT_z2", 20300114),
            ("Gas_CCGT_z2", 20300115), ("Gas_CCGT_z2", 20300116),
            ("Gas_CCGT_z2", 20300117), ("Gas_CCGT_z2", 20300118),
            ("Gas_CCGT_z2", 20300119), ("Gas_CCGT_z2", 20300120),
            ("Gas_CCGT_z2", 20300121), ("Gas_CCGT_z2", 20300122),
            ("Gas_CCGT_z2", 20300123), ("Gas_CCGT_z2", 20300124),
            ("Gas_CCGT_z2", 20300201), ("Gas_CCGT_z2", 20300202),
            ("Gas_CCGT_z2", 20300203), ("Gas_CCGT_z2", 20300204),
            ("Gas_CCGT_z2", 20300205), ("Gas_CCGT_z2", 20300206),
            ("Gas_CCGT_z2", 20300207), ("Gas_CCGT_z2", 20300208),
            ("Gas_CCGT_z2", 20300209), ("Gas_CCGT_z2", 20300210),
            ("Gas_CCGT_z2", 20300211), ("Gas_CCGT_z2", 20300212),
            ("Gas_CCGT_z2", 20300213), ("Gas_CCGT_z2", 20300214),
            ("Gas_CCGT_z2", 20300215), ("Gas_CCGT_z2", 20300216),
            ("Gas_CCGT_z2", 20300217), ("Gas_CCGT_z2", 20300218),
            ("Gas_CCGT_z2", 20300219), ("Gas_CCGT_z2", 20300220),
            ("Gas_CCGT_z2", 20300221), ("Gas_CCGT_z2", 20300222),
            ("Gas_CCGT_z2", 20300223), ("Gas_CCGT_z2", 20300224),
            ("Coal_z2", 20200101), ("Coal_z2", 20200102),
            ("Coal_z2", 20200103), ("Coal_z2", 20200104),
            ("Coal_z2", 20200105), ("Coal_z2", 20200106),
            ("Coal_z2", 20200107), ("Coal_z2", 20200108),
            ("Coal_z2", 20200109), ("Coal_z2", 20200110),
            ("Coal_z2", 20200111), ("Coal_z2", 20200112),
            ("Coal_z2", 20200113), ("Coal_z2", 20200114),
            ("Coal_z2", 20200115), ("Coal_z2", 20200116),
            ("Coal_z2", 20200117), ("Coal_z2", 20200118),
            ("Coal_z2", 20200119), ("Coal_z2", 20200120),
            ("Coal_z2", 20200121), ("Coal_z2", 20200122),
            ("Coal_z2", 20200123), ("Coal_z2", 20200124),
            ("Coal_z2", 20200201), ("Coal_z2", 20200202),
            ("Coal_z2", 20200203), ("Coal_z2", 20200204),
            ("Coal_z2", 20200205), ("Coal_z2", 20200206),
            ("Coal_z2", 20200207), ("Coal_z2", 20200208),
            ("Coal_z2", 20200209), ("Coal_z2", 20200210),
            ("Coal_z2", 20200211), ("Coal_z2", 20200212),
            ("Coal_z2", 20200213), ("Coal_z2", 20200214),
            ("Coal_z2", 20200215), ("Coal_z2", 20200216),
            ("Coal_z2", 20200217), ("Coal_z2", 20200218),
            ("Coal_z2", 20200219), ("Coal_z2", 20200220),
            ("Coal_z2", 20200221), ("Coal_z2", 20200222),
            ("Coal_z2", 20200223), ("Coal_z2", 20200224),
            ("Coal_z2", 20300101), ("Coal_z2", 20300102),
            ("Coal_z2", 20300103), ("Coal_z2", 20300104),
            ("Coal_z2", 20300105), ("Coal_z2", 20300106),
            ("Coal_z2", 20300107), ("Coal_z2", 20300108),
            ("Coal_z2", 20300109), ("Coal_z2", 20300110),
            ("Coal_z2", 20300111), ("Coal_z2", 20300112),
            ("Coal_z2", 20300113), ("Coal_z2", 20300114),
            ("Coal_z2", 20300115), ("Coal_z2", 20300116),
            ("Coal_z2", 20300117), ("Coal_z2", 20300118),
            ("Coal_z2", 20300119), ("Coal_z2", 20300120),
            ("Coal_z2", 20300121), ("Coal_z2", 20300122),
            ("Coal_z2", 20300123), ("Coal_z2", 20300124),
            ("Coal_z2", 20300201), ("Coal_z2", 20300202),
            ("Coal_z2", 20300203), ("Coal_z2", 20300204),
            ("Coal_z2", 20300205), ("Coal_z2", 20300206),
            ("Coal_z2", 20300207), ("Coal_z2", 20300208),
            ("Coal_z2", 20300209), ("Coal_z2", 20300210),
            ("Coal_z2", 20300211), ("Coal_z2", 20300212),
            ("Coal_z2", 20300213), ("Coal_z2", 20300214),
            ("Coal_z2", 20300215), ("Coal_z2", 20300216),
            ("Coal_z2", 20300217), ("Coal_z2", 20300218),
            ("Coal_z2", 20300219), ("Coal_z2", 20300220),
            ("Coal_z2", 20300221), ("Coal_z2", 20300222),
            ("Coal_z2", 20300223), ("Coal_z2", 20300224),
            ("Gas_CCGT_New", 20200101), ("Gas_CCGT_New", 20200102),
            ("Gas_CCGT_New", 20200103), ("Gas_CCGT_New", 20200104),
            ("Gas_CCGT_New", 20200105), ("Gas_CCGT_New", 20200106),
            ("Gas_CCGT_New", 20200107), ("Gas_CCGT_New", 20200108),
            ("Gas_CCGT_New", 20200109), ("Gas_CCGT_New", 20200110),
            ("Gas_CCGT_New", 20200111), ("Gas_CCGT_New", 20200112),
            ("Gas_CCGT_New", 20200113), ("Gas_CCGT_New", 20200114),
            ("Gas_CCGT_New", 20200115), ("Gas_CCGT_New", 20200116),
            ("Gas_CCGT_New", 20200117), ("Gas_CCGT_New", 20200118),
            ("Gas_CCGT_New", 20200119), ("Gas_CCGT_New", 20200120),
            ("Gas_CCGT_New", 20200121), ("Gas_CCGT_New", 20200122),
            ("Gas_CCGT_New", 20200123), ("Gas_CCGT_New", 20200124),
            ("Gas_CCGT_New", 20200201), ("Gas_CCGT_New", 20200202),
            ("Gas_CCGT_New", 20200203), ("Gas_CCGT_New", 20200204),
            ("Gas_CCGT_New", 20200205), ("Gas_CCGT_New", 20200206),
            ("Gas_CCGT_New", 20200207), ("Gas_CCGT_New", 20200208),
            ("Gas_CCGT_New", 20200209), ("Gas_CCGT_New", 20200210),
            ("Gas_CCGT_New", 20200211), ("Gas_CCGT_New", 20200212),
            ("Gas_CCGT_New", 20200213), ("Gas_CCGT_New", 20200214),
            ("Gas_CCGT_New", 20200215), ("Gas_CCGT_New", 20200216),
            ("Gas_CCGT_New", 20200217), ("Gas_CCGT_New", 20200218),
            ("Gas_CCGT_New", 20200219), ("Gas_CCGT_New", 20200220),
            ("Gas_CCGT_New", 20200221), ("Gas_CCGT_New", 20200222),
            ("Gas_CCGT_New", 20200223), ("Gas_CCGT_New", 20200224),
            ("Gas_CCGT_New", 20300101), ("Gas_CCGT_New", 20300102),
            ("Gas_CCGT_New", 20300103), ("Gas_CCGT_New", 20300104),
            ("Gas_CCGT_New", 20300105), ("Gas_CCGT_New", 20300106),
            ("Gas_CCGT_New", 20300107), ("Gas_CCGT_New", 20300108),
            ("Gas_CCGT_New", 20300109), ("Gas_CCGT_New", 20300110),
            ("Gas_CCGT_New", 20300111), ("Gas_CCGT_New", 20300112),
            ("Gas_CCGT_New", 20300113), ("Gas_CCGT_New", 20300114),
            ("Gas_CCGT_New", 20300115), ("Gas_CCGT_New", 20300116),
            ("Gas_CCGT_New", 20300117), ("Gas_CCGT_New", 20300118),
            ("Gas_CCGT_New", 20300119), ("Gas_CCGT_New", 20300120),
            ("Gas_CCGT_New", 20300121), ("Gas_CCGT_New", 20300122),
            ("Gas_CCGT_New", 20300123), ("Gas_CCGT_New", 20300124),
            ("Gas_CCGT_New", 20300201), ("Gas_CCGT_New", 20300202),
            ("Gas_CCGT_New", 20300203), ("Gas_CCGT_New", 20300204),
            ("Gas_CCGT_New", 20300205), ("Gas_CCGT_New", 20300206),
            ("Gas_CCGT_New", 20300207), ("Gas_CCGT_New", 20300208),
            ("Gas_CCGT_New", 20300209), ("Gas_CCGT_New", 20300210),
            ("Gas_CCGT_New", 20300211), ("Gas_CCGT_New", 20300212),
            ("Gas_CCGT_New", 20300213), ("Gas_CCGT_New", 20300214),
            ("Gas_CCGT_New", 20300215), ("Gas_CCGT_New", 20300216),
            ("Gas_CCGT_New", 20300217), ("Gas_CCGT_New", 20300218),
            ("Gas_CCGT_New", 20300219), ("Gas_CCGT_New", 20300220),
            ("Gas_CCGT_New", 20300221), ("Gas_CCGT_New", 20300222),
            ("Gas_CCGT_New", 20300223), ("Gas_CCGT_New", 20300224),
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
            ("Battery_Specified", 20200223), ("Battery_Specified", 20200224),
        ])
        actual_prj_op_tmps = sorted([
            (prj, tmp) for (prj, tmp) in
            instance.REGULATION_UP_PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_prj_op_tmps, actual_prj_op_tmps)

if __name__ == "__main__":
    unittest.main()
