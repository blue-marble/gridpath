#!/usr/bin/env python

from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = ["temporal.operations.timepoints"]
NAME_OF_MODULE_BEING_TESTED = "temporal.investment.periods"
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


class TestPeriods(unittest.TestCase):
    """
    Unit tests for modules.temporal.investment.periods
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

    def test_horizons_data_load_correctly(self):
        """
        Create components; check inputs load as expected
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

        expected_periods = [2020, 2030]
        actual_periods = [p for p in instance.PERIODS]
        self.assertListEqual(expected_periods, actual_periods,
                             msg="PERIODS set data does not load correctly."
                             )

        expected_discount_factor_param = {2020: 1, 2030: 1}
        actual_discount_factor_param = \
            {p: instance.discount_factor[p] for p in instance.PERIODS}
        self.assertDictEqual(expected_discount_factor_param,
                             actual_discount_factor_param,
                             msg="Data for param 'discount_factor' param "
                                 "not loaded correctly"
                             )

        expected_num_years_param = {2020: 10, 2030: 10}
        actual_num_years_param = \
            {p: instance.number_years_represented[p] for p in instance.PERIODS}
        self.assertDictEqual(expected_num_years_param,
                             actual_num_years_param,
                             msg="Data for param 'number_years_represented' "
                                 "param not loaded correctly"
                             )

        # Params: period
        expected_period_param = \
            {20200101: 2020, 20200102: 2020, 20200103: 2020,
             20200104: 2020, 20200105: 2020, 20200106: 2020,
             20200107: 2020, 20200108: 2020, 20200109: 2020,
             20200110: 2020, 20200111: 2020, 20200112: 2020,
             20200113: 2020, 20200114: 2020, 20200115: 2020,
             20200116: 2020, 20200117: 2020, 20200118: 2020,
             20200119: 2020, 20200120: 2020, 20200121: 2020,
             20200122: 2020, 20200123: 2020, 20200124: 2020,
             20200201: 2020, 20200202: 2020, 20200203: 2020,
             20200204: 2020, 20200205: 2020, 20200206: 2020,
             20200207: 2020, 20200208: 2020, 20200209: 2020,
             20200210: 2020, 20200211: 2020, 20200212: 2020,
             20200213: 2020, 20200214: 2020, 20200215: 2020,
             20200216: 2020, 20200217: 2020, 20200218: 2020,
             20200219: 2020, 20200220: 2020, 20200221: 2020,
             20200222: 2020, 20200223: 2020, 20200224: 2020,
             20300101: 2030, 20300102: 2030, 20300103: 2030,
             20300104: 2030, 20300105: 2030, 20300106: 2030,
             20300107: 2030, 20300108: 2030, 20300109: 2030,
             20300110: 2030, 20300111: 2030, 20300112: 2030,
             20300113: 2030, 20300114: 2030, 20300115: 2030,
             20300116: 2030, 20300117: 2030, 20300118: 2030,
             20300119: 2030, 20300120: 2030, 20300121: 2030,
             20300122: 2030, 20300123: 2030, 20300124: 2030,
             20300201: 2030, 20300202: 2030, 20300203: 2030,
             20300204: 2030, 20300205: 2030, 20300206: 2030,
             20300207: 2030, 20300208: 2030, 20300209: 2030,
             20300210: 2030, 20300211: 2030, 20300212: 2030,
             20300213: 2030, 20300214: 2030, 20300215: 2030,
             20300216: 2030, 20300217: 2030, 20300218: 2030,
             20300219: 2030, 20300220: 2030, 20300221: 2030,
             20300222: 2030, 20300223: 2030, 20300224: 2030}
        actual_period_param = \
            {tmp: instance.period[tmp]
             for tmp in instance.TIMEPOINTS
             }

        self.assertDictEqual(expected_period_param, actual_period_param,
                             msg="Data for param 'period' not loaded correctly"
                             )

    def test_derived_data(self):
        """
        Check the in-model parameter calculations
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

        # Set TIMEPOINTS_IN_PERIODS
        expected_tmp_in_p = \
            {2020:
                [20200101, 20200102, 20200103, 20200104, 20200105, 20200106,
                 20200107, 20200108, 20200109, 20200110, 20200111, 20200112,
                 20200113, 20200114, 20200115, 20200116, 20200117, 20200118,
                 20200119, 20200120, 20200121, 20200122, 20200123, 20200124,
                 20200201, 20200202, 20200203, 20200204, 20200205, 20200206,
                 20200207, 20200208, 20200209, 20200210, 20200211, 20200212,
                 20200213, 20200214, 20200215, 20200216, 20200217, 20200218,
                 20200219, 20200220, 20200221, 20200222, 20200223, 20200224],
             2030:
                [20300101, 20300102, 20300103, 20300104, 20300105, 20300106,
                 20300107, 20300108, 20300109, 20300110, 20300111, 20300112,
                 20300113, 20300114, 20300115, 20300116, 20300117, 20300118,
                 20300119, 20300120, 20300121, 20300122, 20300123, 20300124,
                 20300201, 20300202, 20300203, 20300204, 20300205, 20300206,
                 20300207, 20300208, 20300209, 20300210, 20300211, 20300212,
                 20300213, 20300214, 20300215, 20300216, 20300217, 20300218,
                 20300219, 20300220, 20300221, 20300222, 20300223, 20300224]
            }
        actual_tmps_in_p = {
            p: sorted([tmp for tmp in instance.TIMEPOINTS_IN_PERIOD[p]])
            for p in instance.TIMEPOINTS_IN_PERIOD.keys()
            }
        self.assertDictEqual(expected_tmp_in_p, actual_tmps_in_p,
                             msg="TIMEPOINTS_IN_PERIOD data do not match "
                                 "expected."
                             )


if __name__ == "__main__":
    unittest.main()

