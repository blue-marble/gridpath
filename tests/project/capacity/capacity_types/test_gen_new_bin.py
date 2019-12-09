#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function
from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import pandas as pd
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
    "project.capacity.capacity_types.gen_new_bin"
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


class TestNewBinaryBuildGenerator(unittest.TestCase):
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
                              subproblem="",
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
                                     subproblem="",
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
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: NEW_BINARY_BUILD_GENERATOR_VINTAGES
        expected_gen_vintage_set = sorted([
            ("Gas_CCGT_New_Binary", 2020),
            ("Gas_CCGT_New_Binary", 2030)
        ])
        actual_gen_vintage_set = sorted(
            [(prj, period)
             for (prj, period) in instance.NEW_BINARY_BUILD_GENERATOR_VINTAGES
             ]
        )
        self.assertListEqual(expected_gen_vintage_set, actual_gen_vintage_set)

        # Params: lifetime_yrs_by_new_binary_build_vintage
        expected_lifetime = OrderedDict(
            sorted(
                {("Gas_CCGT_New_Binary", 2020): 30,
                 ("Gas_CCGT_New_Binary", 2030): 30}.items()
            )
        )
        actual_lifetime = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.lifetime_yrs_by_new_binary_build_vintage[prj, vintage]
                 for (prj, vintage) in instance.NEW_BINARY_BUILD_GENERATOR_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: new_binary_build_annualized_real_cost_per_mw_yr
        expected_cost = OrderedDict(
            sorted(
                {("Gas_CCGT_New_Binary", 2020): 200000,
                 ("Gas_CCGT_New_Binary", 2030): 200000}.items()
            )
        )
        actual_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_binary_build_annualized_real_cost_per_mw_yr[prj, vintage]
                 for (prj, vintage) in instance.NEW_BINARY_BUILD_GENERATOR_VINTAGES
                 }.items()
            )
        )
        self.assertDictEqual(expected_cost, actual_cost)

    def test_derived_data(self):
        """
        Calculations
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE
        expected_periods_by_gen_vintage = {
            ("Gas_CCGT_New_Binary", 2020): [2020, 2030],
            ("Gas_CCGT_New_Binary", 2030): [2030]
        }
        actual_periods_by_gen_vintage = {
            (prj, vintage): [period for period in
                instance.
                    OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE[
                    prj, vintage]]
            for (prj, vintage) in
                instance.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE
        }
        self.assertDictEqual(expected_periods_by_gen_vintage,
                             actual_periods_by_gen_vintage)

        # Set: NEW_BINARY_BUILD_GENERATOR_OPERATIONAL_PERIODS
        expected_gen_op_periods = [
            ("Gas_CCGT_New_Binary", 2020),
            ("Gas_CCGT_New_Binary", 2030)
        ]
        actual_gen_op_periods = sorted([
            (prj, period) for (prj, period) in
            instance.NEW_BINARY_BUILD_GENERATOR_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_gen_op_periods, actual_gen_op_periods)

        # Set: NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD
        expected_gen_vintage_op_in_period = {
            2020: [("Gas_CCGT_New_Binary", 2020)],
            2030: [("Gas_CCGT_New_Binary", 2020), ("Gas_CCGT_New_Binary", 2030)]
        }
        actual_gen_vintage_op_in_period = {
            p: [(g, v) for (g, v) in
                sorted(instance.NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p])
                ] for p in sorted(instance.PERIODS)
        }
        self.assertDictEqual(expected_gen_vintage_op_in_period,
                             actual_gen_vintage_op_in_period)

    def test_input_validations(self):
        cost_df_columns = ["project", "period", "lifetime_yrs",
            "annualized_real_cost_per_kw_yr"]
        bld_size_df_columns = ["project", "binary_build_size_mw"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"cost_df": pd.DataFrame(
                    columns=cost_df_columns,
                    data=[["gas_ct", 2018, 20, 100],
                          ["gas_ct", 2022, 20, 120]]),
                "bld_size_df": pd.DataFrame(
                    columns=bld_size_df_columns,
                    data=[["gas_ct", 1000]]),
                "prj_periods": [("gas_ct", 2018), ("gas_ct", 2022)],
                "project_error": [],
                "cost_error": []
                },
            # Make sure missing bld size or cost is detected
            2: {"cost_df": pd.DataFrame(
                    columns=cost_df_columns,
                    data=[["gas_ct", 2018, 20, 100]]),
                "bld_size_df": pd.DataFrame(
                    columns=bld_size_df_columns,
                    data=[]),
                "prj_periods": [("gas_ct", 2018), ("gas_ct", 2022)],
                "project_error": ["Missing build size inputs for project 'gas_ct'"],
                "cost_error": ["Missing cost inputs for project 'gas_ct', period '2022'"]
                }
        }

        for test_case in test_cases.keys():
            projects = [p[0] for p in test_cases[test_case]["prj_periods"]]
            bld_size_projects = test_cases[test_case]["bld_size_df"]["project"]

            expected_list = test_cases[test_case]["project_error"]
            actual_list = MODULE_BEING_TESTED.validate_projects(
                list1=projects,
                list2=bld_size_projects
            )
            self.assertListEqual(expected_list, actual_list)

            expected_list = test_cases[test_case]["cost_error"]
            actual_list = MODULE_BEING_TESTED.validate_costs(
                cost_df=test_cases[test_case]["cost_df"],
                prj_periods=test_cases[test_case]["prj_periods"]
            )
            self.assertListEqual(expected_list, actual_list)


if __name__ == "__main__":
    unittest.main()
