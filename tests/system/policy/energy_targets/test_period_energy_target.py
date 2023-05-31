# Copyright 2016-2020 Blue Marble Analytics LLC.
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
    "geography.load_zones",
    "geography.energy_target_zones",
    "system.load_balance.static_load_requirement",
]
NAME_OF_MODULE_BEING_TESTED = "system.policy.energy_targets.period_energy_target"
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


class TestPeriodEnergyTarget(unittest.TestCase):
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
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET
        expected_energy_target_zone_periods = sorted(
            [
                ("RPS_Zone_1", 2020),
                ("RPS_Zone_1", 2030),
                ("RPS_Zone_2", 2020),
                ("RPS_Zone_2", 2030),
            ]
        )
        actual_energy_target_zone_periods = sorted(
            [
                (z, p)
                for (z, p) in instance.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET
            ]
        )
        self.assertListEqual(
            expected_energy_target_zone_periods, actual_energy_target_zone_periods
        )

        # Param: period_energy_target_mwh
        expected_energy_target = OrderedDict(
            sorted(
                {
                    ("RPS_Zone_1", 2020): 50,
                    ("RPS_Zone_1", 2030): 50,
                    ("RPS_Zone_2", 2020): 10,
                    ("RPS_Zone_2", 2030): 10,
                }.items()
            )
        )
        actual_energy_target = OrderedDict(
            sorted(
                {
                    (z, p): instance.period_energy_target_mwh[z, p]
                    for (z, p) in instance.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET
                }.items()
            )
        )
        self.assertDictEqual(expected_energy_target, actual_energy_target)

        # Param: period_energy_target_fraction
        expected_energy_target_fraction = OrderedDict(
            sorted(
                {
                    ("RPS_Zone_1", 2020): 0.2,
                    ("RPS_Zone_1", 2030): 0.33,
                    ("RPS_Zone_2", 2020): 0,
                    ("RPS_Zone_2", 2030): 0,
                }.items()
            )
        )
        actual_energy_target_fraction = OrderedDict(
            sorted(
                {
                    (z, p): instance.period_energy_target_fraction[z, p]
                    for (z, p) in instance.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET
                }.items()
            )
        )
        self.assertDictEqual(
            expected_energy_target_fraction, actual_energy_target_fraction
        )

        # Set: ENERGY_TARGET_ZONE_LOAD_ZONES
        expected_energy_target_zone_load_zones = sorted(
            [("RPS_Zone_1", "Zone1"), ("RPS_Zone_1", "Zone2"), ("RPS_Zone_2", "Zone3")]
        )
        actual_energy_target_zone_load_zones = sorted(
            [(z, p) for (z, p) in instance.PERIOD_ENERGY_TARGET_ZONE_LOAD_ZONES]
        )
        self.assertListEqual(
            expected_energy_target_zone_load_zones, actual_energy_target_zone_load_zones
        )


if __name__ == "__main__":
    unittest.main()
