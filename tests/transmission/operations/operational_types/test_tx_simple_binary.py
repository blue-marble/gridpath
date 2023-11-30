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
    "transmission",
    "transmission.capacity",
    "transmission.capacity.capacity_types",
    "transmission.capacity.capacity",
    "transmission.availability.availability",
]
NAME_OF_MODULE_BEING_TESTED = (
    "transmission.operations.operational_types.tx_simple_binary"
)

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


class TestTxSimpleBinary(unittest.TestCase):
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

        # Set: TX_SIMPLE
        expected_tx = sorted(["Tx_binary_1"])
        actual_tx = sorted(instance.TX_SIMPLE_BINARY)
        self.assertListEqual(expected_tx, actual_tx)

        # Set: TX_SIMPLE_OPR_TMPS
        expect_tx_op_tmp = sorted(
            [
                ("Tx_binary_1", 20200101),
                ("Tx_binary_1", 20200102),
                ("Tx_binary_1", 20200103),
                ("Tx_binary_1", 20200104),
                ("Tx_binary_1", 20200105),
                ("Tx_binary_1", 20200106),
                ("Tx_binary_1", 20200107),
                ("Tx_binary_1", 20200108),
                ("Tx_binary_1", 20200109),
                ("Tx_binary_1", 20200110),
                ("Tx_binary_1", 20200111),
                ("Tx_binary_1", 20200112),
                ("Tx_binary_1", 20200113),
                ("Tx_binary_1", 20200114),
                ("Tx_binary_1", 20200115),
                ("Tx_binary_1", 20200116),
                ("Tx_binary_1", 20200117),
                ("Tx_binary_1", 20200118),
                ("Tx_binary_1", 20200119),
                ("Tx_binary_1", 20200120),
                ("Tx_binary_1", 20200121),
                ("Tx_binary_1", 20200122),
                ("Tx_binary_1", 20200123),
                ("Tx_binary_1", 20200124),
                ("Tx_binary_1", 20200201),
                ("Tx_binary_1", 20200202),
                ("Tx_binary_1", 20200203),
                ("Tx_binary_1", 20200204),
                ("Tx_binary_1", 20200205),
                ("Tx_binary_1", 20200206),
                ("Tx_binary_1", 20200207),
                ("Tx_binary_1", 20200208),
                ("Tx_binary_1", 20200209),
                ("Tx_binary_1", 20200210),
                ("Tx_binary_1", 20200211),
                ("Tx_binary_1", 20200212),
                ("Tx_binary_1", 20200213),
                ("Tx_binary_1", 20200214),
                ("Tx_binary_1", 20200215),
                ("Tx_binary_1", 20200216),
                ("Tx_binary_1", 20200217),
                ("Tx_binary_1", 20200218),
                ("Tx_binary_1", 20200219),
                ("Tx_binary_1", 20200220),
                ("Tx_binary_1", 20200221),
                ("Tx_binary_1", 20200222),
                ("Tx_binary_1", 20200223),
                ("Tx_binary_1", 20200224),
                ("Tx_binary_1", 20300101),
                ("Tx_binary_1", 20300102),
                ("Tx_binary_1", 20300103),
                ("Tx_binary_1", 20300104),
                ("Tx_binary_1", 20300105),
                ("Tx_binary_1", 20300106),
                ("Tx_binary_1", 20300107),
                ("Tx_binary_1", 20300108),
                ("Tx_binary_1", 20300109),
                ("Tx_binary_1", 20300110),
                ("Tx_binary_1", 20300111),
                ("Tx_binary_1", 20300112),
                ("Tx_binary_1", 20300113),
                ("Tx_binary_1", 20300114),
                ("Tx_binary_1", 20300115),
                ("Tx_binary_1", 20300116),
                ("Tx_binary_1", 20300117),
                ("Tx_binary_1", 20300118),
                ("Tx_binary_1", 20300119),
                ("Tx_binary_1", 20300120),
                ("Tx_binary_1", 20300121),
                ("Tx_binary_1", 20300122),
                ("Tx_binary_1", 20300123),
                ("Tx_binary_1", 20300124),
                ("Tx_binary_1", 20300201),
                ("Tx_binary_1", 20300202),
                ("Tx_binary_1", 20300203),
                ("Tx_binary_1", 20300204),
                ("Tx_binary_1", 20300205),
                ("Tx_binary_1", 20300206),
                ("Tx_binary_1", 20300207),
                ("Tx_binary_1", 20300208),
                ("Tx_binary_1", 20300209),
                ("Tx_binary_1", 20300210),
                ("Tx_binary_1", 20300211),
                ("Tx_binary_1", 20300212),
                ("Tx_binary_1", 20300213),
                ("Tx_binary_1", 20300214),
                ("Tx_binary_1", 20300215),
                ("Tx_binary_1", 20300216),
                ("Tx_binary_1", 20300217),
                ("Tx_binary_1", 20300218),
                ("Tx_binary_1", 20300219),
                ("Tx_binary_1", 20300220),
                ("Tx_binary_1", 20300221),
                ("Tx_binary_1", 20300222),
                ("Tx_binary_1", 20300223),
                ("Tx_binary_1", 20300224),
            ]
        )
        actual_tx_op_tmp = sorted(
            [(tx, tmp) for (tx, tmp) in instance.TX_SIMPLE_BINARY_OPR_TMPS]
        )
        self.assertListEqual(expect_tx_op_tmp, actual_tx_op_tmp)

        # Param: tx_simple_binary_loss_factor
        expected_lf = OrderedDict(sorted({"Tx_binary_1": 0}.items()))
        actual_lf = OrderedDict(
            sorted(
                {
                    tx: instance.tx_simple_binary_loss_factor[tx]
                    for tx in instance.TX_SIMPLE_BINARY
                }.items()
            )
        )
        self.assertDictEqual(expected_lf, actual_lf)


if __name__ == "__main__":
    unittest.main()
