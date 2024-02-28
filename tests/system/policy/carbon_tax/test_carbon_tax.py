# Copyright 2021 (c) Crown Copyright, GC.
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
    "geography.carbon_tax_zones",
]
NAME_OF_MODULE_BEING_TESTED = "system.policy.carbon_tax.carbon_tax"
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


class TestCarbonTax(unittest.TestCase):
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

        # Set: CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX
        expected_ct_zone_periods = sorted(
            [
                ("Carbon_Tax_Zone1", 2020),
                ("Carbon_Tax_Zone1", 2030),
                ("Carbon_Tax_Zone2", 2020),
                ("Carbon_Tax_Zone2", 2030),
            ]
        )
        actual_ct_zone_periods = sorted(
            [(z, p) for (z, p) in instance.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX]
        )
        self.assertListEqual(expected_ct_zone_periods, actual_ct_zone_periods)

        # Param: carbon_tax
        expected_carbon_tax = OrderedDict(
            sorted(
                {
                    ("Carbon_Tax_Zone1", 2020): 30,
                    ("Carbon_Tax_Zone1", 2030): 50,
                    ("Carbon_Tax_Zone2", 2020): 10,
                    ("Carbon_Tax_Zone2", 2030): 20,
                }.items()
            )
        )
        actual_carbon_tax = OrderedDict(
            sorted(
                {
                    (z, p): instance.carbon_tax[z, p]
                    for (z, p) in instance.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX
                }.items()
            )
        )
        self.assertDictEqual(expected_carbon_tax, actual_carbon_tax)


if __name__ == "__main__":
    unittest.main()
