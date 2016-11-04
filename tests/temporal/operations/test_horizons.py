#!/usr/bin/env python

from importlib import import_module
import os.path
from pyomo.environ import Param
import sys
import unittest

from tests.common_functions import add_model_components, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = ["temporal.operations.timepoints"]
NAME_OF_MODULE_BEING_TESTED = "temporal.operations.horizons"
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


class TestHorizons(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        add_model_components(prereq_modules=IMPORTED_PREREQ_MODULES,
                             module_to_test=MODULE_BEING_TESTED
                             )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY
                                     )

    def test_horizons_data_load_correctly(self):
        """
        Create components; check inputs load as expected
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY
        )
        instance = m.create_instance(data)

        # Check data are as expected
        # HORIZONS set
        expected_hrzn = [202001, 202002, 203001, 203002]
        actual_hrzn = [tmp for tmp in instance.HORIZONS]
        self.assertListEqual(expected_hrzn, actual_hrzn,
                             msg="HORIZONS set data does not load correctly."
                             )

        # Params: boundary
        expected_boundary_param = {202001: "circular", 202002: "linear",
                                   203001: "circular", 203002: "linear"}
        actual_boundary_param = \
            {h: instance.boundary[h]
             for h in instance.HORIZONS
             }
        self.assertDictEqual(expected_boundary_param, actual_boundary_param,
                             msg="Data for param 'boundary' "
                                 "not loaded correctly")

        # Params: horizon_weight
        expected_hweight_param = {202001: 1.0, 202002: 1.0,
                                  203001: 1.0, 203002: 1.0}
        actual_hweight_param = \
            {h: instance.horizon_weight[h]
             for h in instance.HORIZONS
             }
        self.assertDictEqual(expected_hweight_param, actual_hweight_param,
                             msg="Data for param 'horizon_weight'"
                                 " not loaded correctly")

        # Params: horizon
        expected_horizon_param = \
            {20200101: 202001, 20200102: 202001, 20200103: 202001,
             20200104: 202001, 20200105: 202001, 20200106: 202001,
             20200107: 202001, 20200108: 202001, 20200109: 202001,
             20200110: 202001, 20200111: 202001, 20200112: 202001,
             20200113: 202001, 20200114: 202001, 20200115: 202001,
             20200116: 202001, 20200117: 202001, 20200118: 202001,
             20200119: 202001, 20200120: 202001, 20200121: 202001,
             20200122: 202001, 20200123: 202001, 20200124: 202001,
             20200201: 202002, 20200202: 202002, 20200203: 202002,
             20200204: 202002, 20200205: 202002, 20200206: 202002,
             20200207: 202002, 20200208: 202002, 20200209: 202002,
             20200210: 202002, 20200211: 202002, 20200212: 202002,
             20200213: 202002, 20200214: 202002, 20200215: 202002,
             20200216: 202002, 20200217: 202002, 20200218: 202002,
             20200219: 202002, 20200220: 202002, 20200221: 202002,
             20200222: 202002, 20200223: 202002, 20200224: 202002,
             20300101: 203001, 20300102: 203001, 20300103: 203001,
             20300104: 203001, 20300105: 203001, 20300106: 203001,
             20300107: 203001, 20300108: 203001, 20300109: 203001,
             20300110: 203001, 20300111: 203001, 20300112: 203001,
             20300113: 203001, 20300114: 203001, 20300115: 203001,
             20300116: 203001, 20300117: 203001, 20300118: 203001,
             20300119: 203001, 20300120: 203001, 20300121: 203001,
             20300122: 203001, 20300123: 203001, 20300124: 203001,
             20300201: 203002, 20300202: 203002, 20300203: 203002,
             20300204: 203002, 20300205: 203002, 20300206: 203002,
             20300207: 203002, 20300208: 203002, 20300209: 203002,
             20300210: 203002, 20300211: 203002, 20300212: 203002,
             20300213: 203002, 20300214: 203002, 20300215: 203002,
             20300216: 203002, 20300217: 203002, 20300218: 203002,
             20300219: 203002, 20300220: 203002, 20300221: 203002,
             20300222: 203002, 20300223: 203002, 20300224: 203002}
        actual_horizon_param = \
            {tmp: instance.horizon[tmp]
             for tmp in instance.TIMEPOINTS
             }

        self.assertDictEqual(expected_horizon_param, actual_horizon_param,
                             msg="Data for param 'horizon' not loaded correctly"
                             )

    def test_derived_data(self):
        """
        Check the in-model parameter calculations
        :return:
        """

        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY
        )
        instance = m.create_instance(data)

        # Set TIMEPOINTS_ON_HORIZON
        expected_tmps_on_horizon = {
            202001:
                [20200101, 20200102, 20200103, 20200104, 20200105, 20200106,
                 20200107, 20200108, 20200109, 20200110, 20200111, 20200112,
                 20200113, 20200114, 20200115, 20200116, 20200117, 20200118,
                 20200119, 20200120, 20200121, 20200122, 20200123, 20200124],
            202002:
                [20200201, 20200202, 20200203, 20200204, 20200205, 20200206,
                 20200207, 20200208, 20200209, 20200210, 20200211, 20200212,
                 20200213, 20200214, 20200215, 20200216, 20200217, 20200218,
                 20200219, 20200220, 20200221, 20200222, 20200223, 20200224],
            203001:
                [20300101, 20300102, 20300103, 20300104, 20300105, 20300106,
                 20300107, 20300108, 20300109, 20300110, 20300111, 20300112,
                 20300113, 20300114, 20300115, 20300116, 20300117, 20300118,
                 20300119, 20300120, 20300121, 20300122, 20300123, 20300124],
            203002:
                [20300201, 20300202, 20300203, 20300204, 20300205, 20300206,
                 20300207, 20300208, 20300209, 20300210, 20300211, 20300212,
                 20300213, 20300214, 20300215, 20300216, 20300217, 20300218,
                 20300219, 20300220, 20300221, 20300222, 20300223, 20300224]
             }
        actual_tmps_on_horizon = {
            h: [tmp for tmp in instance.TIMEPOINTS_ON_HORIZON[h]]
            for h in instance.TIMEPOINTS_ON_HORIZON.keys()
            }
        self.assertDictEqual(expected_tmps_on_horizon, actual_tmps_on_horizon,
                             msg="HORIZONS_ON_TIMEPOINT data do not match "
                                 "expected."
                             )

        # Param: first_horizon_timepoint
        expected_first_horizon_timepoint = {
            202001: 20200101, 202002:20200201,
            203001: 20300101, 203002: 20300201
        }
        actual_first_horizon_timepoint = {
            h: instance.first_horizon_timepoint[h] for h in instance.HORIZONS
        }
        self.assertDictEqual(expected_first_horizon_timepoint,
                             actual_first_horizon_timepoint,
                             msg="Data for param first_horizon_timepoint do "
                                 "not match expected.")

        # Param: last_horizon_timepoint
        expected_last_horizon_timepoint = {
            202001: 20200124, 202002:20200224,
            203001: 20300124, 203002: 20300224
        }
        actual_last_horizon_timepoint = {
            h: instance.last_horizon_timepoint[h] for h in instance.HORIZONS
        }
        self.assertDictEqual(expected_last_horizon_timepoint,
                             actual_last_horizon_timepoint,
                             msg="Data for param last_horizon_timepoint do "
                                 "not match expected.")

        # Param: previous_timepoint
        # Testing for both horizons that 'circular' and 'linear'
        expected_prev_tmp = {
            20200101: 20200124, 20200102: 20200101, 20200103: 20200102,
            20200104: 20200103, 20200105: 20200104, 20200106: 20200105,
            20200107: 20200106, 20200108: 20200107, 20200109: 20200108,
            20200110: 20200109, 20200111: 20200110, 20200112: 20200111,
            20200113: 20200112, 20200114: 20200113, 20200115: 20200114,
            20200116: 20200115, 20200117: 20200116, 20200118: 20200117,
            20200119: 20200118, 20200120: 20200119, 20200121: 20200120,
            20200122: 20200121, 20200123: 20200122, 20200124: 20200123,
            20200201: None, 20200202: 20200201, 20200203: 20200202,
            20200204: 20200203, 20200205: 20200204, 20200206: 20200205,
            20200207: 20200206, 20200208: 20200207, 20200209: 20200208,
            20200210: 20200209, 20200211: 20200210, 20200212: 20200211,
            20200213: 20200212, 20200214: 20200213, 20200215: 20200214,
            20200216: 20200215, 20200217: 20200216, 20200218: 20200217,
            20200219: 20200218, 20200220: 20200219, 20200221: 20200220,
            20200222: 20200221, 20200223: 20200222, 20200224: 20200223,
            20300101: 20300124, 20300102: 20300101, 20300103: 20300102,
            20300104: 20300103, 20300105: 20300104, 20300106: 20300105,
            20300107: 20300106, 20300108: 20300107, 20300109: 20300108,
            20300110: 20300109, 20300111: 20300110, 20300112: 20300111,
            20300113: 20300112, 20300114: 20300113, 20300115: 20300114,
            20300116: 20300115, 20300117: 20300116, 20300118: 20300117,
            20300119: 20300118, 20300120: 20300119, 20300121: 20300120,
            20300122: 20300121, 20300123: 20300122, 20300124: 20300123,
            20300201: None, 20300202: 20300201, 20300203: 20300202,
            20300204: 20300203, 20300205: 20300204, 20300206: 20300205,
            20300207: 20300206, 20300208: 20300207, 20300209: 20300208,
            20300210: 20300209, 20300211: 20300210, 20300212: 20300211,
            20300213: 20300212, 20300214: 20300213, 20300215: 20300214,
            20300216: 20300215, 20300217: 20300216, 20300218: 20300217,
            20300219: 20300218, 20300220: 20300219, 20300221: 20300220,
            20300222: 20300221, 20300223: 20300222, 20300224: 20300223
        }
        actual_prev_tmp = {
            tmp: instance.previous_timepoint[tmp] for tmp in instance.TIMEPOINTS
        }
        self.assertDictEqual(expected_prev_tmp,
                             actual_prev_tmp,
                             msg="Data for param previous_timepoint do "
                                 "not match expected.")

if __name__ == "__main__":
    unittest.main()

