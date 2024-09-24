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
NAME_OF_MODULE_BEING_TESTED = "geography.instantaneous_penetration_zones"

# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestInstantaneousPenetrationZones(unittest.TestCase):
    """ """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(
            prereq_modules=[],
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
            prereq_modules=[],
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
            prereq_modules=[],
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: INSTANTANEOUS_PENETRATION_ZONES
        expected_energy_target_zones = sorted(["IPZone1"])
        actual_energy_target_zones = sorted(
            [z for z in instance.INSTANTANEOUS_PENETRATION_ZONES]
        )
        self.assertListEqual(expected_energy_target_zones, actual_energy_target_zones)

        # Param: allow_violation
        expected_allow_violation = OrderedDict(sorted({"IPZone1": 0}.items()))
        actual_allow_violation = OrderedDict(
            sorted(
                {
                    z: instance.allow_violation_min_penetration[z]
                    for z in instance.INSTANTANEOUS_PENETRATION_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_allow_violation, actual_allow_violation)

        # Param: violation penalty
        expected_penalty = OrderedDict(sorted({"IPZone1": 0}.items()))
        actual_penalty = OrderedDict(
            sorted(
                {
                    z: instance.violation_penalty_min_penetration_per_mwh[z]
                    for z in instance.INSTANTANEOUS_PENETRATION_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_penalty, actual_penalty)
        # Param: allow_violation
        expected_allow_violation = OrderedDict(sorted({"IPZone1": 0}.items()))
        actual_allow_violation = OrderedDict(
            sorted(
                {
                    z: instance.allow_violation_max_penetration[z]
                    for z in instance.INSTANTANEOUS_PENETRATION_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_allow_violation, actual_allow_violation)

        # Param: violation penalty
        expected_penalty = OrderedDict(sorted({"IPZone1": 0}.items()))
        actual_penalty = OrderedDict(
            sorted(
                {
                    z: instance.violation_penalty_max_penetration_per_mwh[z]
                    for z in instance.INSTANTANEOUS_PENETRATION_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_penalty, actual_penalty)


if __name__ == "__main__":
    unittest.main()
