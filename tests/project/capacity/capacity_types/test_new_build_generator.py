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
    "temporal.investment.periods", "geography.load_zones", "project"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.capacity.capacity_types.new_build_generator"
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


class TestNewBuildGenerator(unittest.TestCase):
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

        # Set: NEW_BUILD_GENERATOR_VINTAGES
        expected_gen_vintage_set = sorted([
            ("Gas_CCGT_New", 2020), ("Gas_CCGT_New", 2030),
            ("Gas_CT_New", 2030)
        ])
        actual_gen_vintage_set = sorted(
            [(prj, period)
             for (prj, period) in instance.NEW_BUILD_GENERATOR_VINTAGES
             ]
        )
        self.assertListEqual(expected_gen_vintage_set, actual_gen_vintage_set)

        # Params: lifetime_yrs_by_new_build_vintage
        expected_lifetime = OrderedDict(
            sorted(
                {("Gas_CCGT_New", 2020): 30, ("Gas_CCGT_New", 2030): 30,
                 ("Gas_CT_New", 2030): 30}.items()
            )
        )
        actual_lifetime = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.lifetime_yrs_by_new_build_vintage[prj, vintage]
                 for (prj, vintage) in instance.NEW_BUILD_GENERATOR_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: annualized_real_cost_per_mw_yr
        expected_cost = OrderedDict(
            sorted(
                {("Gas_CCGT_New", 2020): 200000,
                 ("Gas_CCGT_New", 2030): 180000,
                 ("Gas_CT_New", 2030): 140000}.items()
            )
        )
        actual_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.annualized_real_cost_per_mw_yr[prj, vintage]
                 for (prj, vintage) in instance.NEW_BUILD_GENERATOR_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_cost, actual_cost)

        # Set: NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT
        expected_gen_vintage_min_set = sorted([
            ("Gas_CT_New", 2030)
        ])
        actual_gen_vintage_min_set = sorted(
            [(prj, period)
             for (prj, period)
             in instance.NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_gen_vintage_min_set,
                             actual_gen_vintage_min_set)

        # Params: annualized_real_cost_per_mw_yr
        expected_min_new_mw = OrderedDict(
            sorted(
                {("Gas_CT_New", 2030): 10}.items()
            )
        )
        actual_min_new_mw = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.min_cumulative_new_build_mw[prj, vintage]
                 for (prj, vintage)
                 in instance.NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_new_mw, actual_min_new_mw)

        # Set: NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT
        expected_gen_vintage_max_set = sorted([
            ("Gas_CCGT_New", 2020), ("Gas_CCGT_New", 2030)
        ])
        actual_gen_vintage_max_set = sorted(
            [(prj, period)
             for (prj, period)
             in instance.NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_gen_vintage_max_set,
                             actual_gen_vintage_max_set)

        # Params: annualized_real_cost_per_mw_yr
        expected_max_new_mw = OrderedDict(
            sorted(
                {("Gas_CCGT_New", 2020): 20,
                 ("Gas_CCGT_New", 2030): 20}.items()
            )
        )
        actual_max_new_mw = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.max_cumulative_new_build_mw[prj, vintage]
                 for (prj, vintage)
                 in instance.NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_new_mw, actual_max_new_mw)

    def test_derived_data(self):
        """
        Calculations
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

        # Set: OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE
        expected_periods_by_gen_vintage = {
            ("Gas_CCGT_New", 2020): [2020, 2030],
            ("Gas_CCGT_New", 2030): [2030],
            ("Gas_CT_New", 2030): [2030]
        }
        actual_periods_by_gen_vintage = {
            (prj, vintage): [period for period in
                instance.
                    OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE[
                    prj, vintage]]
            for (prj, vintage) in
                instance.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE
        }
        self.assertDictEqual(expected_periods_by_gen_vintage,
                             actual_periods_by_gen_vintage)

        # Set: NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS
        expected_gen_op_periods = [
            ("Gas_CCGT_New", 2020), ("Gas_CCGT_New", 2030), ("Gas_CT_New", 2030)
        ]
        actual_gen_op_periods = [
            (prj, period) for (prj, period) in
            instance.NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS
        ]
        self.assertListEqual(expected_gen_op_periods, actual_gen_op_periods)

        # Set: NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD
        expected_gen_vintage_op_in_period = {
            2020: [("Gas_CCGT_New", 2020)],
            2030: [("Gas_CCGT_New", 2020), ("Gas_CT_New", 2030),
                   ("Gas_CCGT_New", 2030)]
        }
        actual_gen_vintage_op_in_period = {
            p: [(g, v) for (g, v) in
                instance.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                ] for p in instance.PERIODS
        }
        self.assertDictEqual(expected_gen_vintage_op_in_period,
                             actual_gen_vintage_op_in_period)


if __name__ == "__main__":
    unittest.main()
