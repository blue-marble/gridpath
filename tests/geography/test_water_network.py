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
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
]
NAME_OF_MODULE_BEING_TESTED = "geography.water_network"
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


class TestWaterNetwork(unittest.TestCase):
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

        # Set: WATER_LINKS
        expected_wl = sorted(["Water_Link_12", "Water_Link_23"])
        actual_wl = sorted([wl for wl in instance.WATER_LINKS])
        self.assertListEqual(expected_wl, actual_wl)

        # Param: water_node_from
        expected_wn_from = {
            "Water_Link_12": "Water_Node_1",
            "Water_Link_23": "Water_Node_2",
        }
        actual_wn_from = {
            wl: instance.water_node_from[wl] for wl in instance.WATER_LINKS
        }
        self.assertDictEqual(expected_wn_from, actual_wn_from)

        # Param: water_node_to
        expected_wn_to = {
            "Water_Link_12": "Water_Node_2",
            "Water_Link_23": "Water_Node_3",
        }
        actual_wn_to = {wl: instance.water_node_to[wl] for wl in instance.WATER_LINKS}
        self.assertDictEqual(expected_wn_to, actual_wn_to)

        # Param: water_link_flow_transport_time_hours
        expected_tr_time = {
            "Water_Link_12": 1,
            "Water_Link_23": 2,
        }
        actual_tr_time = {
            wl: instance.water_link_flow_transport_time_hours[wl]
            for wl in instance.WATER_LINKS
        }
        self.assertDictEqual(expected_tr_time, actual_tr_time)

        # Param: allow_water_link_min_flow_violation
        expected_allow_min = {
            "Water_Link_12": 1,
            "Water_Link_23": 0,
        }
        actual_allow_min = {
            wl: instance.allow_water_link_min_flow_violation[wl]
            for wl in instance.WATER_LINKS
        }
        self.assertDictEqual(expected_allow_min, actual_allow_min)

        # Param: min_flow_violation_penalty_cost
        expected_min_v = {
            "Water_Link_12": 100,
            "Water_Link_23": 0,
        }
        actual_min_v = {
            wl: instance.min_flow_violation_penalty_cost[wl]
            for wl in instance.WATER_LINKS
        }
        self.assertDictEqual(expected_min_v, actual_min_v)

        # Param: allow_water_link_max_flow_violation
        expected_allow_max = {
            "Water_Link_12": 0,
            "Water_Link_23": 1,
        }
        actual_allow_max = {
            wl: instance.allow_water_link_max_flow_violation[wl]
            for wl in instance.WATER_LINKS
        }
        self.assertDictEqual(expected_allow_max, actual_allow_max)

        # Param: max_flow_violation_penalty_cost
        expected_max_v = {
            "Water_Link_12": 0,
            "Water_Link_23": 100,
        }
        actual_max_v = {
            wl: instance.max_flow_violation_penalty_cost[wl]
            for wl in instance.WATER_LINKS
        }
        self.assertDictEqual(expected_max_v, actual_max_v)
