#!/usr/bin/env python

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
    "project.operations.operational_types.dispatchable_capacity_commit"
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


class TestDispatchableCapacityCommitOperationalType(unittest.TestCase):
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

        # Set: DISPATCHABLE_CAPACITY_COMMIT_GENERATORS
        expected_disp_cap_commit_gen_set = sorted([
            "Gas_CCGT", "Coal", "Gas_CT", "Gas_CCGT_New", "Gas_CT_New",
            "Gas_CCGT_z2", "Coal_z2", "Gas_CT_z2"
        ])
        actual_disp_cap_commit_gen_set = sorted([
            prj for prj in instance.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS
            ])
        self.assertListEqual(expected_disp_cap_commit_gen_set,
                             actual_disp_cap_commit_gen_set)

        # Set: DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS
        expected_operational_timpoints_by_project = sorted([
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
            ("Gas_CT", 20200101), ("Gas_CT", 20200102),
            ("Gas_CT", 20200103), ("Gas_CT", 20200104),
            ("Gas_CT", 20200105), ("Gas_CT", 20200106),
            ("Gas_CT", 20200107), ("Gas_CT", 20200108),
            ("Gas_CT", 20200109), ("Gas_CT", 20200110),
            ("Gas_CT", 20200111), ("Gas_CT", 20200112),
            ("Gas_CT", 20200113), ("Gas_CT", 20200114),
            ("Gas_CT", 20200115), ("Gas_CT", 20200116),
            ("Gas_CT", 20200117), ("Gas_CT", 20200118),
            ("Gas_CT", 20200119), ("Gas_CT", 20200120),
            ("Gas_CT", 20200121), ("Gas_CT", 20200122),
            ("Gas_CT", 20200123), ("Gas_CT", 20200124),
            ("Gas_CT", 20200201), ("Gas_CT", 20200202),
            ("Gas_CT", 20200203), ("Gas_CT", 20200204),
            ("Gas_CT", 20200205), ("Gas_CT", 20200206),
            ("Gas_CT", 20200207), ("Gas_CT", 20200208),
            ("Gas_CT", 20200209), ("Gas_CT", 20200210),
            ("Gas_CT", 20200211), ("Gas_CT", 20200212),
            ("Gas_CT", 20200213), ("Gas_CT", 20200214),
            ("Gas_CT", 20200215), ("Gas_CT", 20200216),
            ("Gas_CT", 20200217), ("Gas_CT", 20200218),
            ("Gas_CT", 20200219), ("Gas_CT", 20200220),
            ("Gas_CT", 20200221), ("Gas_CT", 20200222),
            ("Gas_CT", 20200223), ("Gas_CT", 20200224),
            ("Gas_CT", 20300101), ("Gas_CT", 20300102),
            ("Gas_CT", 20300103), ("Gas_CT", 20300104),
            ("Gas_CT", 20300105), ("Gas_CT", 20300106),
            ("Gas_CT", 20300107), ("Gas_CT", 20300108),
            ("Gas_CT", 20300109), ("Gas_CT", 20300110),
            ("Gas_CT", 20300111), ("Gas_CT", 20300112),
            ("Gas_CT", 20300113), ("Gas_CT", 20300114),
            ("Gas_CT", 20300115), ("Gas_CT", 20300116),
            ("Gas_CT", 20300117), ("Gas_CT", 20300118),
            ("Gas_CT", 20300119), ("Gas_CT", 20300120),
            ("Gas_CT", 20300121), ("Gas_CT", 20300122),
            ("Gas_CT", 20300123), ("Gas_CT", 20300124),
            ("Gas_CT", 20300201), ("Gas_CT", 20300202),
            ("Gas_CT", 20300203), ("Gas_CT", 20300204),
            ("Gas_CT", 20300205), ("Gas_CT", 20300206),
            ("Gas_CT", 20300207), ("Gas_CT", 20300208),
            ("Gas_CT", 20300209), ("Gas_CT", 20300210),
            ("Gas_CT", 20300211), ("Gas_CT", 20300212),
            ("Gas_CT", 20300213), ("Gas_CT", 20300214),
            ("Gas_CT", 20300215), ("Gas_CT", 20300216),
            ("Gas_CT", 20300217), ("Gas_CT", 20300218),
            ("Gas_CT", 20300219), ("Gas_CT", 20300220),
            ("Gas_CT", 20300221), ("Gas_CT", 20300222),
            ("Gas_CT", 20300223), ("Gas_CT", 20300224),
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
            ("Gas_CT_z2", 20200101), ("Gas_CT_z2", 20200102),
            ("Gas_CT_z2", 20200103), ("Gas_CT_z2", 20200104),
            ("Gas_CT_z2", 20200105), ("Gas_CT_z2", 20200106),
            ("Gas_CT_z2", 20200107), ("Gas_CT_z2", 20200108),
            ("Gas_CT_z2", 20200109), ("Gas_CT_z2", 20200110),
            ("Gas_CT_z2", 20200111), ("Gas_CT_z2", 20200112),
            ("Gas_CT_z2", 20200113), ("Gas_CT_z2", 20200114),
            ("Gas_CT_z2", 20200115), ("Gas_CT_z2", 20200116),
            ("Gas_CT_z2", 20200117), ("Gas_CT_z2", 20200118),
            ("Gas_CT_z2", 20200119), ("Gas_CT_z2", 20200120),
            ("Gas_CT_z2", 20200121), ("Gas_CT_z2", 20200122),
            ("Gas_CT_z2", 20200123), ("Gas_CT_z2", 20200124),
            ("Gas_CT_z2", 20200201), ("Gas_CT_z2", 20200202),
            ("Gas_CT_z2", 20200203), ("Gas_CT_z2", 20200204),
            ("Gas_CT_z2", 20200205), ("Gas_CT_z2", 20200206),
            ("Gas_CT_z2", 20200207), ("Gas_CT_z2", 20200208),
            ("Gas_CT_z2", 20200209), ("Gas_CT_z2", 20200210),
            ("Gas_CT_z2", 20200211), ("Gas_CT_z2", 20200212),
            ("Gas_CT_z2", 20200213), ("Gas_CT_z2", 20200214),
            ("Gas_CT_z2", 20200215), ("Gas_CT_z2", 20200216),
            ("Gas_CT_z2", 20200217), ("Gas_CT_z2", 20200218),
            ("Gas_CT_z2", 20200219), ("Gas_CT_z2", 20200220),
            ("Gas_CT_z2", 20200221), ("Gas_CT_z2", 20200222),
            ("Gas_CT_z2", 20200223), ("Gas_CT_z2", 20200224),
            ("Gas_CT_z2", 20300101), ("Gas_CT_z2", 20300102),
            ("Gas_CT_z2", 20300103), ("Gas_CT_z2", 20300104),
            ("Gas_CT_z2", 20300105), ("Gas_CT_z2", 20300106),
            ("Gas_CT_z2", 20300107), ("Gas_CT_z2", 20300108),
            ("Gas_CT_z2", 20300109), ("Gas_CT_z2", 20300110),
            ("Gas_CT_z2", 20300111), ("Gas_CT_z2", 20300112),
            ("Gas_CT_z2", 20300113), ("Gas_CT_z2", 20300114),
            ("Gas_CT_z2", 20300115), ("Gas_CT_z2", 20300116),
            ("Gas_CT_z2", 20300117), ("Gas_CT_z2", 20300118),
            ("Gas_CT_z2", 20300119), ("Gas_CT_z2", 20300120),
            ("Gas_CT_z2", 20300121), ("Gas_CT_z2", 20300122),
            ("Gas_CT_z2", 20300123), ("Gas_CT_z2", 20300124),
            ("Gas_CT_z2", 20300201), ("Gas_CT_z2", 20300202),
            ("Gas_CT_z2", 20300203), ("Gas_CT_z2", 20300204),
            ("Gas_CT_z2", 20300205), ("Gas_CT_z2", 20300206),
            ("Gas_CT_z2", 20300207), ("Gas_CT_z2", 20300208),
            ("Gas_CT_z2", 20300209), ("Gas_CT_z2", 20300210),
            ("Gas_CT_z2", 20300211), ("Gas_CT_z2", 20300212),
            ("Gas_CT_z2", 20300213), ("Gas_CT_z2", 20300214),
            ("Gas_CT_z2", 20300215), ("Gas_CT_z2", 20300216),
            ("Gas_CT_z2", 20300217), ("Gas_CT_z2", 20300218),
            ("Gas_CT_z2", 20300219), ("Gas_CT_z2", 20300220),
            ("Gas_CT_z2", 20300221), ("Gas_CT_z2", 20300222),
            ("Gas_CT_z2", 20300223), ("Gas_CT_z2", 20300224),
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
            ("Gas_CT_New", 20300101), ("Gas_CT_New", 20300102),
            ("Gas_CT_New", 20300103), ("Gas_CT_New", 20300104),
            ("Gas_CT_New", 20300105), ("Gas_CT_New", 20300106),
            ("Gas_CT_New", 20300107), ("Gas_CT_New", 20300108),
            ("Gas_CT_New", 20300109), ("Gas_CT_New", 20300110),
            ("Gas_CT_New", 20300111), ("Gas_CT_New", 20300112),
            ("Gas_CT_New", 20300113), ("Gas_CT_New", 20300114),
            ("Gas_CT_New", 20300115), ("Gas_CT_New", 20300116),
            ("Gas_CT_New", 20300117), ("Gas_CT_New", 20300118),
            ("Gas_CT_New", 20300119), ("Gas_CT_New", 20300120),
            ("Gas_CT_New", 20300121), ("Gas_CT_New", 20300122),
            ("Gas_CT_New", 20300123), ("Gas_CT_New", 20300124),
            ("Gas_CT_New", 20300201), ("Gas_CT_New", 20300202),
            ("Gas_CT_New", 20300203), ("Gas_CT_New", 20300204),
            ("Gas_CT_New", 20300205), ("Gas_CT_New", 20300206),
            ("Gas_CT_New", 20300207), ("Gas_CT_New", 20300208),
            ("Gas_CT_New", 20300209), ("Gas_CT_New", 20300210),
            ("Gas_CT_New", 20300211), ("Gas_CT_New", 20300212),
            ("Gas_CT_New", 20300213), ("Gas_CT_New", 20300214),
            ("Gas_CT_New", 20300215), ("Gas_CT_New", 20300216),
            ("Gas_CT_New", 20300217), ("Gas_CT_New", 20300218),
            ("Gas_CT_New", 20300219), ("Gas_CT_New", 20300220),
            ("Gas_CT_New", 20300221), ("Gas_CT_New", 20300222),
            ("Gas_CT_New", 20300223), ("Gas_CT_New", 20300224),
        ])
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.
                DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_timepoints_by_project)

        # Param: unit_size_mw
        expected_unit_size = {
            "Gas_CCGT": 6, "Coal": 6, "Gas_CT": 6, "Gas_CCGT_New": 6,
            "Gas_CT_New": 6, "Gas_CCGT_z2": 6, "Coal_z2": 6, "Gas_CT_z2": 6
        }
        actual_unit_size = {
            prj: instance.unit_size_mw[prj]
            for prj in instance.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS
            }
        self.assertDictEqual(expected_unit_size,
                             actual_unit_size)

        # Param: disp_cap_commit_min_stable_level_fraction
        expected_min_stable_fraction = {
            "Gas_CCGT": 0.4, "Coal": 0.4, "Gas_CT": 0.4, "Gas_CCGT_New": 0.4,
            "Gas_CT_New": 0.4, "Gas_CCGT_z2": 0.4, "Coal_z2": 0.4,
            "Gas_CT_z2": 0.4
        }
        actual_min_stable_fraction = {
            prj: instance.disp_cap_commit_min_stable_level_fraction[prj]
            for prj in instance.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_min_stable_fraction,
                             actual_min_stable_fraction
                             )

        # Param: ramp_rate_up_frac_of_capacity
        expected_ramp_up_rate = {
            "Gas_CCGT": 0.3, "Coal": 0.2, "Gas_CT": 0.5, "Gas_CCGT_New": 0.5,
            "Gas_CT_New": 0.8, "Gas_CCGT_z2": 1, "Coal_z2": 1,
            "Gas_CT_z2": 1
        }
        actual_ramp_down_rate = {
            prj: instance.dispcapcommit_ramp_rate_up_frac_of_capacity_per_hour[
                prj]
            for prj in instance.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_ramp_up_rate,
                             actual_ramp_down_rate
                             )
        
        # Param: ramp_rate_down_frac_of_capacity
        expected_ramp_down_rate = {
            "Gas_CCGT": 0.5, "Coal": 0.3, "Gas_CT": 0.2, "Gas_CCGT_New": 0.8,
            "Gas_CT_New": 0.5, "Gas_CCGT_z2": 1, "Coal_z2": 1,
            "Gas_CT_z2": 1
        }
        actual_ramp_down_rate = {
            prj: instance.dispcapcommit_ramp_rate_down_frac_of_capacity_per_hour[
                prj]
            for prj in instance.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_ramp_down_rate,
                             actual_ramp_down_rate
                             )

if __name__ == "__main__":
    unittest.main()
