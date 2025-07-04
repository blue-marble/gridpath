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
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "geography.markets",
    "geography.water_network",
    "system.water.water_system_params",
    "system.water.water_nodes",
    "system.water.water_flows",
    "system.water.water_node_inflows_outflows",
    "system.water.reservoirs",
    "system.water.water_node_balance",
    "system.water.powerhouses",
    "project",
    "project.capacity.capacity",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
    "system.load_balance.static_load_requirement",
    "project.capacity.potential",
    "project.operations.operational_types",
    "project.operations.power",
    "system.markets.market_participation",
]
NAME_OF_MODULE_BEING_TESTED = "system.markets.volume"
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


class TestMarketPrices(unittest.TestCase):
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

        # Load test data
        # Load test data
        market_volume_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "market_volume.tab"), sep="\t"
        )

        # Param: max_market_sales
        expected_max_sales = OrderedDict(
            sorted(
                market_volume_df.set_index(["market", "timepoint"])
                .to_dict()["max_market_sales"]
                .items()
            )
        )
        actual_max_sales = OrderedDict(
            sorted(
                {
                    (mrkt, tmp): instance.max_market_sales[mrkt, tmp]
                    for mrkt in instance.MARKETS
                    for tmp in instance.TMPS
                }.items()
            )
        )
        self.assertDictEqual(expected_max_sales, actual_max_sales)

        # Param: max_market_purchases
        expected_max_purchases = OrderedDict(
            sorted(
                market_volume_df.set_index(["market", "timepoint"])
                .to_dict()["max_market_purchases"]
                .items()
            )
        )
        actual_max_purchases = OrderedDict(
            sorted(
                {
                    (mrkt, tmp): instance.max_market_purchases[mrkt, tmp]
                    for mrkt in instance.MARKETS
                    for tmp in instance.TMPS
                }.items()
            )
        )
        self.assertDictEqual(expected_max_purchases, actual_max_purchases)

        # Param: max_final_market_sales
        expected_max_final_sales = OrderedDict(
            sorted(
                market_volume_df.set_index(["market", "timepoint"])
                .to_dict()["max_final_market_sales"]
                .items()
            )
        )
        for key in expected_max_final_sales.keys():
            expected_max_final_sales[key] = float("inf")

        actual_max_final_sales = OrderedDict(
            sorted(
                {
                    (mrkt, tmp): instance.max_final_market_sales[mrkt, tmp]
                    for mrkt in instance.MARKETS
                    for tmp in instance.TMPS
                }.items()
            )
        )
        self.assertDictEqual(expected_max_final_sales, actual_max_final_sales)

        # Param: max_final_market_purchases
        expected_max_final_purchases = OrderedDict(
            sorted(
                market_volume_df.set_index(["market", "timepoint"])
                .to_dict()["max_final_market_purchases"]
                .items()
            )
        )
        actual_max_final_purchases = OrderedDict(
            sorted(
                {
                    (mrkt, tmp): instance.max_final_market_purchases[mrkt, tmp]
                    for mrkt in instance.MARKETS
                    for tmp in instance.TMPS
                }.items()
            )
        )
        self.assertDictEqual(expected_max_final_purchases, actual_max_final_purchases)


if __name__ == "__main__":
    unittest.main()
