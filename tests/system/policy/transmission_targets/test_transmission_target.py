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
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.transmission_target_zones",
]
NAME_OF_MODULE_BEING_TESTED = "system.policy.transmission_targets.transmission_target"
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


class TestPeriodTxTarget(unittest.TestCase):
    """ """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
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
        :return:
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

    def test_data_loaded_correctly(self):
        """
        Test components initialized with data as expected
        :return:
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

        # Set: Tx_Target_Zone1
        expected_tx_target_zone_periods_min = sorted(
            [
                ("Tx_Target_Zone1", "year", 2020),
                ("Tx_Target_Zone1", "year", 2030),
                ("Tx_Target_Zone2", "year", 2020),
                ("Tx_Target_Zone2", "year", 2030),
            ]
        )
        actual_tx_target_zone_bt_hrz_min = sorted(
            [
                (z, bt, hz)
                for (
                    z,
                    bt,
                    hz,
                ) in instance.TRANSMISSION_TARGET_ZONE_BLN_TYPE_HRZS_WITH_TRANSMISSION_TARGET
            ]
        )
        self.assertListEqual(
            expected_tx_target_zone_periods_min, actual_tx_target_zone_bt_hrz_min
        )

        # Param: transmission_target_pos_dir_min_mwh
        expected_tx_target_pos = OrderedDict(
            sorted(
                {
                    ("Tx_Target_Zone1", "year", 2020): 50,
                    ("Tx_Target_Zone1", "year", 2030): 0,
                    ("Tx_Target_Zone2", "year", 2020): 10,
                    ("Tx_Target_Zone2", "year", 2030): 10,
                }.items()
            )
        )
        actual_tx_target_pos = OrderedDict(
            sorted(
                {
                    (z, bt, hz): instance.transmission_target_pos_dir_min_mwh[z, bt, hz]
                    for (
                        z,
                        bt,
                        hz,
                    ) in instance.TRANSMISSION_TARGET_ZONE_BLN_TYPE_HRZS_WITH_TRANSMISSION_TARGET
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_target_pos, actual_tx_target_pos)

        # Param: transmission_target_pos_dir_max_mwh
        expected_tx_target_pos_max = OrderedDict(
            sorted(
                {
                    ("Tx_Target_Zone1", "year", 2020): float("inf"),
                    ("Tx_Target_Zone1", "year", 2030): 100,
                    ("Tx_Target_Zone2", "year", 2020): float("inf"),
                    ("Tx_Target_Zone2", "year", 2030): 20,
                }.items()
            )
        )
        actual_tx_target_pos_max = OrderedDict(
            sorted(
                {
                    (z, bt, hz): instance.transmission_target_pos_dir_max_mwh[z, bt, hz]
                    for (
                        z,
                        bt,
                        hz,
                    ) in instance.TRANSMISSION_TARGET_ZONE_BLN_TYPE_HRZS_WITH_TRANSMISSION_TARGET
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_target_pos_max, actual_tx_target_pos_max)

        # Param: transmission_target_neg_dir_min_mwh
        expected_tx_target_neg_min = OrderedDict(
            sorted(
                {
                    ("Tx_Target_Zone1", "year", 2020): 0.2,
                    ("Tx_Target_Zone1", "year", 2030): 0.33,
                    ("Tx_Target_Zone2", "year", 2020): 0,
                    ("Tx_Target_Zone2", "year", 2030): 0,
                }.items()
            )
        )
        actual_tx_target_neg_min = OrderedDict(
            sorted(
                {
                    (z, bt, hz): instance.transmission_target_neg_dir_min_mwh[z, bt, hz]
                    for (
                        z,
                        bt,
                        hz,
                    ) in instance.TRANSMISSION_TARGET_ZONE_BLN_TYPE_HRZS_WITH_TRANSMISSION_TARGET
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_target_neg_min, actual_tx_target_neg_min)

        # Param: transmission_target_neg_dir_max_mwh
        expected_tx_target_neg_max = OrderedDict(
            sorted(
                {
                    ("Tx_Target_Zone1", "year", 2020): 1,
                    ("Tx_Target_Zone1", "year", 2030): float("inf"),
                    ("Tx_Target_Zone2", "year", 2020): 10,
                    ("Tx_Target_Zone2", "year", 2030): float("inf"),
                }.items()
            )
        )
        actual_tx_target_neg_max = OrderedDict(
            sorted(
                {
                    (z, bt, hz): instance.transmission_target_neg_dir_max_mwh[z, bt, hz]
                    for (
                        z,
                        bt,
                        hz,
                    ) in instance.TRANSMISSION_TARGET_ZONE_BLN_TYPE_HRZS_WITH_TRANSMISSION_TARGET
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_target_neg_max, actual_tx_target_neg_max)


if __name__ == "__main__":
    unittest.main()
