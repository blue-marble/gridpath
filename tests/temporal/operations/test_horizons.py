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
NAME_OF_MODULE_BEING_TESTED = "temporal.operations.horizons"
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


class TestHorizons(unittest.TestCase):
    """

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
        horizons_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "horizons.tab"),
                sep="\t"
            )
        timepoints_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
                sep="\t", usecols=['TIMEPOINTS', 'horizon']
            )

        # Check data are as expected
        # HORIZONS set
        expected_hrzn = horizons_df['HORIZONS'].tolist()
        actual_hrzn = [tmp for tmp in instance.HORIZONS]
        self.assertListEqual(expected_hrzn, actual_hrzn,
                             msg="HORIZONS set data does not load correctly."
                             )

        # Params: boundary
        expected_boundary_param = \
            horizons_df.set_index('HORIZONS').to_dict()['boundary']
        actual_boundary_param = \
            {h: instance.boundary[h]
             for h in instance.HORIZONS
             }
        self.assertDictEqual(expected_boundary_param, actual_boundary_param,
                             msg="Data for param 'boundary' "
                                 "not loaded correctly")

        # Params: horizon_weight
        expected_hweight_param = \
            horizons_df.set_index('HORIZONS').to_dict()['horizon_weight']
        actual_hweight_param = \
            {h: instance.horizon_weight[h]
             for h in instance.HORIZONS
             }
        self.assertDictEqual(expected_hweight_param, actual_hweight_param,
                             msg="Data for param 'horizon_weight'"
                                 " not loaded correctly")

        # Params: horizon
        expected_horizon_param = \
            timepoints_df.set_index('TIMEPOINTS').to_dict()['horizon']
        actual_horizon_param = \
            {tmp: instance.horizon[tmp]
             for tmp in instance.TIMEPOINTS
             }

        self.assertDictEqual(
            expected_horizon_param, actual_horizon_param,
            msg="Data for param 'horizon' not loaded correctly"
        )

        # Set TIMEPOINTS_ON_HORIZON
        expected_tmps_on_horizon = dict()
        for tmp in expected_horizon_param:
            if expected_horizon_param[tmp] \
                    not in expected_tmps_on_horizon.keys():
                expected_tmps_on_horizon[expected_horizon_param[tmp]] = [tmp]
            else:
                expected_tmps_on_horizon[expected_horizon_param[tmp]].append(
                    tmp
                )

        actual_tmps_on_horizon = {
            h: [tmp for tmp in instance.TIMEPOINTS_ON_HORIZON[h]]
            for h in list(instance.TIMEPOINTS_ON_HORIZON.keys())
            }
        self.assertDictEqual(expected_tmps_on_horizon, actual_tmps_on_horizon,
                             msg="HORIZONS_ON_TIMEPOINT data do not match "
                                 "expected."
                             )

        # Param: first_horizon_timepoint
        expected_first_horizon_timepoint = {
            h: expected_tmps_on_horizon[h][0] for h in expected_hrzn
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
            h: expected_tmps_on_horizon[h][-1] for h in expected_hrzn
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
        timepoints_list = timepoints_df['TIMEPOINTS'].tolist()
        expected_prev_tmp = dict()
        for tmp in timepoints_list:
            if tmp == \
                    expected_first_horizon_timepoint[
                        expected_horizon_param[tmp]
                    ]:
                if expected_boundary_param[expected_horizon_param[tmp]] == \
                        'circular':
                    expected_prev_tmp[tmp] = \
                        expected_last_horizon_timepoint[
                            expected_horizon_param[tmp]
                        ]
                elif expected_boundary_param[expected_horizon_param[tmp]] == \
                        'linear':
                    expected_prev_tmp[tmp] = None
                else:
                    raise(IOError, "Test data specifies horizon boundary "
                                   "different from allowed values of "
                                   "'circular' and 'linear'")
            else:
                expected_prev_tmp[tmp] = \
                    timepoints_list[timepoints_list.index(tmp)-1]

        actual_prev_tmp = {
            tmp: instance.previous_timepoint[tmp]
            for tmp in instance.TIMEPOINTS
        }
        self.assertDictEqual(expected_prev_tmp,
                             actual_prev_tmp,
                             msg="Data for param previous_timepoint do "
                                 "not match expected.")


if __name__ == "__main__":
    unittest.main()
