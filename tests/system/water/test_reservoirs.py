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

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.water_network",
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

        # Set: RESERVOIR_NODES
        expected_r_n = sorted(
            [
                ("Reservoir1", "Water_Node_1"),
                ("Reservoir2", "Water_Node_2"),
                ("Reservoir3", "Water_Node_3"),
            ]
        )
        actual_r_n = sorted([(r, n) for (r, n) in instance.RESERVOIR_NODES])

        self.assertListEqual(expected_r_n, actual_r_n)

        # Set: RESERVOIRS
        expected_r = sorted(
            [
                "Reservoir1",
                "Reservoir2",
                "Reservoir3",
            ]
        )
        actual_r = sorted([r for r in instance.RESERVOIRS])

        self.assertListEqual(expected_r, actual_r)

        # Set: RESERVOIRS_BY_NODE
        expected_r_by_n = {
            "Water_Node_1": sorted(["Reservoir1"]),
            "Water_Node_2": sorted(["Reservoir2"]),
            "Water_Node_3": sorted(["Reservoir3"]),
        }

        actual_r_by_n = {
            n: sorted([r for r in list(instance.RESERVOIRS_BY_NODE[n])])
            for n in instance.RESERVOIRS_BY_NODE.keys()
        }

        self.assertDictEqual(expected_r_by_n, actual_r_by_n)

        # Set: RESERVOIR_TMPS_W_TARGET_ELEVATION
        expected_r_tmp = [
            ("Reservoir1", 20200101),
            ("Reservoir2", 20200101),
            ("Reservoir3", 20200101),
        ]

        actual_r_tmp = sorted(
            [(r, tmp) for (r, tmp) in instance.RESERVOIR_TMPS_W_TARGET_ELEVATION]
        )

        self.assertListEqual(expected_r_tmp, actual_r_tmp)

        # Param: balancing_type_reservoir
        expected_bt = {
            "Reservoir1": "day",
            "Reservoir2": "day",
            "Reservoir3": "day",
        }
        actual_bt = {
            r: instance.balancing_type_reservoir[r] for r in instance.RESERVOIRS
        }
        self.assertDictEqual(expected_bt, actual_bt)

        # Param: reservoir_target_elevation
        expected_te = {
            ("Reservoir1", 20200101): 1100,
            ("Reservoir2", 20200101): 750,
            ("Reservoir3", 20200101): 550,
        }
        actual_te = {
            (r, tmp): instance.reservoir_target_elevation[r, tmp]
            for (r, tmp) in instance.RESERVOIR_TMPS_W_TARGET_ELEVATION
        }
        self.assertDictEqual(expected_te, actual_te)

        # Param: maximum_elevation_elevationunit
        expected_maxe = {
            "Reservoir1": 1200,
            "Reservoir2": 800,
            "Reservoir3": 600,
        }
        actual_maxe = {
            r: instance.maximum_elevation_elevationunit[r] for r in instance.RESERVOIRS
        }
        self.assertDictEqual(expected_maxe, actual_maxe)

        # Param: minimum_elevation_elevationunit
        expected_mine = {
            "Reservoir1": 1000,
            "Reservoir2": 700,
            "Reservoir3": 500,
        }
        actual_mine = {
            r: instance.minimum_elevation_elevationunit[r] for r in instance.RESERVOIRS
        }
        self.assertDictEqual(expected_mine, actual_mine)

        # Param: volume_to_elevation_conversion_coefficient
        expected_vtoe = {
            "Reservoir1": 0.01,
            "Reservoir2": 0.1,
            "Reservoir3": 0.15,
        }
        actual_vtoe = {
            r: instance.volume_to_elevation_conversion_coefficient[r]
            for r in instance.RESERVOIRS
        }
        self.assertDictEqual(expected_vtoe, actual_vtoe)

        # Param: max_spill
        expected_maxspill = {
            "Reservoir1": 100000,
            "Reservoir2": 100000,
            "Reservoir3": 100000,
        }
        actual_maxspill = {r: instance.max_spill[r] for r in instance.RESERVOIRS}
        self.assertDictEqual(expected_maxspill, actual_maxspill)

        # Param: evaporation_coefficient
        expected_evap = {
            "Reservoir1": 0.1,
            "Reservoir2": 0.1,
            "Reservoir3": 0.1,
        }
        actual_evap = {
            r: instance.evaporation_coefficient[r] for r in instance.RESERVOIRS
        }
        self.assertDictEqual(expected_evap, actual_evap)
