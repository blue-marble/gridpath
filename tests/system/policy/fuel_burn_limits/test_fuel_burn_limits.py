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
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.fuel_burn_limit_balancing_areas",
]
NAME_OF_MODULE_BEING_TESTED = "system.policy.fuel_burn_limits.fuel_burn_limits"
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


Infinity = float("inf")
Negative_Infinity = float("-inf")


class TestSystemFuelBurnLimits(unittest.TestCase):
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

        # Set: FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
        expected_fuel_ba_bt_horizons = sorted(
            [
                ("Zone1", "year", 2020),
                ("Zone1", "year", 2030),
                ("Zone2", "year", 2020),
                ("Zone2", "year", 2030),
            ]
        )
        actual_fuel_ba_bt_horizons = sorted(
            [
                (ba, bt, h)
                for (
                    ba,
                    bt,
                    h,
                ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
            ]
        )
        self.assertListEqual(expected_fuel_ba_bt_horizons, actual_fuel_ba_bt_horizons)

        # Param: fuel_burn_min_unit
        expected_limit = OrderedDict(
            sorted(
                {
                    ("Zone1", "year", 2020): Negative_Infinity,
                    ("Zone1", "year", 2030): 1000,
                    ("Zone2", "year", 2020): 1000,
                    ("Zone2", "year", 2030): Negative_Infinity,
                }.items()
            )
        )
        actual_limit = OrderedDict(
            sorted(
                {
                    (ba, bt, h): instance.fuel_burn_min_unit[ba, bt, h]
                    for (
                        ba,
                        bt,
                        h,
                    ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
                }.items()
            )
        )

        self.assertDictEqual(expected_limit, actual_limit)

        # Param: fuel_burn_max_unit
        expected_limit = OrderedDict(
            sorted(
                {
                    ("Zone1", "year", 2020): 50,
                    ("Zone1", "year", 2030): 5,
                    ("Zone2", "year", 2020): 10,
                    ("Zone2", "year", 2030): 100,
                }.items()
            )
        )
        actual_limit = OrderedDict(
            sorted(
                {
                    (ba, bt, h): instance.fuel_burn_max_unit[ba, bt, h]
                    for (
                        ba,
                        bt,
                        h,
                    ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
                }.items()
            )
        )

        self.assertDictEqual(expected_limit, actual_limit)

        # Param: relative_fuel_burn_max_ba
        expected_relative_ba = OrderedDict(
            sorted(
                {
                    ("Zone1", "year", 2020): "undefined",
                    ("Zone1", "year", 2030): "undefined",
                    ("Zone2", "year", 2020): "Zone1",
                    ("Zone2", "year", 2030): "undefined",
                }.items()
            )
        )
        actual_relative_ba = OrderedDict(
            sorted(
                {
                    (ba, bt, h): instance.relative_fuel_burn_max_ba[ba, bt, h]
                    for (
                        ba,
                        bt,
                        h,
                    ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
                }.items()
            )
        )

        self.assertDictEqual(expected_relative_ba, actual_relative_ba)

        # Param: fraction_of_relative_fuel_burn_max_fuel_ba
        expected_relative_ba = OrderedDict(
            sorted(
                {
                    ("Zone1", "year", 2020): Infinity,
                    ("Zone1", "year", 2030): Infinity,
                    ("Zone2", "year", 2020): 0.5,
                    ("Zone2", "year", 2030): Infinity,
                }.items()
            )
        )
        actual_relative_ba = OrderedDict(
            sorted(
                {
                    (
                        ba,
                        bt,
                        h,
                    ): instance.fraction_of_relative_fuel_burn_max_fuel_ba[ba, bt, h]
                    for (
                        ba,
                        bt,
                        h,
                    ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
                }.items()
            )
        )

        self.assertDictEqual(expected_relative_ba, actual_relative_ba)

        # Set: FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_MIN_ABS_LIMIT
        expected_fuel_ba_bt_horizons_min_abs = sorted(
            [
                ("Zone1", "year", 2030),
                ("Zone2", "year", 2020),
            ]
        )
        actual_fuel_ba_bt_horizons_min_abs = sorted(
            [
                (ba, bt, h)
                for (
                    ba,
                    bt,
                    h,
                ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_MIN_ABS_LIMIT
            ]
        )
        self.assertListEqual(
            expected_fuel_ba_bt_horizons_min_abs, actual_fuel_ba_bt_horizons_min_abs
        )

        # Set: FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_MAX_ABS_LIMIT
        expected_fuel_ba_bt_horizons_max_abs = sorted(
            [
                ("Zone1", "year", 2020),
                ("Zone1", "year", 2030),
                ("Zone2", "year", 2020),
                ("Zone2", "year", 2030),
            ]
        )
        actual_fuel_ba_bt_horizons_max_abs = sorted(
            [
                (ba, bt, h)
                for (
                    ba,
                    bt,
                    h,
                ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_MAX_ABS_LIMIT
            ]
        )
        self.assertListEqual(
            expected_fuel_ba_bt_horizons_max_abs, actual_fuel_ba_bt_horizons_max_abs
        )

        # Set: FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_MAX_REL_LIMIT
        expected_fuel_ba_bt_horizons_rel = sorted(
            [
                ("Zone2", "year", 2020),
            ]
        )
        actual_fuel_ba_bt_horizons_rel = sorted(
            [
                (ba, bt, h)
                for (
                    ba,
                    bt,
                    h,
                ) in instance.FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_MAX_REL_LIMIT
            ]
        )
        self.assertListEqual(
            expected_fuel_ba_bt_horizons_rel, actual_fuel_ba_bt_horizons_rel
        )


if __name__ == "__main__":
    unittest.main()
