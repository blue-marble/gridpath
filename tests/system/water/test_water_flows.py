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
NAME_OF_MODULE_BEING_TESTED = "system.water.water_flows"
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


class TestWaterFlows(unittest.TestCase):
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

        # Param: min_flow_vol_per_second
        df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "water_flow_bounds.tab"),
            sep="\t",
        )

        # Check that no values are getting the default value of 0
        df = df.replace(".", 0)
        df["min_flow_vol_per_second"] = pd.to_numeric(df["min_flow_vol_per_second"])

        expected_min_bound = df.set_index(["water_link", "timepoint"]).to_dict()[
            "min_flow_vol_per_second"
        ]
        actual_min_bound = {
            (wl, tmp): instance.min_flow_vol_per_second[wl, tmp]
            for wl in instance.WATER_LINKS
            for tmp in instance.TMPS
        }
        self.assertDictEqual(expected_min_bound, actual_min_bound)

        # Param: max_flow_vol_per_second
        df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "water_flow_bounds.tab"),
            sep="\t",
        )

        # Check that no values are getting the default value of infinity
        df = df.replace(".", float("inf"))
        df["max_flow_vol_per_second"] = pd.to_numeric(df["max_flow_vol_per_second"])

        expected_max_bound = df.set_index(["water_link", "timepoint"]).to_dict()[
            "max_flow_vol_per_second"
        ]
        actual_max_bound = {
            (wl, tmp): instance.max_flow_vol_per_second[wl, tmp]
            for wl in instance.WATER_LINKS
            for tmp in instance.TMPS
        }
        self.assertDictEqual(expected_max_bound, actual_max_bound)

        # Set: WATER_LINK_DEPARTURE_ARRIVAL_TMPS
        expected_wl_dp_arr_tmp = sorted(
            [
                ("Water_Link_12", 20200101, 20200102),
                ("Water_Link_12", 20200102, 20200103),
                ("Water_Link_12", 20200103, 20200104),
                ("Water_Link_12", 20200104, 20200105),
                ("Water_Link_12", 20200105, 20200106),
                ("Water_Link_12", 20200106, 20200107),
                ("Water_Link_12", 20200107, 20200108),
                ("Water_Link_12", 20200108, 20200109),
                ("Water_Link_12", 20200109, 20200110),
                ("Water_Link_12", 20200110, 20200111),
                ("Water_Link_12", 20200111, 20200112),
                ("Water_Link_12", 20200112, 20200113),
                ("Water_Link_12", 20200113, 20200114),
                ("Water_Link_12", 20200114, 20200115),
                ("Water_Link_12", 20200115, 20200116),
                ("Water_Link_12", 20200116, 20200117),
                ("Water_Link_12", 20200117, 20200119),
                ("Water_Link_12", 20200118, 20200121),
                ("Water_Link_12", 20200119, 20200121),
                ("Water_Link_12", 20200120, 20200121),
                ("Water_Link_12", 20200121, 20200122),
                ("Water_Link_12", 20200122, 20200101),
                ("Water_Link_12", 20200123, 20200102),
                ("Water_Link_12", 20200124, 20200102),
                ("Water_Link_12", 20200201, 20200202),
                ("Water_Link_12", 20200202, 20200203),
                ("Water_Link_12", 20200203, 20200204),
                ("Water_Link_12", 20200204, 20200205),
                ("Water_Link_12", 20200205, 20200206),
                ("Water_Link_12", 20200206, 20200207),
                ("Water_Link_12", 20200207, 20200208),
                ("Water_Link_12", 20200208, 20200209),
                ("Water_Link_12", 20200209, 20200210),
                ("Water_Link_12", 20200210, 20200211),
                ("Water_Link_12", 20200211, 20200212),
                ("Water_Link_12", 20200212, 20200213),
                ("Water_Link_12", 20200213, 20200214),
                ("Water_Link_12", 20200214, 20200215),
                ("Water_Link_12", 20200215, 20200216),
                ("Water_Link_12", 20200216, 20200217),
                ("Water_Link_12", 20200217, 20200218),
                ("Water_Link_12", 20200218, 20200219),
                ("Water_Link_12", 20200219, 20200220),
                ("Water_Link_12", 20200220, 20200221),
                ("Water_Link_12", 20200221, 20200222),
                ("Water_Link_12", 20200222, 20200223),
                ("Water_Link_12", 20200223, 20200224),
                ("Water_Link_12", 20300101, 20300102),
                ("Water_Link_12", 20300102, 20300103),
                ("Water_Link_12", 20300103, 20300104),
                ("Water_Link_12", 20300104, 20300105),
                ("Water_Link_12", 20300105, 20300106),
                ("Water_Link_12", 20300106, 20300107),
                ("Water_Link_12", 20300107, 20300108),
                ("Water_Link_12", 20300108, 20300109),
                ("Water_Link_12", 20300109, 20300110),
                ("Water_Link_12", 20300110, 20300111),
                ("Water_Link_12", 20300111, 20300112),
                ("Water_Link_12", 20300112, 20300113),
                ("Water_Link_12", 20300113, 20300114),
                ("Water_Link_12", 20300114, 20300115),
                ("Water_Link_12", 20300115, 20300116),
                ("Water_Link_12", 20300116, 20300117),
                ("Water_Link_12", 20300117, 20300118),
                ("Water_Link_12", 20300118, 20300119),
                ("Water_Link_12", 20300119, 20300120),
                ("Water_Link_12", 20300120, 20300121),
                ("Water_Link_12", 20300121, 20300122),
                ("Water_Link_12", 20300122, 20300123),
                ("Water_Link_12", 20300123, 20300124),
                ("Water_Link_12", 20300124, 20300101),
                ("Water_Link_12", 20300201, 20300202),
                ("Water_Link_12", 20300202, 20300203),
                ("Water_Link_12", 20300203, 20300204),
                ("Water_Link_12", 20300204, 20300205),
                ("Water_Link_12", 20300205, 20300206),
                ("Water_Link_12", 20300206, 20300207),
                ("Water_Link_12", 20300207, 20300208),
                ("Water_Link_12", 20300208, 20300209),
                ("Water_Link_12", 20300209, 20300210),
                ("Water_Link_12", 20300210, 20300211),
                ("Water_Link_12", 20300211, 20300212),
                ("Water_Link_12", 20300212, 20300213),
                ("Water_Link_12", 20300213, 20300214),
                ("Water_Link_12", 20300214, 20300215),
                ("Water_Link_12", 20300215, 20300216),
                ("Water_Link_12", 20300216, 20300217),
                ("Water_Link_12", 20300217, 20300218),
                ("Water_Link_12", 20300218, 20300219),
                ("Water_Link_12", 20300219, 20300220),
                ("Water_Link_12", 20300220, 20300221),
                ("Water_Link_12", 20300221, 20300222),
                ("Water_Link_12", 20300222, 20300223),
                ("Water_Link_12", 20300223, 20300224),
                ("Water_Link_23", 20200101, 20200103),
                ("Water_Link_23", 20200102, 20200103),
                ("Water_Link_23", 20200103, 20200105),
                ("Water_Link_23", 20200104, 20200106),
                ("Water_Link_23", 20200105, 20200107),
                ("Water_Link_23", 20200106, 20200108),
                ("Water_Link_23", 20200107, 20200109),
                ("Water_Link_23", 20200108, 20200110),
                ("Water_Link_23", 20200109, 20200111),
                ("Water_Link_23", 20200110, 20200112),
                ("Water_Link_23", 20200111, 20200113),
                ("Water_Link_23", 20200112, 20200114),
                ("Water_Link_23", 20200113, 20200115),
                ("Water_Link_23", 20200114, 20200116),
                ("Water_Link_23", 20200115, 20200116),
                ("Water_Link_23", 20200116, 20200118),
                ("Water_Link_23", 20200117, 20200121),
                ("Water_Link_23", 20200118, 20200121),
                ("Water_Link_23", 20200119, 20200121),
                ("Water_Link_23", 20200120, 20200121),
                ("Water_Link_23", 20200121, 20200101),
                ("Water_Link_23", 20200122, 20200102),
                ("Water_Link_23", 20200123, 20200103),
                ("Water_Link_23", 20200124, 20200103),
                ("Water_Link_23", 20200201, 20200203),
                ("Water_Link_23", 20200202, 20200204),
                ("Water_Link_23", 20200203, 20200205),
                ("Water_Link_23", 20200204, 20200206),
                ("Water_Link_23", 20200205, 20200207),
                ("Water_Link_23", 20200206, 20200208),
                ("Water_Link_23", 20200207, 20200209),
                ("Water_Link_23", 20200208, 20200210),
                ("Water_Link_23", 20200209, 20200211),
                ("Water_Link_23", 20200210, 20200212),
                ("Water_Link_23", 20200211, 20200213),
                ("Water_Link_23", 20200212, 20200214),
                ("Water_Link_23", 20200213, 20200215),
                ("Water_Link_23", 20200214, 20200216),
                ("Water_Link_23", 20200215, 20200217),
                ("Water_Link_23", 20200216, 20200218),
                ("Water_Link_23", 20200217, 20200219),
                ("Water_Link_23", 20200218, 20200220),
                ("Water_Link_23", 20200219, 20200221),
                ("Water_Link_23", 20200220, 20200222),
                ("Water_Link_23", 20200221, 20200223),
                ("Water_Link_23", 20200222, 20200224),
                ("Water_Link_23", 20200223, 20200224),
                ("Water_Link_23", 20300101, 20300103),
                ("Water_Link_23", 20300102, 20300104),
                ("Water_Link_23", 20300103, 20300105),
                ("Water_Link_23", 20300104, 20300106),
                ("Water_Link_23", 20300105, 20300107),
                ("Water_Link_23", 20300106, 20300108),
                ("Water_Link_23", 20300107, 20300109),
                ("Water_Link_23", 20300108, 20300110),
                ("Water_Link_23", 20300109, 20300111),
                ("Water_Link_23", 20300110, 20300112),
                ("Water_Link_23", 20300111, 20300113),
                ("Water_Link_23", 20300112, 20300114),
                ("Water_Link_23", 20300113, 20300115),
                ("Water_Link_23", 20300114, 20300116),
                ("Water_Link_23", 20300115, 20300117),
                ("Water_Link_23", 20300116, 20300118),
                ("Water_Link_23", 20300117, 20300119),
                ("Water_Link_23", 20300118, 20300120),
                ("Water_Link_23", 20300119, 20300121),
                ("Water_Link_23", 20300120, 20300122),
                ("Water_Link_23", 20300121, 20300123),
                ("Water_Link_23", 20300122, 20300124),
                ("Water_Link_23", 20300123, 20300101),
                ("Water_Link_23", 20300124, 20300102),
                ("Water_Link_23", 20300201, 20300203),
                ("Water_Link_23", 20300202, 20300204),
                ("Water_Link_23", 20300203, 20300205),
                ("Water_Link_23", 20300204, 20300206),
                ("Water_Link_23", 20300205, 20300207),
                ("Water_Link_23", 20300206, 20300208),
                ("Water_Link_23", 20300207, 20300209),
                ("Water_Link_23", 20300208, 20300210),
                ("Water_Link_23", 20300209, 20300211),
                ("Water_Link_23", 20300210, 20300212),
                ("Water_Link_23", 20300211, 20300213),
                ("Water_Link_23", 20300212, 20300214),
                ("Water_Link_23", 20300213, 20300215),
                ("Water_Link_23", 20300214, 20300216),
                ("Water_Link_23", 20300215, 20300217),
                ("Water_Link_23", 20300216, 20300218),
                ("Water_Link_23", 20300217, 20300219),
                ("Water_Link_23", 20300218, 20300220),
                ("Water_Link_23", 20300219, 20300221),
                ("Water_Link_23", 20300220, 20300222),
                ("Water_Link_23", 20300221, 20300223),
                ("Water_Link_23", 20300222, 20300224),
                ("Water_Link_23", 20300223, 20300224),
            ]
        )
        actual_wl_dp_arr_tmp = sorted(
            [
                (wl, dep_tmp, arr_tmp)
                for (wl, dep_tmp, arr_tmp) in instance.WATER_LINK_DEPARTURE_ARRIVAL_TMPS
            ]
        )

        print(actual_wl_dp_arr_tmp)
        self.assertListEqual(expected_wl_dp_arr_tmp, actual_wl_dp_arr_tmp)
