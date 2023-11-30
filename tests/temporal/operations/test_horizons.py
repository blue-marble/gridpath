# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from collections import OrderedDict
from importlib import import_module
import os.path
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = ["temporal.operations.timepoints"]
NAME_OF_MODULE_BEING_TESTED = "temporal.operations.horizons"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package="gridpath")
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestHorizons(unittest.TestCase):
    """ """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        """
        create_abstract_model(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        """
        add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # TODO: add test data with more horizon types

        # Load test data
        balancing_type_horizon_horizons_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "horizons.tab"), sep="\t"
        )

        timepoints_on_balancing_type_horizon_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "horizon_timepoints.tab"),
            sep="\t",
        )

        # Check data are as expected
        # BLN_TYPE_HRZS set
        expected_horizons = [
            (b, h)
            for (b, h) in zip(
                balancing_type_horizon_horizons_df.balancing_type_horizon,
                balancing_type_horizon_horizons_df.horizon,
            )
        ]
        actual_horizons = [(b, h) for (b, h) in instance.BLN_TYPE_HRZS]
        self.assertListEqual(
            expected_horizons,
            actual_horizons,
            msg="HORIZONS set data does not load correctly.",
        )

        # Params: boundary
        expected_boundary_param = balancing_type_horizon_horizons_df.set_index(
            ["balancing_type_horizon", "horizon"]
        ).to_dict()["boundary"]
        actual_boundary_param = {
            (b, h): instance.boundary[b, h] for (b, h) in instance.BLN_TYPE_HRZS
        }
        self.assertDictEqual(
            expected_boundary_param,
            actual_boundary_param,
            msg="Data for param 'boundary' not loaded " "correctly",
        )

        # BLN_TYPES set
        expected_balancing_type_horizons = list(
            balancing_type_horizon_horizons_df.balancing_type_horizon.unique()
        )
        actual_balancing_type_horizons = list(instance.BLN_TYPES)
        self.assertListEqual(
            expected_balancing_type_horizons, actual_balancing_type_horizons
        )

        # HRZS_BY_BLN_TYPE set
        expected_horizon_by_balancing_type_horizon = {
            balancing_type_horizon: horizons["horizon"].tolist()
            for balancing_type_horizon, horizons in balancing_type_horizon_horizons_df.groupby(
                "balancing_type_horizon"
            )
        }
        actual_horizon_by_balancing_type_horizon = {
            balancing_type_horizon: [
                horizon
                for horizon in list(instance.HRZS_BY_BLN_TYPE[balancing_type_horizon])
            ]
            for balancing_type_horizon in instance.HRZS_BY_BLN_TYPE.keys()
        }
        self.assertDictEqual(
            expected_horizon_by_balancing_type_horizon,
            actual_horizon_by_balancing_type_horizon,
        )

        # TMPS_BLN_TYPES
        expected_tmps_bln_types = sorted(
            timepoints_on_balancing_type_horizon_df[
                ["timepoint", "balancing_type_horizon"]
            ]
            .drop_duplicates()
            .to_records(index=False)
            .tolist()
        )
        actual_tmps_bln_types = sorted(
            (tmp, bt) for (tmp, bt) in instance.TMPS_BLN_TYPES
        )
        self.assertListEqual(expected_tmps_bln_types, actual_tmps_bln_types)

        # Set TMPS_BY_BLN_TYPE_HRZ
        expected_tmps_on_horizon = {
            (balancing_type, horizon): timepoints["timepoint"].tolist()
            for (
                (balancing_type, horizon),
                timepoints,
            ) in timepoints_on_balancing_type_horizon_df.groupby(
                ["balancing_type_horizon", "horizon"]
            )
        }

        actual_tmps_on_horizon = {
            (b, h): [tmp for tmp in instance.TMPS_BY_BLN_TYPE_HRZ[b, h]]
            for (b, h) in list(instance.TMPS_BY_BLN_TYPE_HRZ.keys())
        }

        self.assertDictEqual(
            expected_tmps_on_horizon,
            actual_tmps_on_horizon,
            msg="TMPS_BY_BLN_TYPE_HRZ data do not match " "expected.",
        )

        # Param: horizon
        expected_horizon_by_tmp_type = {
            (tmp, balancing_type_horizon): horizon
            for tmp, balancing_type_horizon, horizon in zip(
                timepoints_on_balancing_type_horizon_df.timepoint,
                timepoints_on_balancing_type_horizon_df.balancing_type_horizon,
                timepoints_on_balancing_type_horizon_df.horizon,
            )
        }
        actual_horizon_by_tmp_type = {
            (tmp, _type): instance.horizon[tmp, _type]
            for tmp in instance.TMPS
            for _type in instance.BLN_TYPES
        }
        self.assertDictEqual(expected_horizon_by_tmp_type, actual_horizon_by_tmp_type)

        # Param: first_hrz_tmp
        expected_first_hrz_tmp = {
            (b, h): expected_tmps_on_horizon[b, h][0] for (b, h) in expected_horizons
        }
        actual_first_hrz_tmp = {
            (b, h): instance.first_hrz_tmp[b, h] for (b, h) in instance.BLN_TYPE_HRZS
        }
        self.assertDictEqual(
            expected_first_hrz_tmp,
            actual_first_hrz_tmp,
            msg="Data for param " "first_hrz_tmp do " "not match expected.",
        )

        # Param: last_hrz_tmp
        expected_last_hrz_tmp = {
            (b, h): expected_tmps_on_horizon[b, h][-1] for (b, h) in expected_horizons
        }
        actual_last_hrz_tmp = {
            (b, h): instance.last_hrz_tmp[b, h] for (b, h) in instance.BLN_TYPE_HRZS
        }
        self.assertDictEqual(
            expected_last_hrz_tmp,
            actual_last_hrz_tmp,
            msg="Data for param " "last_hrz_tmp do " "not match expected.",
        )

        # Param: prev_tmp
        # Testing for both horizons that are 'circular' and 'linear'
        # TODO: should we have the actual previous timepoints in a data file
        #  somewhere as opposed to figuring it out here
        expected_prev_tmp = dict()
        prev_tmp = None
        for horizon, balancing_type, tmp in [
            tuple(row) for row in timepoints_on_balancing_type_horizon_df.values
        ]:
            if tmp == expected_first_hrz_tmp[balancing_type, horizon]:
                if expected_boundary_param[balancing_type, horizon] == "circular":
                    expected_prev_tmp[tmp, balancing_type] = expected_last_hrz_tmp[
                        balancing_type, horizon
                    ]
                elif expected_boundary_param[balancing_type, horizon] == "linear":
                    expected_prev_tmp[tmp, balancing_type] = "."
                else:
                    raise (
                        ValueError,
                        "Test data specifies horizon boundary different "
                        "from allowed values of 'circular' and 'linear'",
                    )
            else:
                expected_prev_tmp[tmp, balancing_type] = prev_tmp
            prev_tmp = tmp

        actual_prev_tmp = {
            (tmp, bt): instance.prev_tmp[tmp, bt]
            for (tmp, bt) in instance.TMPS_BLN_TYPES
        }

        expected_prev_tmp_ordered = OrderedDict(sorted(expected_prev_tmp.items()))
        actual_prev_tmp_ordered = OrderedDict(sorted(actual_prev_tmp.items()))

        self.assertDictEqual(
            expected_prev_tmp_ordered,
            actual_prev_tmp_ordered,
            msg="Data for param prev_tmp do " "not match expected.",
        )

        # Param: next_tmp
        # Testing for both horizons that 'circular' and 'linear'
        expected_next_tmp = dict()
        prev_tmp = None
        for horizon, balancing_type, tmp in [
            tuple(row) for row in timepoints_on_balancing_type_horizon_df.values
        ]:
            if prev_tmp is None:
                if expected_boundary_param[balancing_type, horizon] == "circular":
                    expected_next_tmp[
                        expected_last_hrz_tmp[balancing_type, horizon], balancing_type
                    ] = expected_first_hrz_tmp[balancing_type, horizon]
                elif expected_boundary_param[balancing_type, horizon] == "linear":
                    expected_next_tmp[
                        expected_last_hrz_tmp[balancing_type, horizon], balancing_type
                    ] = "."
                else:
                    raise (
                        ValueError,
                        "Test data specifies horizon boundary different "
                        "from allowed values of 'circular' and 'linear'",
                    )
            else:
                expected_next_tmp[prev_tmp, balancing_type] = tmp
            # If we have reached the last horizon timepoint, set the
            # previous timepoint to None (to enter the boundary logic above)
            if tmp == expected_last_hrz_tmp[balancing_type, horizon]:
                prev_tmp = None
            else:
                prev_tmp = tmp

        expected_next_tmp_ordered = OrderedDict(sorted(expected_next_tmp.items()))

        actual_next_tmp = {
            (tmp, bt): instance.next_tmp[tmp, bt]
            for (tmp, bt) in instance.TMPS_BLN_TYPES
        }
        actual_next_tmp_ordered = OrderedDict(sorted(actual_next_tmp.items()))

        self.assertDictEqual(
            expected_next_tmp_ordered,
            actual_next_tmp_ordered,
            msg="Data for param next_tmp do not match " "expected.",
        )


if __name__ == "__main__":
    unittest.main()
