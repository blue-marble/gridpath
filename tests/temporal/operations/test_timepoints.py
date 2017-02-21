#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from importlib import import_module
import os.path
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# No prerequisite modules
NAME_OF_MODULE_BEING_TESTED = "temporal.operations.timepoints"

try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestTimepoints(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=[],
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
        add_components_and_load_data(prereq_modules=[],
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     horizon="",
                                     stage=""
                                     )

    def test_timepoints_data_load_correctly(self):
        """
        Create components; check inputs load as expected
        :return:
        """
        m, data = \
            add_components_and_load_data(prereq_modules=[],
                                         module_to_test=MODULE_BEING_TESTED,
                                         test_data_dir=TEST_DATA_DIRECTORY,
                                         horizon="",
                                         stage="")
        instance = m.create_instance(data)

        expected_tmp = \
            [20200101, 20200102, 20200103, 20200104, 20200105, 20200106,
             20200107, 20200108, 20200109, 20200110, 20200111, 20200112,
             20200113, 20200114, 20200115, 20200116, 20200117, 20200118,
             20200119, 20200120, 20200121, 20200122, 20200123, 20200124,
             20200201, 20200202, 20200203, 20200204, 20200205, 20200206,
             20200207, 20200208, 20200209, 20200210, 20200211, 20200212,
             20200213, 20200214, 20200215, 20200216, 20200217, 20200218,
             20200219, 20200220, 20200221, 20200222, 20200223, 20200224,
             20300101, 20300102, 20300103, 20300104, 20300105, 20300106,
             20300107, 20300108, 20300109, 20300110, 20300111, 20300112,
             20300113, 20300114, 20300115, 20300116, 20300117, 20300118,
             20300119, 20300120, 20300121, 20300122, 20300123, 20300124,
             20300201, 20300202, 20300203, 20300204, 20300205, 20300206,
             20300207, 20300208, 20300209, 20300210, 20300211, 20300212,
             20300213, 20300214, 20300215, 20300216, 20300217, 20300218,
             20300219, 20300220, 20300221, 20300222, 20300223, 20300224]
        actual_tmp = [tmp for tmp in instance.TIMEPOINTS]
        self.assertListEqual(expected_tmp, actual_tmp,
                             msg="TIMEPOINTS set data does not load correctly."
                             )

        expected_num_hrs_param = \
            {20200101: 1, 20200102: 1, 20200103: 1, 20200104: 1, 20200105: 1,
             20200106: 1, 20200107: 1, 20200108: 1, 20200109: 1, 20200110: 1,
             20200111: 1, 20200112: 1, 20200113: 1, 20200114: 1, 20200115: 1,
             20200116: 1, 20200117: 1, 20200118: 1, 20200119: 1, 20200120: 1,
             20200121: 1, 20200122: 1, 20200123: 1, 20200124: 1, 20200201: 1,
             20200202: 1, 20200203: 1, 20200204: 1, 20200205: 1, 20200206: 1,
             20200207: 1, 20200208: 1, 20200209: 1, 20200210: 1, 20200211: 1,
             20200212: 1, 20200213: 1, 20200214: 1, 20200215: 1, 20200216: 1,
             20200217: 1, 20200218: 1, 20200219: 1, 20200220: 1, 20200221: 1,
             20200222: 1, 20200223: 1, 20200224: 1, 20300101: 1, 20300102: 1,
             20300103: 1, 20300104: 1, 20300105: 1, 20300106: 1, 20300107: 1,
             20300108: 1, 20300109: 1, 20300110: 1, 20300111: 1, 20300112: 1,
             20300113: 1, 20300114: 1, 20300115: 1, 20300116: 1, 20300117: 1,
             20300118: 1, 20300119: 1, 20300120: 1, 20300121: 1, 20300122: 1,
             20300123: 1, 20300124: 1, 20300201: 1, 20300202: 1, 20300203: 1,
             20300204: 1, 20300205: 1, 20300206: 1, 20300207: 1, 20300208: 1,
             20300209: 1, 20300210: 1, 20300211: 1, 20300212: 1, 20300213: 1,
             20300214: 1, 20300215: 1, 20300216: 1, 20300217: 1, 20300218: 1,
             20300219: 1, 20300220: 1, 20300221: 1, 20300222: 1, 20300223: 1,
             20300224: 1}

        actual_num_hrs_param = \
            {tmp: instance.number_of_hours_in_timepoint[tmp]
             for tmp in instance.TIMEPOINTS
             }
        self.assertDictEqual(expected_num_hrs_param, actual_num_hrs_param,
                             msg="Data for param 'number_of_hours_in_timepoint'"
                                 " not loaded correctly")

if __name__ == "__main__":
    unittest.main()
