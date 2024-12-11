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
]
NAME_OF_MODULE_BEING_TESTED = "system.water.water_nodes"
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


class TestWaterNodes(unittest.TestCase):
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

        # Set: WATER_NODES
        expected_wn = sorted(["Water_Node_1", "Water_Node_2", "Water_Node_3"])
        actual_wn = sorted([wn for wn in instance.WATER_NODES])
        self.assertListEqual(expected_wn, actual_wn)

        # Param: exogenous_water_inflow_rate_vol_per_sec
        df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "water_inflows.tab"),
            sep="\t",
        )

        # Check that no values are getting the default value of 0
        df = df.replace(".", 0)
        df["exogenous_water_inflow_rate_vol_per_sec"] = pd.to_numeric(
            df["exogenous_water_inflow_rate_vol_per_sec"]
        )

        expected_min_bound = df.set_index(["water_node", "timepoint"]).to_dict()[
            "exogenous_water_inflow_rate_vol_per_sec"
        ]
        actual_min_bound = {
            (wl, tmp): instance.exogenous_water_inflow_rate_vol_per_sec[wl, tmp]
            for wl in instance.WATER_NODES
            for tmp in instance.TMPS
        }
        self.assertDictEqual(expected_min_bound, actual_min_bound)

        # Set: WATER_LINKS_TO_BY_WATER_NODE
        expected_l = {
            "Water_Node_1": [],
            "Water_Node_2": ["Water_Link_12"],
            "Water_Node_3": ["Water_Link_23"],
        }
        actual_l = {
            wn: instance.WATER_LINKS_TO_BY_WATER_NODE[wn]
            for wn in instance.WATER_LINKS_TO_BY_WATER_NODE.keys()
        }
        self.assertDictEqual(expected_l, actual_l)

        # Set: WATER_LINKS_FROM_BY_WATER_NODE
        expected_l = {
            "Water_Node_1": ["Water_Link_12"],
            "Water_Node_2": ["Water_Link_23"],
            "Water_Node_3": [],
        }
        actual_l = {
            wn: instance.WATER_LINKS_FROM_BY_WATER_NODE[wn]
            for wn in instance.WATER_LINKS_FROM_BY_WATER_NODE.keys()
        }
        self.assertDictEqual(expected_l, actual_l)
