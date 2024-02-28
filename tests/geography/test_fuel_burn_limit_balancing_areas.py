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

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
]
NAME_OF_MODULE_BEING_TESTED = "geography.fuel_burn_limit_balancing_areas"
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


class TestFuelBurnLimitBalancingAreas(unittest.TestCase):
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

        # Set: FUEL_BURN_LIMIT_BAS
        expected_bas = sorted(
            [
                ("Gas", "Zone1"),
                ("Coal", "Zone1"),
                ("Coal", "Zone2"),
                ("Nuclear", "Zone1"),
            ]
        )
        actual_bas = sorted([(f, ba) for (f, ba) in instance.FUEL_BURN_LIMIT_BAS])
        self.assertListEqual(expected_bas, actual_bas)

        # Param: min_allow_violation
        expected_allow_violation = OrderedDict(
            sorted(
                {
                    ("Gas", "Zone1"): 0,
                    ("Coal", "Zone1"): 0,
                    ("Coal", "Zone2"): 1,
                    ("Nuclear", "Zone1"): 0,
                }.items()
            )
        )
        actual_allow_violation = OrderedDict(
            sorted(
                {
                    (f, ba): instance.fuel_burn_min_allow_violation[f, ba]
                    for (f, ba) in instance.FUEL_BURN_LIMIT_BAS
                }.items()
            )
        )
        self.assertDictEqual(expected_allow_violation, actual_allow_violation)

        # Param: min_violation penalty
        expected_penalty = OrderedDict(
            sorted(
                {
                    ("Gas", "Zone1"): 10,
                    ("Coal", "Zone1"): 10,
                    ("Coal", "Zone2"): 15,
                    ("Nuclear", "Zone1"): 15,
                }.items()
            )
        )
        actual_penalty = OrderedDict(
            sorted(
                {
                    (f, ba): instance.fuel_burn_min_violation_penalty_per_unit[f, ba]
                    for (f, ba) in instance.FUEL_BURN_LIMIT_BAS
                }.items()
            )
        )
        self.assertDictEqual(expected_penalty, actual_penalty)

        # Param: max_allow_violation
        expected_allow_violation = OrderedDict(
            sorted(
                {
                    ("Gas", "Zone1"): 0,
                    ("Coal", "Zone1"): 0,
                    ("Coal", "Zone2"): 0,
                    ("Nuclear", "Zone1"): 1,
                }.items()
            )
        )
        actual_allow_violation = OrderedDict(
            sorted(
                {
                    (f, ba): instance.fuel_burn_max_allow_violation[f, ba]
                    for (f, ba) in instance.FUEL_BURN_LIMIT_BAS
                }.items()
            )
        )
        self.assertDictEqual(expected_allow_violation, actual_allow_violation)

        # Param: max_violation penalty
        expected_penalty = OrderedDict(
            sorted(
                {
                    ("Gas", "Zone1"): 99999,
                    ("Coal", "Zone1"): 99999,
                    ("Coal", "Zone2"): 99999,
                    ("Nuclear", "Zone1"): 10,
                }.items()
            )
        )
        actual_penalty = OrderedDict(
            sorted(
                {
                    (f, ba): instance.fuel_burn_max_violation_penalty_per_unit[f, ba]
                    for (f, ba) in instance.FUEL_BURN_LIMIT_BAS
                }.items()
            )
        )
        self.assertDictEqual(expected_penalty, actual_penalty)

        # Param: relative_max_allow_violation
        expected_allow_violation = OrderedDict(
            sorted(
                {
                    ("Gas", "Zone1"): 0,
                    ("Coal", "Zone1"): 0,
                    ("Coal", "Zone2"): 0,
                    ("Nuclear", "Zone1"): 1,
                }.items()
            )
        )
        actual_allow_violation = OrderedDict(
            sorted(
                {
                    (f, ba): instance.fuel_burn_relative_max_allow_violation[f, ba]
                    for (f, ba) in instance.FUEL_BURN_LIMIT_BAS
                }.items()
            )
        )
        self.assertDictEqual(expected_allow_violation, actual_allow_violation)

        # Param: relative_max_violation penalty
        expected_penalty = OrderedDict(
            sorted(
                {
                    ("Gas", "Zone1"): 10,
                    ("Coal", "Zone1"): 99999,
                    ("Coal", "Zone2"): 99999,
                    ("Nuclear", "Zone1"): 10,
                }.items()
            )
        )
        actual_penalty = OrderedDict(
            sorted(
                {
                    (f, ba): instance.fuel_burn_relative_max_violation_penalty_per_unit[
                        f, ba
                    ]
                    for (f, ba) in instance.FUEL_BURN_LIMIT_BAS
                }.items()
            )
        )
        self.assertDictEqual(expected_penalty, actual_penalty)
