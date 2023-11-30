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
    "project",
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_types.fuel_prod_spec"
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


class TestFuelProdSpec(unittest.TestCase):
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
        Test that the data loaded are as expected
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

        # Set: FUEL_SPEC_OPR_PRDS
        expected_proj_period_set = sorted([("Fuel_Prod", 2030)])
        actual_proj_period_set = sorted(
            [(prj, period) for (prj, period) in instance.FUEL_SPEC_OPR_PRDS]
        )
        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)

        # Capacity
        # Params: fuel_production_capacity_fuelunitperhour
        expected_prod_cap = OrderedDict(sorted({("Fuel_Prod", 2030): 100}.items()))
        actual_prod_cap = OrderedDict(
            sorted(
                {
                    (prj, period): instance.fuel_production_capacity_fuelunitperhour[
                        prj, period
                    ]
                    for (prj, period) in instance.FUEL_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_prod_cap, actual_prod_cap)

        # Params: fuel_release_capacity_fuelunitperhour
        expected_rel_cap = OrderedDict(sorted({("Fuel_Prod", 2030): 1000}.items()))
        actual_rel_cap = OrderedDict(
            sorted(
                {
                    (prj, period): instance.fuel_release_capacity_fuelunitperhour[
                        prj, period
                    ]
                    for (prj, period) in instance.FUEL_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_rel_cap, actual_rel_cap)

        # Params: fuel_storage_capacity_fuelunit
        expected_stor_cap = OrderedDict(sorted({("Fuel_Prod", 2030): 10000}.items()))
        actual_stor_cap = OrderedDict(
            sorted(
                {
                    (prj, period): instance.fuel_storage_capacity_fuelunit[prj, period]
                    for (prj, period) in instance.FUEL_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_stor_cap, actual_stor_cap)

        # Fixed costs
        # Params: fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr
        expected_prod_cost = OrderedDict(sorted({("Fuel_Prod", 2030): 10}.items()))
        actual_prod_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        period,
                    ): instance.fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr[
                        prj, period
                    ]
                    for (prj, period) in instance.FUEL_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_prod_cost, actual_prod_cost)

        # Params: fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr
        expected_rel_cost = OrderedDict(sorted({("Fuel_Prod", 2030): 100}.items()))
        actual_rel_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        period,
                    ): instance.fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr[
                        prj, period
                    ]
                    for (prj, period) in instance.FUEL_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_rel_cost, actual_rel_cost)

        # Params: fuel_storage_capacity_fixed_cost_per_fuelunit_yr
        expected_stor_cost = OrderedDict(sorted({("Fuel_Prod", 2030): 1000}.items()))
        actual_stor_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        period,
                    ): instance.fuel_storage_capacity_fixed_cost_per_fuelunit_yr[
                        prj, period
                    ]
                    for (prj, period) in instance.FUEL_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_stor_cost, actual_stor_cost)


if __name__ == "__main__":
    unittest.main()
