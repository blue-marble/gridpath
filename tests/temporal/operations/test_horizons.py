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

        # TODO: add test data with more horizon types

        # Load test data
        balancing_type_horizons_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "horizons.tab"),
                sep="\t"
            )

        timepoints_on_balancing_type_horizon_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs",
                             "horizon_timepoints.tab"),
                sep="\t"
            )

        # Check data are as expected
        # BALANCING_TYPE_HORIZONS set
        expected_balancing_type_horizons = [
            tuple(x) for x in balancing_type_horizons_df[
                ['balancing_type', 'horizon']
            ].values
        ]
        actual_balancing_type_horizons = [
            (_type, horizon)
            for (_type, horizon) in instance.BALANCING_TYPE_HORIZONS
        ]
        self.assertListEqual(expected_balancing_type_horizons, actual_balancing_type_horizons,
                             msg="HORIZONS set data does not load correctly."
                             )

        # Params: boundary
        expected_boundary_param = \
            balancing_type_horizons_df.set_index(
                ['balancing_type', 'horizon']
            ).to_dict()['boundary']
        actual_boundary_param = \
            {(t, h): instance.boundary[t, h]
             for (t, h) in instance.BALANCING_TYPE_HORIZONS
             }
        self.assertDictEqual(expected_boundary_param, actual_boundary_param,
                             msg="Data for param 'boundary' "
                                 "not loaded correctly")

        # BALANCING_TYPES set
        expected_balancing_types = \
            list(balancing_type_horizons_df.balancing_type.unique())
        actual_balancing_types = list(instance.BALANCING_TYPES)
        self.assertListEqual(expected_balancing_types, actual_balancing_types)

        # HORIZONS_BY_BALANCING_TYPE set
        expected_horizon_by_balancing_type = \
            {balancing_type: horizons["horizon"].tolist()
             for balancing_type, horizons
             in balancing_type_horizons_df.groupby("balancing_type")}
        actual_horizon_by_balancing_type = {
            balancing_type: [
                horizon for horizon
                in list(instance.HORIZONS_BY_BALANCING_TYPE[balancing_type])
            ] for balancing_type in instance.HORIZONS_BY_BALANCING_TYPE.keys()
        }
        self.assertDictEqual(expected_horizon_by_balancing_type,
                             actual_horizon_by_balancing_type)

        # Set TIMEPOINTS_ON_BALANCING_TYPE_HORIZON
        expected_tmps_on_balancing_type_horizon = {
            (balancing_type, horizon): timepoints["timepoint"].tolist()
            for ((balancing_type, horizon), timepoints)
            in timepoints_on_balancing_type_horizon_df.groupby(
                ["balancing_type", "horizon"]
            )
        }

        actual_tmps_on_balancing_type_horizon = {
            (t, h): [tmp for tmp in
                     instance.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[t, h]]
            for (t, h) in list(instance.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON.keys())
            }

        self.assertDictEqual(expected_tmps_on_balancing_type_horizon,
                             actual_tmps_on_balancing_type_horizon,
                             msg="TIMEPOINTS_ON_BALANCING_TYPE_HORIZON data do "
                                 "not match expected."
                             )

        # Param: horizon
        expected_horizon_by_tmp_type = {
            (tmp, balancing_type): horizon for tmp, balancing_type, horizon
            in zip(
                timepoints_on_balancing_type_horizon_df.timepoint,
                timepoints_on_balancing_type_horizon_df.balancing_type,
                timepoints_on_balancing_type_horizon_df.horizon
            )
        }
        actual_horizon_by_tmp_type = {
            (tmp, _type): instance.horizon[tmp, _type]
            for tmp in instance.TIMEPOINTS for _type in instance.BALANCING_TYPES
        }
        self.assertDictEqual(expected_horizon_by_tmp_type,
                             actual_horizon_by_tmp_type)

        # Param: first_horizon_timepoint
        expected_first_horizon_timepoint = {
            (t, h): expected_tmps_on_balancing_type_horizon[t, h][0]
            for (t, h) in expected_balancing_type_horizons
        }
        actual_first_horizon_timepoint = {
            (t, h): instance.first_horizon_timepoint[t, h]
            for (t, h) in instance.BALANCING_TYPE_HORIZONS
        }
        self.assertDictEqual(expected_first_horizon_timepoint,
                             actual_first_horizon_timepoint,
                             msg="Data for param "
                                 "first_horizon_timepoint do "
                                 "not match expected.")

        # Param: last_horizon_timepoint
        expected_last_horizon_timepoint = {
            (t, h): expected_tmps_on_balancing_type_horizon[t, h][-1]
            for (t, h) in expected_balancing_type_horizons
        }
        actual_last_horizon_timepoint = {
            (t, h): instance.last_horizon_timepoint[t, h]
            for (t, h) in instance.BALANCING_TYPE_HORIZONS
        }
        self.assertDictEqual(expected_last_horizon_timepoint,
                             actual_last_horizon_timepoint,
                             msg="Data for param "
                                 "last_horizon_timepoint do "
                                 "not match expected.")

        # Param: previous_timepoint
        # Testing for both horizons that 'circular' and 'linear'
        # TODO: should we have the actual previous timepoints in a data file
        #  somewhere as opposed to figuring it out here
        expected_prev_tmp = dict()
        prev_tmp = None
        for (balancing_type, horizon, tmp) \
            in [tuple(row) for row in
                timepoints_on_balancing_type_horizon_df.values]:
            if tmp == expected_first_horizon_timepoint[
                    balancing_type, horizon]:
                if expected_boundary_param[balancing_type, horizon] == \
                        'circular':
                    expected_prev_tmp[tmp, balancing_type] = \
                        expected_last_horizon_timepoint[
                            balancing_type, horizon]
                elif expected_boundary_param[balancing_type, horizon] == \
                        'linear':
                    expected_prev_tmp[tmp, balancing_type] = None
                else:
                    raise(ValueError,
                          "Test data specifies horizon boundary different "
                          "from allowed values of 'circular' and 'linear'")
            else:
                expected_prev_tmp[tmp, balancing_type] = prev_tmp
            prev_tmp = tmp

        actual_prev_tmp = {
            (tmp, balancing_type): instance.previous_timepoint[tmp, balancing_type]
            for tmp in instance.TIMEPOINTS
            for balancing_type in instance.BALANCING_TYPES
        }

        self.assertDictEqual(expected_prev_tmp,
                             actual_prev_tmp,
                             msg="Data for param previous_timepoint do "
                                 "not match expected.")

        # Param: next_timepoint
        # Testing for both horizons that 'circular' and 'linear'
        expected_next_tmp = dict()
        prev_tmp = None
        for (balancing_type, horizon, tmp) \
            in [tuple(row) for row in
                timepoints_on_balancing_type_horizon_df.values]:
            if prev_tmp is None:
                if expected_boundary_param[balancing_type, horizon] == \
                        'circular':
                    expected_next_tmp[expected_last_horizon_timepoint[
                        balancing_type, horizon], balancing_type
                    ] = \
                        expected_first_horizon_timepoint[
                            balancing_type, horizon]
                elif expected_boundary_param[balancing_type, horizon] == \
                        'linear':
                    expected_next_tmp[expected_last_horizon_timepoint[
                        balancing_type, horizon], balancing_type] = None
                else:
                    raise(ValueError,
                          "Test data specifies horizon boundary different "
                          "from allowed values of 'circular' and 'linear'")
            else:
                expected_next_tmp[prev_tmp, balancing_type] = tmp
            # If we have reached the last horizon timepoint, set the
            # previous timepoint to None (to enter the boundary logic above)
            if tmp == expected_last_horizon_timepoint[
                        balancing_type, horizon]:
                prev_tmp = None
            else:
                prev_tmp = tmp

        expected_next_tmp_ordered = OrderedDict(sorted(
            expected_next_tmp.items()))

        actual_next_tmp = {
            (tmp, balancing_type): instance.next_timepoint[tmp, balancing_type]
            for tmp in instance.TIMEPOINTS
            for balancing_type in instance.BALANCING_TYPES
        }
        actual_next_tmp_ordered = OrderedDict(sorted(
            actual_next_tmp.items()))

        self.assertDictEqual(expected_next_tmp_ordered,
                             actual_next_tmp_ordered,
                             msg="Data for param next_timepoint do not match "
                                 "expected.")


if __name__ == "__main__":
    unittest.main()
