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
    "geography.load_zones",
    "geography.prm_zones",
    "project",
    "project.capacity.capacity",
    "system.reliability.prm.prm_requirement",
    "project.reliability.prm",
    "project.reliability.prm.prm_types",
    "project.reliability.prm.prm_simple",
    "system.reliability.prm.aggregate_project_simple_prm_contribution",
    "transmission.reliability.capacity_transfer_links",
    "transmission",
    "transmission.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "system.reliability.prm.capacity_contribution_transfers"
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


class TestCapacityContributionTransfers(unittest.TestCase):
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

        # Param: min_transfer_powerunit
        expected_min_transfer_powerunit = {
            ("PRM_Zone1", "PRM_Zone2", 2020): 0,
            ("PRM_Zone1", "PRM_Zone2", 2030): 0,
        }

        actual_min_transfer_powerunit = {
            (z, z_to, p): instance.min_transfer_powerunit[z, z_to, p]
            for (z, z_to) in instance.PRM_ZONES_CAPACITY_TRANSFER_ZONES
            for p in instance.PERIODS
        }

        self.assertDictEqual(
            expected_min_transfer_powerunit, actual_min_transfer_powerunit
        )

        # Param: max_transfer_powerunit
        expected_max_transfer_powerunit = {
            ("PRM_Zone1", "PRM_Zone2", 2020): 99,
            ("PRM_Zone1", "PRM_Zone2", 2030): float("inf"),
        }

        actual_max_transfer_powerunit = {
            (z, z_to, p): instance.max_transfer_powerunit[z, z_to, p]
            for (z, z_to) in instance.PRM_ZONES_CAPACITY_TRANSFER_ZONES
            for p in instance.PERIODS
        }

        self.assertDictEqual(
            expected_max_transfer_powerunit, actual_max_transfer_powerunit
        )

        # Param: capacity_transfer_cost_per_powerunit_yr
        expected_cost = {
            ("PRM_Zone1", "PRM_Zone2", 2020): 1,
            ("PRM_Zone1", "PRM_Zone2", 2030): 0,
        }

        actual_cost = {
            (z, z_to, p): instance.capacity_transfer_cost_per_powerunit_yr[z, z_to, p]
            for (z, z_to) in instance.PRM_ZONES_CAPACITY_TRANSFER_ZONES
            for p in instance.PERIODS
        }

        self.assertDictEqual(expected_cost, actual_cost)

        # Set: PRM_TX_LINES
        expected_prm_tx_lines = sorted(["Tx1", "Tx_New"])
        actual_prm_tx_lines = sorted([tx for tx in instance.PRM_TX_LINES])

        self.assertListEqual(expected_prm_tx_lines, actual_prm_tx_lines)

        # Param: prm_zone_from
        expected_from = {"Tx1": "PRM_Zone1", "Tx_New": "PRM_Zone2"}

        actual_from = {tx: instance.prm_zone_from[tx] for tx in instance.PRM_TX_LINES}

        self.assertDictEqual(expected_from, actual_from)

        # Param: prm_zone_to
        expected_to = {"Tx1": "PRM_Zone2", "Tx_New": "PRM_Zone1"}

        actual_to = {tx: instance.prm_zone_to[tx] for tx in instance.PRM_TX_LINES}

        self.assertDictEqual(expected_to, actual_to)


if __name__ == "__main__":
    unittest.main()
