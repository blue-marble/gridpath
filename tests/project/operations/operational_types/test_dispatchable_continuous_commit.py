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
    "project.capacity.capacity", "project.fuels", "project.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.dispatchable_continuous_commit"
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


class TestDispatchableContinuousCommitOperationalType(unittest.TestCase):
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

        # Set: DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS
        expected_disp_cont_commit_gen_set = sorted([
            "Disp_Cont_Commit", "Clunky_Old_Gen"
        ])
        actual_disp_cont_commit_gen_set = sorted([
            prj for prj in instance.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS
            ])
        self.assertListEqual(expected_disp_cont_commit_gen_set,
                             actual_disp_cont_commit_gen_set)

        # Set: DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS
        expected_operational_timpoints_by_project = sorted([
            ("Disp_Cont_Commit", 20200101), ("Disp_Cont_Commit", 20200102),
            ("Disp_Cont_Commit", 20200103), ("Disp_Cont_Commit", 20200104),
            ("Disp_Cont_Commit", 20200105), ("Disp_Cont_Commit", 20200106),
            ("Disp_Cont_Commit", 20200107), ("Disp_Cont_Commit", 20200108),
            ("Disp_Cont_Commit", 20200109), ("Disp_Cont_Commit", 20200110),
            ("Disp_Cont_Commit", 20200111), ("Disp_Cont_Commit", 20200112),
            ("Disp_Cont_Commit", 20200113), ("Disp_Cont_Commit", 20200114),
            ("Disp_Cont_Commit", 20200115), ("Disp_Cont_Commit", 20200116),
            ("Disp_Cont_Commit", 20200117), ("Disp_Cont_Commit", 20200118),
            ("Disp_Cont_Commit", 20200119), ("Disp_Cont_Commit", 20200120),
            ("Disp_Cont_Commit", 20200121), ("Disp_Cont_Commit", 20200122),
            ("Disp_Cont_Commit", 20200123), ("Disp_Cont_Commit", 20200124),
            ("Disp_Cont_Commit", 20200201), ("Disp_Cont_Commit", 20200202),
            ("Disp_Cont_Commit", 20200203), ("Disp_Cont_Commit", 20200204),
            ("Disp_Cont_Commit", 20200205), ("Disp_Cont_Commit", 20200206),
            ("Disp_Cont_Commit", 20200207), ("Disp_Cont_Commit", 20200208),
            ("Disp_Cont_Commit", 20200209), ("Disp_Cont_Commit", 20200210),
            ("Disp_Cont_Commit", 20200211), ("Disp_Cont_Commit", 20200212),
            ("Disp_Cont_Commit", 20200213), ("Disp_Cont_Commit", 20200214),
            ("Disp_Cont_Commit", 20200215), ("Disp_Cont_Commit", 20200216),
            ("Disp_Cont_Commit", 20200217), ("Disp_Cont_Commit", 20200218),
            ("Disp_Cont_Commit", 20200219), ("Disp_Cont_Commit", 20200220),
            ("Disp_Cont_Commit", 20200221), ("Disp_Cont_Commit", 20200222),
            ("Disp_Cont_Commit", 20200223), ("Disp_Cont_Commit", 20200224),
            ("Disp_Cont_Commit", 20300101), ("Disp_Cont_Commit", 20300102),
            ("Disp_Cont_Commit", 20300103), ("Disp_Cont_Commit", 20300104),
            ("Disp_Cont_Commit", 20300105), ("Disp_Cont_Commit", 20300106),
            ("Disp_Cont_Commit", 20300107), ("Disp_Cont_Commit", 20300108),
            ("Disp_Cont_Commit", 20300109), ("Disp_Cont_Commit", 20300110),
            ("Disp_Cont_Commit", 20300111), ("Disp_Cont_Commit", 20300112),
            ("Disp_Cont_Commit", 20300113), ("Disp_Cont_Commit", 20300114),
            ("Disp_Cont_Commit", 20300115), ("Disp_Cont_Commit", 20300116),
            ("Disp_Cont_Commit", 20300117), ("Disp_Cont_Commit", 20300118),
            ("Disp_Cont_Commit", 20300119), ("Disp_Cont_Commit", 20300120),
            ("Disp_Cont_Commit", 20300121), ("Disp_Cont_Commit", 20300122),
            ("Disp_Cont_Commit", 20300123), ("Disp_Cont_Commit", 20300124),
            ("Disp_Cont_Commit", 20300201), ("Disp_Cont_Commit", 20300202),
            ("Disp_Cont_Commit", 20300203), ("Disp_Cont_Commit", 20300204),
            ("Disp_Cont_Commit", 20300205), ("Disp_Cont_Commit", 20300206),
            ("Disp_Cont_Commit", 20300207), ("Disp_Cont_Commit", 20300208),
            ("Disp_Cont_Commit", 20300209), ("Disp_Cont_Commit", 20300210),
            ("Disp_Cont_Commit", 20300211), ("Disp_Cont_Commit", 20300212),
            ("Disp_Cont_Commit", 20300213), ("Disp_Cont_Commit", 20300214),
            ("Disp_Cont_Commit", 20300215), ("Disp_Cont_Commit", 20300216),
            ("Disp_Cont_Commit", 20300217), ("Disp_Cont_Commit", 20300218),
            ("Disp_Cont_Commit", 20300219), ("Disp_Cont_Commit", 20300220),
            ("Disp_Cont_Commit", 20300221), ("Disp_Cont_Commit", 20300222),
            ("Disp_Cont_Commit", 20300223), ("Disp_Cont_Commit", 20300224),
            ("Clunky_Old_Gen", 20200101), ("Clunky_Old_Gen", 20200102),
            ("Clunky_Old_Gen", 20200103), ("Clunky_Old_Gen", 20200104),
            ("Clunky_Old_Gen", 20200105), ("Clunky_Old_Gen", 20200106),
            ("Clunky_Old_Gen", 20200107), ("Clunky_Old_Gen", 20200108),
            ("Clunky_Old_Gen", 20200109), ("Clunky_Old_Gen", 20200110),
            ("Clunky_Old_Gen", 20200111), ("Clunky_Old_Gen", 20200112),
            ("Clunky_Old_Gen", 20200113), ("Clunky_Old_Gen", 20200114),
            ("Clunky_Old_Gen", 20200115), ("Clunky_Old_Gen", 20200116),
            ("Clunky_Old_Gen", 20200117), ("Clunky_Old_Gen", 20200118),
            ("Clunky_Old_Gen", 20200119), ("Clunky_Old_Gen", 20200120),
            ("Clunky_Old_Gen", 20200121), ("Clunky_Old_Gen", 20200122),
            ("Clunky_Old_Gen", 20200123), ("Clunky_Old_Gen", 20200124),
            ("Clunky_Old_Gen", 20200201), ("Clunky_Old_Gen", 20200202),
            ("Clunky_Old_Gen", 20200203), ("Clunky_Old_Gen", 20200204),
            ("Clunky_Old_Gen", 20200205), ("Clunky_Old_Gen", 20200206),
            ("Clunky_Old_Gen", 20200207), ("Clunky_Old_Gen", 20200208),
            ("Clunky_Old_Gen", 20200209), ("Clunky_Old_Gen", 20200210),
            ("Clunky_Old_Gen", 20200211), ("Clunky_Old_Gen", 20200212),
            ("Clunky_Old_Gen", 20200213), ("Clunky_Old_Gen", 20200214),
            ("Clunky_Old_Gen", 20200215), ("Clunky_Old_Gen", 20200216),
            ("Clunky_Old_Gen", 20200217), ("Clunky_Old_Gen", 20200218),
            ("Clunky_Old_Gen", 20200219), ("Clunky_Old_Gen", 20200220),
            ("Clunky_Old_Gen", 20200221), ("Clunky_Old_Gen", 20200222),
            ("Clunky_Old_Gen", 20200223), ("Clunky_Old_Gen", 20200224),
            ("Clunky_Old_Gen", 20300101), ("Clunky_Old_Gen", 20300102),
            ("Clunky_Old_Gen", 20300103), ("Clunky_Old_Gen", 20300104),
            ("Clunky_Old_Gen", 20300105), ("Clunky_Old_Gen", 20300106),
            ("Clunky_Old_Gen", 20300107), ("Clunky_Old_Gen", 20300108),
            ("Clunky_Old_Gen", 20300109), ("Clunky_Old_Gen", 20300110),
            ("Clunky_Old_Gen", 20300111), ("Clunky_Old_Gen", 20300112),
            ("Clunky_Old_Gen", 20300113), ("Clunky_Old_Gen", 20300114),
            ("Clunky_Old_Gen", 20300115), ("Clunky_Old_Gen", 20300116),
            ("Clunky_Old_Gen", 20300117), ("Clunky_Old_Gen", 20300118),
            ("Clunky_Old_Gen", 20300119), ("Clunky_Old_Gen", 20300120),
            ("Clunky_Old_Gen", 20300121), ("Clunky_Old_Gen", 20300122),
            ("Clunky_Old_Gen", 20300123), ("Clunky_Old_Gen", 20300124),
            ("Clunky_Old_Gen", 20300201), ("Clunky_Old_Gen", 20300202),
            ("Clunky_Old_Gen", 20300203), ("Clunky_Old_Gen", 20300204),
            ("Clunky_Old_Gen", 20300205), ("Clunky_Old_Gen", 20300206),
            ("Clunky_Old_Gen", 20300207), ("Clunky_Old_Gen", 20300208),
            ("Clunky_Old_Gen", 20300209), ("Clunky_Old_Gen", 20300210),
            ("Clunky_Old_Gen", 20300211), ("Clunky_Old_Gen", 20300212),
            ("Clunky_Old_Gen", 20300213), ("Clunky_Old_Gen", 20300214),
            ("Clunky_Old_Gen", 20300215), ("Clunky_Old_Gen", 20300216),
            ("Clunky_Old_Gen", 20300217), ("Clunky_Old_Gen", 20300218),
            ("Clunky_Old_Gen", 20300219), ("Clunky_Old_Gen", 20300220),
            ("Clunky_Old_Gen", 20300221), ("Clunky_Old_Gen", 20300222),
            ("Clunky_Old_Gen", 20300223), ("Clunky_Old_Gen", 20300224)
        ])
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.
                DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_timepoints_by_project)

        # Param: disp_cont_commit_min_stable_level_fraction
        expected_min_stable_fraction = {"Disp_Cont_Commit": 0.4,
                                        "Clunky_Old_Gen": 0.4}
        actual_min_stable_fraction = {
            prj: instance.disp_cont_commit_min_stable_level_fraction[prj]
            for prj in instance.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS
        }
        self.assertDictEqual(expected_min_stable_fraction,
                             actual_min_stable_fraction
                             )

if __name__ == "__main__":
    unittest.main()
