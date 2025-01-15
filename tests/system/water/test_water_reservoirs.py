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
]
NAME_OF_MODULE_BEING_TESTED = "system.water.reservoirs"
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


class TestReservoirs(unittest.TestCase):
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

        # Set: WATER_NODES_W_RESERVOIRS
        expected_r_n = sorted(["Water_Node_1", "Water_Node_2", "Water_Node_3"])
        actual_r_n = sorted([n for n in instance.WATER_NODES_W_RESERVOIRS])

        self.assertListEqual(expected_r_n, actual_r_n)

        # Set: WATER_NODE_WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME
        expected_r_tmp = [
            ("Water_Node_1", 20200101),
            ("Water_Node_2", 20200101),
            ("Water_Node_3", 20200101),
        ]

        actual_r_tmp = sorted(
            [
                (r, tmp)
                for (r, tmp) in instance.WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME
            ]
        )

        self.assertListEqual(expected_r_tmp, actual_r_tmp)

        # Param: balancing_type_reservoir
        expected_bt = {
            "Water_Node_1": "day",
            "Water_Node_2": "day",
            "Water_Node_3": "day",
        }
        actual_bt = {
            r: instance.balancing_type_reservoir[r]
            for r in instance.WATER_NODES_W_RESERVOIRS
        }
        self.assertDictEqual(expected_bt, actual_bt)

        # Param: reservoir_target_volume
        expected_te = {
            ("Water_Node_1", 20200101): 110000,
            ("Water_Node_2", 20200101): 7500,
            ("Water_Node_3", 20200101): 3600,
        }
        actual_te = {
            (r, tmp): instance.reservoir_target_volume[r, tmp]
            for (r, tmp) in instance.WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME
        }
        self.assertDictEqual(expected_te, actual_te)

        # Param: reservoir_target_release_avg_flow_volunit_per_sec
        expected_rt = {
            ("Water_Node_1", "day", 202001): 200,
            ("Water_Node_2", "day", 202001): 200,
            ("Water_Node_3", "day", 202001): 200,
        }
        actual_rt = {
            (r, bt, hrz): instance.reservoir_target_release_avg_flow_volunit_per_sec[
                r, bt, hrz
            ]
            for (
                r,
                bt,
                hrz,
            ) in instance.WATER_NODE_RESERVOIR_BT_HRZS_WITH_TOTAL_RELEASE_REQUIREMENTS
        }
        self.assertDictEqual(expected_rt, actual_rt)

        # Param: maximum_volume_volumeunit
        expected_maxe = {
            "Water_Node_1": 1200,
            "Water_Node_2": 800,
            "Water_Node_3": 600,
        }
        actual_maxe = {
            r: instance.maximum_volume_volumeunit[r]
            for r in instance.WATER_NODES_W_RESERVOIRS
        }
        self.assertDictEqual(expected_maxe, actual_maxe)

        # Param: minimum_volume_volumeunit
        expected_mine = {
            "Water_Node_1": 1000,
            "Water_Node_2": 700,
            "Water_Node_3": 500,
        }
        actual_mine = {
            r: instance.minimum_volume_volumeunit[r]
            for r in instance.WATER_NODES_W_RESERVOIRS
        }
        self.assertDictEqual(expected_mine, actual_mine)

        # Param: max_spill
        expected_maxspill = {
            "Water_Node_1": 100000,
            "Water_Node_2": 100000,
            "Water_Node_3": 100000,
        }
        actual_maxspill = {
            r: instance.max_spill[r] for r in instance.WATER_NODES_W_RESERVOIRS
        }
        self.assertDictEqual(expected_maxspill, actual_maxspill)

        # Param: evaporation_coefficient
        expected_evap = {
            "Water_Node_1": 0.1,
            "Water_Node_2": 0.1,
            "Water_Node_3": 0.1,
        }
        actual_evap = {
            r: instance.evaporation_coefficient[r]
            for r in instance.WATER_NODES_W_RESERVOIRS
        }
        self.assertDictEqual(expected_evap, actual_evap)
