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
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "test_data")

# No prerequisite modules
NAME_OF_MODULE_BEING_TESTED = "geography.spinning_reserves_balancing_areas"

try:
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestSpinningReservesBAs(unittest.TestCase):
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

    def test_spinning_reserves_zones_data_loads_correctly(self):
        """
        Create set and load data; check resulting set is as expected
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

        # Balancing areas
        expected = sorted(["Zone1", "Zone2"])
        actual = sorted([z for z in instance.SPINNING_RESERVES_ZONES])
        self.assertListEqual(
            expected,
            actual,
            msg="SPINNING_RESERVES_ZONES set data does not " "load correctly.",
        )

        # Param: allow_violation
        expected_allow_violation = OrderedDict(sorted({"Zone1": 1, "Zone2": 1}.items()))
        actual_allow_violation = OrderedDict(
            sorted(
                {
                    z: instance.spinning_reserves_allow_violation[z]
                    for z in instance.SPINNING_RESERVES_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_allow_violation, actual_allow_violation)

        # Param: violation penalty
        expected_penalty = OrderedDict(
            sorted({"Zone1": 99999999, "Zone2": 99999999}.items())
        )
        actual_penalty = OrderedDict(
            sorted(
                {
                    z: instance.spinning_reserves_violation_penalty_per_mw[z]
                    for z in instance.SPINNING_RESERVES_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_penalty, actual_penalty)


if __name__ == "__main__":
    unittest.main()
