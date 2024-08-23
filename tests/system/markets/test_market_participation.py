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


from importlib import import_module
import os.path
from pyomo.environ import value
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "geography.markets",
]
NAME_OF_MODULE_BEING_TESTED = "system.markets.market_participation"
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


class TestMarketParticipation(unittest.TestCase):
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

        # Set: LZ_MARKETS
        expected_lz_markets = sorted(
            [
                ("Zone1", "Market_Hub_1"),
                ("Zone1", "Market_Hub_2"),
                ("Zone2", "Market_Hub_1"),
            ]
        )
        actual_lz_markets = sorted([(z, mrk) for (z, mrk) in instance.LZ_MARKETS])
        self.assertListEqual(expected_lz_markets, actual_lz_markets)

        # Set: MARKET_LZS
        expected_market_lzs = sorted(["Zone1", "Zone2"])
        actual_market_lzs = sorted([z for z in instance.MARKET_LZS])
        self.assertListEqual(expected_market_lzs, actual_market_lzs)

        # Set: MARKETS_BY_LZ
        expected_markets_by_lz = {
            "Zone1": ["Market_Hub_1", "Market_Hub_2"],
            "Zone2": ["Market_Hub_1"],
        }

        actual_markets_by_lz = {
            z: [mrkt for mrkt in instance.MARKETS_BY_LZ[z]] for z in instance.MARKET_LZS
        }
        self.assertDictEqual(expected_markets_by_lz, actual_markets_by_lz)

        # Param: final_participation_stage
        expected_final_participation_stage = {
            ("Zone1", "Market_Hub_1"): 2,
            ("Zone1", "Market_Hub_2"): 3,
            ("Zone2", "Market_Hub_1"): 1,
        }
        actual_final_participation_stage = {
            (z, m): instance.final_participation_stage[z, m]
            for (z, m) in instance.LZ_MARKETS
        }
        self.assertDictEqual(
            expected_final_participation_stage, actual_final_participation_stage
        )

        # Param: first_stage_flag
        self.assertEqual(True, instance.first_stage_flag.value)

        # Param: no_market_participation_in_stage
        expected_no_market_participation_in_stage = {
            ("Zone1", "Market_Hub_1"): False,
            ("Zone1", "Market_Hub_2"): False,
            ("Zone2", "Market_Hub_1"): False,
        }
        actual_no_market_participation_in_stage = {
            (z, m): instance.no_market_participation_in_stage[z, m]
            for (z, m) in instance.LZ_MARKETS
        }
        self.assertDictEqual(
            expected_no_market_participation_in_stage,
            actual_no_market_participation_in_stage,
        )


if __name__ == "__main__":
    unittest.main()
