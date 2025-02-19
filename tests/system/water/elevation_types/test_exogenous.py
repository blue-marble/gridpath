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

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

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
    # "system.water.reservoirs",
]
# Components added based on elevation_type by system.water.reservoirs module
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


class TestExogenousElevationType(unittest.TestCase):
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

        # Param: reservoir_exogenous_elevation
        expected_te = {
            ("Water_Node_1", 20200101): 1100,
            ("Water_Node_1", 20200102): 1100,
            ("Water_Node_1", 20200103): 1100,
            ("Water_Node_1", 20200104): 1100,
            ("Water_Node_1", 20200105): 1100,
            ("Water_Node_1", 20200106): 1100,
            ("Water_Node_1", 20200107): 1100,
            ("Water_Node_1", 20200108): 1100,
            ("Water_Node_1", 20200109): 1100,
            ("Water_Node_1", 20200110): 1100,
            ("Water_Node_1", 20200111): 1100,
            ("Water_Node_1", 20200112): 1100,
            ("Water_Node_1", 20200113): 1100,
            ("Water_Node_1", 20200114): 1100,
            ("Water_Node_1", 20200115): 1100,
            ("Water_Node_1", 20200116): 1100,
            ("Water_Node_1", 20200117): 1100,
            ("Water_Node_1", 20200118): 1100,
            ("Water_Node_1", 20200119): 1100,
            ("Water_Node_1", 20200120): 1100,
            ("Water_Node_1", 20200121): 1100,
            ("Water_Node_1", 20200122): 1100,
            ("Water_Node_1", 20200123): 1100,
            ("Water_Node_1", 20200124): 1100,
            ("Water_Node_1", 20200201): 1100,
            ("Water_Node_1", 20200202): 1100,
            ("Water_Node_1", 20200203): 1100,
            ("Water_Node_1", 20200204): 1100,
            ("Water_Node_1", 20200205): 1100,
            ("Water_Node_1", 20200206): 1100,
            ("Water_Node_1", 20200207): 1100,
            ("Water_Node_1", 20200208): 1100,
            ("Water_Node_1", 20200209): 1100,
            ("Water_Node_1", 20200210): 1100,
            ("Water_Node_1", 20200211): 1100,
            ("Water_Node_1", 20200212): 1100,
            ("Water_Node_1", 20200213): 1100,
            ("Water_Node_1", 20200214): 1100,
            ("Water_Node_1", 20200215): 1100,
            ("Water_Node_1", 20200216): 1100,
            ("Water_Node_1", 20200217): 1100,
            ("Water_Node_1", 20200218): 1100,
            ("Water_Node_1", 20200219): 1100,
            ("Water_Node_1", 20200220): 1100,
            ("Water_Node_1", 20200221): 1100,
            ("Water_Node_1", 20200222): 1100,
            ("Water_Node_1", 20200223): 1100,
            ("Water_Node_1", 20200224): 1100,
            ("Water_Node_1", 20300101): 1100,
            ("Water_Node_1", 20300102): 1100,
            ("Water_Node_1", 20300103): 1100,
            ("Water_Node_1", 20300104): 1100,
            ("Water_Node_1", 20300105): 1100,
            ("Water_Node_1", 20300106): 1100,
            ("Water_Node_1", 20300107): 1100,
            ("Water_Node_1", 20300108): 1100,
            ("Water_Node_1", 20300109): 1100,
            ("Water_Node_1", 20300110): 1100,
            ("Water_Node_1", 20300111): 1100,
            ("Water_Node_1", 20300112): 1100,
            ("Water_Node_1", 20300113): 1100,
            ("Water_Node_1", 20300114): 1100,
            ("Water_Node_1", 20300115): 1100,
            ("Water_Node_1", 20300116): 1100,
            ("Water_Node_1", 20300117): 1100,
            ("Water_Node_1", 20300118): 1100,
            ("Water_Node_1", 20300119): 1100,
            ("Water_Node_1", 20300120): 1100,
            ("Water_Node_1", 20300121): 1100,
            ("Water_Node_1", 20300122): 1100,
            ("Water_Node_1", 20300123): 1100,
            ("Water_Node_1", 20300124): 1100,
            ("Water_Node_1", 20300201): 1100,
            ("Water_Node_1", 20300202): 1100,
            ("Water_Node_1", 20300203): 1100,
            ("Water_Node_1", 20300204): 1100,
            ("Water_Node_1", 20300205): 1100,
            ("Water_Node_1", 20300206): 1100,
            ("Water_Node_1", 20300207): 1100,
            ("Water_Node_1", 20300208): 1100,
            ("Water_Node_1", 20300209): 1100,
            ("Water_Node_1", 20300210): 1100,
            ("Water_Node_1", 20300211): 1100,
            ("Water_Node_1", 20300212): 1100,
            ("Water_Node_1", 20300213): 1100,
            ("Water_Node_1", 20300214): 1100,
            ("Water_Node_1", 20300215): 1100,
            ("Water_Node_1", 20300216): 1100,
            ("Water_Node_1", 20300217): 1100,
            ("Water_Node_1", 20300218): 1100,
            ("Water_Node_1", 20300219): 1100,
            ("Water_Node_1", 20300220): 1100,
            ("Water_Node_1", 20300221): 1100,
            ("Water_Node_1", 20300222): 1100,
            ("Water_Node_1", 20300223): 1100,
            ("Water_Node_1", 20300224): 1100,
        }

        actual_te = {
            (r, tmp): instance.reservoir_exogenous_elevation[r, tmp]
            for r in instance.EXOG_ELEV_WATER_NODES_W_RESERVOIRS
            for tmp in instance.TMPS
        }

        self.assertDictEqual(expected_te, actual_te)
