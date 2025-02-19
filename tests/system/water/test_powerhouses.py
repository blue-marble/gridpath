# Copyright 2016-2024 Blue Marble Analytics LLC.
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
    "geography.water_network",
    "system.water.water_system_params",
    "system.water.water_nodes",
    "system.water.water_flows",
    "system.water.water_node_inflows_outflows",
    "system.water.reservoirs",
    "system.water.water_node_balance",
]
NAME_OF_MODULE_BEING_TESTED = "system.water.powerhouses"
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


class TestWaterNodeBalance(unittest.TestCase):
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

        # Set: POWERHOUSES
        expected_pwrh = sorted(["Powerhouse1", "Powerhouse2"])
        actual_pwrh = sorted([n for n in instance.POWERHOUSES])

        self.assertListEqual(expected_pwrh, actual_pwrh)

        # Set: POWERHOUSE_GENERATORS
        expected_pwrh_g = sorted([("Powerhouse1", "Hydro_System_Gen1")])
        actual_pwrh_g = sorted([(p, g) for (p, g) in instance.POWERHOUSE_GENERATORS])

        self.assertListEqual(expected_pwrh_g, actual_pwrh_g)

        # Set: GENERATORS_BY_POWERHOUSE
        expected_g_by_p = {
            "Powerhouse1": ["Hydro_System_Gen1"],
            "Powerhouse2": [],
        }
        actual_g_by_p = {
            p: [g for g in instance.GENERATORS_BY_POWERHOUSE[p]]
            for p in instance.POWERHOUSES
        }
        self.assertDictEqual(expected_g_by_p, actual_g_by_p)

        # Param: powerhouse_water_node
        expected_res = {
            "Powerhouse1": "Water_Node_1",
            "Powerhouse2": "Water_Node_2",
        }
        actual_res = {
            p: instance.powerhouse_water_node[p] for p in instance.POWERHOUSES
        }
        self.assertDictEqual(expected_res, actual_res)

        # Param: tailwater_elevation
        expected_telev = {
            "Powerhouse1": 800,
            "Powerhouse2": 600,
        }
        actual_telev = {
            p: instance.tailwater_elevation[p] for p in instance.POWERHOUSES
        }
        self.assertDictEqual(expected_telev, actual_telev)

        # Param: headloss_factor
        expected_headloss = {
            "Powerhouse1": 0.05,
            "Powerhouse2": 0.05,
        }
        actual_headloss = {p: instance.headloss_factor[p] for p in instance.POWERHOUSES}
        self.assertDictEqual(expected_headloss, actual_headloss)

        # Param: turbine_efficiency
        expected_t_eff = {
            "Powerhouse1": 0.9,
            "Powerhouse2": 0.9,
        }
        actual_t_eff = {p: instance.turbine_efficiency[p] for p in instance.POWERHOUSES}
        self.assertDictEqual(expected_t_eff, actual_t_eff)
