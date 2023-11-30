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
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = ["geography.load_zones"]
NAME_OF_MODULE_BEING_TESTED = "transmission"
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


class TestTransmissionInit(unittest.TestCase):
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

        # Set: TX_LINES
        expected_tx_lines = sorted(["Tx1", "Tx2", "Tx3", "Tx_New", "Tx_binary_1"])
        actual_tx_lines = sorted([tx for tx in instance.TX_LINES])
        self.assertListEqual(expected_tx_lines, actual_tx_lines)

        # Param: tx_capacity_type
        expected_cap_type = OrderedDict(
            sorted(
                {
                    "Tx1": "tx_spec",
                    "Tx_New": "tx_new_lin",
                    "Tx2": "tx_spec",
                    "Tx3": "tx_spec",
                    "Tx_binary_1": "tx_spec",
                }.items()
            )
        )
        actual_cap_type = OrderedDict(
            sorted(
                {tx: instance.tx_capacity_type[tx] for tx in instance.TX_LINES}.items()
            )
        )
        self.assertDictEqual(expected_cap_type, actual_cap_type)

        # Param: tx_availability_type
        expected_cap_type = OrderedDict(
            sorted(
                {
                    "Tx1": "exogenous",
                    "Tx_New": "exogenous",
                    "Tx2": "exogenous_monthly",
                    "Tx3": "exogenous",
                    "Tx_binary_1": "exogenous",
                }.items()
            )
        )
        actual_cap_type = OrderedDict(
            sorted(
                {
                    tx: instance.tx_availability_type[tx] for tx in instance.TX_LINES
                }.items()
            )
        )
        self.assertDictEqual(expected_cap_type, actual_cap_type)

        # Param: load_zone_from
        expected_load_zone_from = OrderedDict(
            sorted(
                {
                    "Tx1": "Zone1",
                    "Tx_New": "Zone1",
                    "Tx2": "Zone1",
                    "Tx3": "Zone2",
                    "Tx_binary_1": "Zone1",
                }.items()
            )
        )
        actual_load_zone_from = OrderedDict(
            sorted(
                {tx: instance.load_zone_from[tx] for tx in instance.TX_LINES}.items()
            )
        )
        self.assertDictEqual(expected_load_zone_from, actual_load_zone_from)

        # Param: load_zone_to
        expected_load_zone_to = OrderedDict(
            sorted(
                {
                    "Tx1": "Zone2",
                    "Tx_New": "Zone2",
                    "Tx2": "Zone3",
                    "Tx3": "Zone3",
                    "Tx_binary_1": "Zone2",
                }.items()
            )
        )
        actual_load_zone_to = OrderedDict(
            sorted({tx: instance.load_zone_to[tx] for tx in instance.TX_LINES}.items())
        )
        self.assertDictEqual(expected_load_zone_to, actual_load_zone_to)


if __name__ == "__main__":
    unittest.main()
