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
    "project",
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_types.fuel_prod_new"
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


class TestFuelProdNew(unittest.TestCase):
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
        Test that the data loaded are as expected
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

        # Set: FUEL_PROD_NEW
        expected_project_set = ["Fuel_Prod_New"]
        actual_project_set = sorted([prj for prj in instance.FUEL_PROD_NEW])
        self.assertListEqual(expected_project_set, actual_project_set)

        # Set: FUEL_PROD_NEW_VNTS
        expected_vintages = sorted([("Fuel_Prod_New", 2020), ("Fuel_Prod_New", 2030)])
        actual_vintages = sorted(
            [(prj, period) for (prj, period) in instance.FUEL_PROD_NEW_VNTS]
        )
        self.assertListEqual(expected_vintages, actual_vintages)

        # Params: fuel_prod_new_operational_lifetime_yrs
        expected_lifetime = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 30, ("Fuel_Prod_New", 2030): 30}.items())
        )
        actual_lifetime = OrderedDict(
            sorted(
                {
                    (prj, vintage): instance.fuel_prod_new_operational_lifetime_yrs[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: fuel_prod_new_prod_fixed_cost_fuelunitperhour_yr
        expected_prod_fcost = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 1, ("Fuel_Prod_New", 2030): 1}.items())
        )
        actual_prod_fcost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.fuel_prod_new_prod_fixed_cost_fuelunitperhour_yr[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_prod_fcost, actual_prod_fcost)

        # Params: fuel_prod_new_release_fixed_cost_fuelunitperhour_yr
        expected_rel_fcost = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 2, ("Fuel_Prod_New", 2030): 2}.items())
        )
        actual_rel_fcost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.fuel_prod_new_release_fixed_cost_fuelunitperhour_yr[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_rel_fcost, actual_rel_fcost)

        # Params: fuel_prod_new_storage_fixed_cost_fuelunit_yr
        expected_rel_fcost = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 3, ("Fuel_Prod_New", 2030): 3}.items())
        )
        actual_rel_fcost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.fuel_prod_new_storage_fixed_cost_fuelunit_yr[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_rel_fcost, actual_rel_fcost)

        # Params: fuel_prod_new_financial_lifetime_yrs
        expected_flifetime = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 20, ("Fuel_Prod_New", 2030): 30}.items())
        )
        actual_flifetime = OrderedDict(
            sorted(
                {
                    (prj, vintage): instance.fuel_prod_new_financial_lifetime_yrs[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_flifetime, actual_flifetime)

        # Params: fuel_prod_new_prod_cost_fuelunitperhour_yr
        expected_prod_cost = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 4, ("Fuel_Prod_New", 2030): 1}.items())
        )
        actual_prod_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.fuel_prod_new_prod_cost_fuelunitperhour_yr[prj, vintage]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_prod_cost, actual_prod_cost)

        # Params: fuel_prod_new_release_cost_fuelunitperhour_yr
        expected_rel_cost = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 5, ("Fuel_Prod_New", 2030): 2}.items())
        )
        actual_rel_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.fuel_prod_new_release_cost_fuelunitperhour_yr[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_rel_cost, actual_rel_cost)

        # Params: fuel_prod_new_storage_cost_fuelunit_yr
        expected_rel_cost = OrderedDict(
            sorted({("Fuel_Prod_New", 2020): 6, ("Fuel_Prod_New", 2030): 3}.items())
        )
        actual_rel_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.fuel_prod_new_storage_cost_fuelunit_yr[prj, vintage]
                    for (prj, vintage) in instance.FUEL_PROD_NEW_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_rel_cost, actual_rel_cost)

    def test_derived_data(self):
        """
        Calculations
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

        # Sets: OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE
        expected_op_periods_by_fuel_prod_vintage = {
            ("Fuel_Prod_New", 2020): [2020, 2030],
            ("Fuel_Prod_New", 2030): [2030],
        }
        actual_periods_by_fuel_prod_vintage = {
            (prj, vintage): [
                period
                for period in instance.OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE[prj, vintage]
            ]
            for (prj, vintage) in instance.OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE
        }
        self.assertDictEqual(
            expected_op_periods_by_fuel_prod_vintage,
            actual_periods_by_fuel_prod_vintage,
        )

        # Sets: FUEL_PROD_NEW_FIN_PRDS
        expected_fuel_prod_f_periods = sorted(
            [("Fuel_Prod_New", 2020), ("Fuel_Prod_New", 2030)]
        )
        actual_fuel_prod_f_periods = sorted(
            [(prj, period) for (prj, period) in instance.FUEL_PROD_NEW_FIN_PRDS]
        )
        self.assertListEqual(expected_fuel_prod_f_periods, actual_fuel_prod_f_periods)

        # Sets: FUEL_PROD_NEW_VNTS_FIN_IN_PRD
        expected_fuel_prod_vintage_f_in_period = {
            2020: [("Fuel_Prod_New", 2020)],
            2030: [("Fuel_Prod_New", 2020), ("Fuel_Prod_New", 2030)],
        }
        actual_fuel_prod_vintage_f_in_period = {
            p: [(g, v) for (g, v) in instance.FUEL_PROD_NEW_VNTS_FIN_IN_PRD[p]]
            for p in instance.PERIODS
        }
        self.assertDictEqual(
            expected_fuel_prod_vintage_f_in_period,
            actual_fuel_prod_vintage_f_in_period,
        )

        # Sets: FUEL_PROD_NEW_OPR_PRDS
        expected_fuel_prod_op_periods = sorted(
            [("Fuel_Prod_New", 2020), ("Fuel_Prod_New", 2030)]
        )
        actual_fuel_prod_op_periods = sorted(
            [(prj, period) for (prj, period) in instance.FUEL_PROD_NEW_OPR_PRDS]
        )
        self.assertListEqual(expected_fuel_prod_op_periods, actual_fuel_prod_op_periods)

        # Sets: FUEL_PROD_NEW_VNTS_OPR_IN_PRD
        expected_fuel_prod_vintage_op_in_period = {
            2020: [("Fuel_Prod_New", 2020)],
            2030: [("Fuel_Prod_New", 2020), ("Fuel_Prod_New", 2030)],
        }
        actual_fuel_prod_vintage_op_in_period = {
            p: [(g, v) for (g, v) in instance.FUEL_PROD_NEW_VNTS_OPR_IN_PRD[p]]
            for p in instance.PERIODS
        }
        self.assertDictEqual(
            expected_fuel_prod_vintage_op_in_period,
            actual_fuel_prod_vintage_op_in_period,
        )


if __name__ == "__main__":
    unittest.main()
