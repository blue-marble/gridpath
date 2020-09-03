#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from importlib import import_module
import os.path
import pandas as pd
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


class TestPeriods(unittest.TestCase):
    """
    Unit tests for gridpath.temporal.investment.periods
    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
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
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
                                     )

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Load test data
        periods_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "periods.tab"),
                sep="\t"
            )
        timepoints_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
                sep="\t",
                usecols=["timepoint", "period", "number_of_hours_in_timepoint",
                         "timepoint_weight"]
            )

        # PERIODS set
        expected_periods = periods_df['period'].tolist()
        actual_periods = [p for p in instance.PERIODS]
        self.assertListEqual(expected_periods, actual_periods,
                             msg="PERIODS set data does not load correctly."
                             )
        # TODO: set index and convert to dict once
        # Param: discount_factor
        expected_discount_factor_param = \
            periods_df.set_index('period').to_dict()['discount_factor']
        actual_discount_factor_param = \
            {p: instance.discount_factor[p] for p in instance.PERIODS}
        self.assertDictEqual(expected_discount_factor_param,
                             actual_discount_factor_param,
                             msg="Data for param 'discount_factor' param "
                                 "not loaded correctly"
                             )
        # Param: number_years_represented
        expected_num_years_param = \
            periods_df.set_index('period').to_dict()[
                'number_years_represented'
            ]
        actual_num_years_param = \
            {p: instance.number_years_represented[p] for p in instance.PERIODS}
        self.assertDictEqual(expected_num_years_param,
                             actual_num_years_param,
                             msg="Data for param 'number_years_represented' "
                                 "param not loaded correctly"
                             )

        # Param: hours_in_full_period
        expected_hours_in_full_period = \
            periods_df.set_index('period').to_dict()[
                'hours_in_full_period'
            ]
        actual_hours_in_full_period = \
            {p: instance.hours_in_full_period[p] for p in instance.PERIODS}
        self.assertDictEqual(expected_hours_in_full_period,
                             actual_hours_in_full_period,
                             msg="Data for param 'hours_in_full_period' "
                                 "param not loaded correctly"
                             )

        # Params: period
        expected_period_param = \
            timepoints_df.set_index('timepoint').to_dict()['period']
        actual_period_param = \
            {tmp: instance.period[tmp]
             for tmp in instance.TMPS
             }

        self.assertDictEqual(expected_period_param, actual_period_param,
                             msg="Data for param 'period' not loaded correctly"
                             )

        # Set TMPS_IN_PRD
        expected_tmp_in_p = dict()
        for tmp in timepoints_df['timepoint'].tolist():
            if expected_period_param[tmp] not in expected_tmp_in_p.keys():
                expected_tmp_in_p[expected_period_param[tmp]] = [tmp]
            else:
                expected_tmp_in_p[expected_period_param[tmp]].append(tmp)

        actual_tmps_in_p = {
            p: sorted([tmp for tmp in instance.TMPS_IN_PRD[p]])
            for p in list(instance.TMPS_IN_PRD.keys())
            }
        self.assertDictEqual(expected_tmp_in_p, actual_tmps_in_p,
                             msg="TMPS_IN_PRD data do not match "
                                 "expected."
                             )

        # Param: first_period
        expected_first_period = expected_periods[0]
        actual_first_period = instance.first_period
        self.assertEqual(expected_first_period, actual_first_period)

        # Set: NOT_FIRST_PRDS
        expected_not_first_periods = expected_periods[1:]
        actual_not_first_periods = [p for p in instance.NOT_FIRST_PRDS]
        self.assertListEqual(
            expected_not_first_periods, actual_not_first_periods
        )

        # Param: prev_period
        expected_prev_periods = {
            p: expected_periods[expected_periods.index(p)-1]
            for p in expected_not_first_periods
        }
        actual_prev_periods = {p: instance.prev_period[p] for p in
                               instance.NOT_FIRST_PRDS}
        self.assertDictEqual(expected_prev_periods, actual_prev_periods)

        # Param: hours_in_subproblem_period
        timepoints_df["tot_hours"] = timepoints_df[
            "number_of_hours_in_timepoint"] * timepoints_df["timepoint_weight"]
        expected_hours_in_subproblem_period = timepoints_df.groupby(["period"])[
            "tot_hours"].sum().to_dict()

        actual_hours_in_subproblem_period = \
            {p: instance.hours_in_subproblem_period[p] for p in instance.PERIODS}
        self.assertDictEqual(expected_hours_in_subproblem_period,
                             actual_hours_in_subproblem_period,
                             msg="Data for param 'hours_in_subproblem_period' "
                                 "param not loaded correctly"
                             )


if __name__ == "__main__":
    unittest.main()
