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
NAME_OF_MODULE_BEING_TESTED = "transmission.operations.operational_types.tx_dcopf"

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


class TestTxOperations(unittest.TestCase):
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

        # Set: TX_DCOPF
        expected_tx = sorted(["Tx1", "Tx2", "Tx3"])
        actual_tx = sorted(instance.TX_DCOPF)
        self.assertListEqual(expected_tx, actual_tx)

        # Set: TX_DCOPF_OPR_TMPS
        expect_tx_op_tmp = sorted(
            [
                ("Tx1", 20200101),
                ("Tx1", 20200102),
                ("Tx1", 20200103),
                ("Tx1", 20200104),
                ("Tx1", 20200105),
                ("Tx1", 20200106),
                ("Tx1", 20200107),
                ("Tx1", 20200108),
                ("Tx1", 20200109),
                ("Tx1", 20200110),
                ("Tx1", 20200111),
                ("Tx1", 20200112),
                ("Tx1", 20200113),
                ("Tx1", 20200114),
                ("Tx1", 20200115),
                ("Tx1", 20200116),
                ("Tx1", 20200117),
                ("Tx1", 20200118),
                ("Tx1", 20200119),
                ("Tx1", 20200120),
                ("Tx1", 20200121),
                ("Tx1", 20200122),
                ("Tx1", 20200123),
                ("Tx1", 20200124),
                ("Tx1", 20200201),
                ("Tx1", 20200202),
                ("Tx1", 20200203),
                ("Tx1", 20200204),
                ("Tx1", 20200205),
                ("Tx1", 20200206),
                ("Tx1", 20200207),
                ("Tx1", 20200208),
                ("Tx1", 20200209),
                ("Tx1", 20200210),
                ("Tx1", 20200211),
                ("Tx1", 20200212),
                ("Tx1", 20200213),
                ("Tx1", 20200214),
                ("Tx1", 20200215),
                ("Tx1", 20200216),
                ("Tx1", 20200217),
                ("Tx1", 20200218),
                ("Tx1", 20200219),
                ("Tx1", 20200220),
                ("Tx1", 20200221),
                ("Tx1", 20200222),
                ("Tx1", 20200223),
                ("Tx1", 20200224),
                ("Tx1", 20300101),
                ("Tx1", 20300102),
                ("Tx1", 20300103),
                ("Tx1", 20300104),
                ("Tx1", 20300105),
                ("Tx1", 20300106),
                ("Tx1", 20300107),
                ("Tx1", 20300108),
                ("Tx1", 20300109),
                ("Tx1", 20300110),
                ("Tx1", 20300111),
                ("Tx1", 20300112),
                ("Tx1", 20300113),
                ("Tx1", 20300114),
                ("Tx1", 20300115),
                ("Tx1", 20300116),
                ("Tx1", 20300117),
                ("Tx1", 20300118),
                ("Tx1", 20300119),
                ("Tx1", 20300120),
                ("Tx1", 20300121),
                ("Tx1", 20300122),
                ("Tx1", 20300123),
                ("Tx1", 20300124),
                ("Tx1", 20300201),
                ("Tx1", 20300202),
                ("Tx1", 20300203),
                ("Tx1", 20300204),
                ("Tx1", 20300205),
                ("Tx1", 20300206),
                ("Tx1", 20300207),
                ("Tx1", 20300208),
                ("Tx1", 20300209),
                ("Tx1", 20300210),
                ("Tx1", 20300211),
                ("Tx1", 20300212),
                ("Tx1", 20300213),
                ("Tx1", 20300214),
                ("Tx1", 20300215),
                ("Tx1", 20300216),
                ("Tx1", 20300217),
                ("Tx1", 20300218),
                ("Tx1", 20300219),
                ("Tx1", 20300220),
                ("Tx1", 20300221),
                ("Tx1", 20300222),
                ("Tx1", 20300223),
                ("Tx1", 20300224),
                ("Tx2", 20200101),
                ("Tx2", 20200102),
                ("Tx2", 20200103),
                ("Tx2", 20200104),
                ("Tx2", 20200105),
                ("Tx2", 20200106),
                ("Tx2", 20200107),
                ("Tx2", 20200108),
                ("Tx2", 20200109),
                ("Tx2", 20200110),
                ("Tx2", 20200111),
                ("Tx2", 20200112),
                ("Tx2", 20200113),
                ("Tx2", 20200114),
                ("Tx2", 20200115),
                ("Tx2", 20200116),
                ("Tx2", 20200117),
                ("Tx2", 20200118),
                ("Tx2", 20200119),
                ("Tx2", 20200120),
                ("Tx2", 20200121),
                ("Tx2", 20200122),
                ("Tx2", 20200123),
                ("Tx2", 20200124),
                ("Tx2", 20200201),
                ("Tx2", 20200202),
                ("Tx2", 20200203),
                ("Tx2", 20200204),
                ("Tx2", 20200205),
                ("Tx2", 20200206),
                ("Tx2", 20200207),
                ("Tx2", 20200208),
                ("Tx2", 20200209),
                ("Tx2", 20200210),
                ("Tx2", 20200211),
                ("Tx2", 20200212),
                ("Tx2", 20200213),
                ("Tx2", 20200214),
                ("Tx2", 20200215),
                ("Tx2", 20200216),
                ("Tx2", 20200217),
                ("Tx2", 20200218),
                ("Tx2", 20200219),
                ("Tx2", 20200220),
                ("Tx2", 20200221),
                ("Tx2", 20200222),
                ("Tx2", 20200223),
                ("Tx2", 20200224),
                ("Tx2", 20300101),
                ("Tx2", 20300102),
                ("Tx2", 20300103),
                ("Tx2", 20300104),
                ("Tx2", 20300105),
                ("Tx2", 20300106),
                ("Tx2", 20300107),
                ("Tx2", 20300108),
                ("Tx2", 20300109),
                ("Tx2", 20300110),
                ("Tx2", 20300111),
                ("Tx2", 20300112),
                ("Tx2", 20300113),
                ("Tx2", 20300114),
                ("Tx2", 20300115),
                ("Tx2", 20300116),
                ("Tx2", 20300117),
                ("Tx2", 20300118),
                ("Tx2", 20300119),
                ("Tx2", 20300120),
                ("Tx2", 20300121),
                ("Tx2", 20300122),
                ("Tx2", 20300123),
                ("Tx2", 20300124),
                ("Tx2", 20300201),
                ("Tx2", 20300202),
                ("Tx2", 20300203),
                ("Tx2", 20300204),
                ("Tx2", 20300205),
                ("Tx2", 20300206),
                ("Tx2", 20300207),
                ("Tx2", 20300208),
                ("Tx2", 20300209),
                ("Tx2", 20300210),
                ("Tx2", 20300211),
                ("Tx2", 20300212),
                ("Tx2", 20300213),
                ("Tx2", 20300214),
                ("Tx2", 20300215),
                ("Tx2", 20300216),
                ("Tx2", 20300217),
                ("Tx2", 20300218),
                ("Tx2", 20300219),
                ("Tx2", 20300220),
                ("Tx2", 20300221),
                ("Tx2", 20300222),
                ("Tx2", 20300223),
                ("Tx2", 20300224),
                ("Tx3", 20200101),
                ("Tx3", 20200102),
                ("Tx3", 20200103),
                ("Tx3", 20200104),
                ("Tx3", 20200105),
                ("Tx3", 20200106),
                ("Tx3", 20200107),
                ("Tx3", 20200108),
                ("Tx3", 20200109),
                ("Tx3", 20200110),
                ("Tx3", 20200111),
                ("Tx3", 20200112),
                ("Tx3", 20200113),
                ("Tx3", 20200114),
                ("Tx3", 20200115),
                ("Tx3", 20200116),
                ("Tx3", 20200117),
                ("Tx3", 20200118),
                ("Tx3", 20200119),
                ("Tx3", 20200120),
                ("Tx3", 20200121),
                ("Tx3", 20200122),
                ("Tx3", 20200123),
                ("Tx3", 20200124),
                ("Tx3", 20200201),
                ("Tx3", 20200202),
                ("Tx3", 20200203),
                ("Tx3", 20200204),
                ("Tx3", 20200205),
                ("Tx3", 20200206),
                ("Tx3", 20200207),
                ("Tx3", 20200208),
                ("Tx3", 20200209),
                ("Tx3", 20200210),
                ("Tx3", 20200211),
                ("Tx3", 20200212),
                ("Tx3", 20200213),
                ("Tx3", 20200214),
                ("Tx3", 20200215),
                ("Tx3", 20200216),
                ("Tx3", 20200217),
                ("Tx3", 20200218),
                ("Tx3", 20200219),
                ("Tx3", 20200220),
                ("Tx3", 20200221),
                ("Tx3", 20200222),
                ("Tx3", 20200223),
                ("Tx3", 20200224),
                ("Tx3", 20300101),
                ("Tx3", 20300102),
                ("Tx3", 20300103),
                ("Tx3", 20300104),
                ("Tx3", 20300105),
                ("Tx3", 20300106),
                ("Tx3", 20300107),
                ("Tx3", 20300108),
                ("Tx3", 20300109),
                ("Tx3", 20300110),
                ("Tx3", 20300111),
                ("Tx3", 20300112),
                ("Tx3", 20300113),
                ("Tx3", 20300114),
                ("Tx3", 20300115),
                ("Tx3", 20300116),
                ("Tx3", 20300117),
                ("Tx3", 20300118),
                ("Tx3", 20300119),
                ("Tx3", 20300120),
                ("Tx3", 20300121),
                ("Tx3", 20300122),
                ("Tx3", 20300123),
                ("Tx3", 20300124),
                ("Tx3", 20300201),
                ("Tx3", 20300202),
                ("Tx3", 20300203),
                ("Tx3", 20300204),
                ("Tx3", 20300205),
                ("Tx3", 20300206),
                ("Tx3", 20300207),
                ("Tx3", 20300208),
                ("Tx3", 20300209),
                ("Tx3", 20300210),
                ("Tx3", 20300211),
                ("Tx3", 20300212),
                ("Tx3", 20300213),
                ("Tx3", 20300214),
                ("Tx3", 20300215),
                ("Tx3", 20300216),
                ("Tx3", 20300217),
                ("Tx3", 20300218),
                ("Tx3", 20300219),
                ("Tx3", 20300220),
                ("Tx3", 20300221),
                ("Tx3", 20300222),
                ("Tx3", 20300223),
                ("Tx3", 20300224),
            ]
        )
        actual_tx_op_tmp = sorted(
            [(tx, tmp) for (tx, tmp) in instance.TX_DCOPF_OPR_TMPS]
        )
        self.assertListEqual(expect_tx_op_tmp, actual_tx_op_tmp)

        # Set: PRDS_CYCLES_ZONES
        expected_periods_cycles_zones = sorted(
            [
                (2020, 0, "Zone1"),
                (2020, 0, "Zone2"),
                (2020, 0, "Zone3"),
                (2030, 0, "Zone1"),
                (2030, 0, "Zone2"),
                (2030, 0, "Zone3"),
            ]
        )
        actual_periods_cycles_zones = sorted(
            [(p, c, z) for (p, c, z) in instance.PRDS_CYCLES_ZONES]
        )
        self.assertListEqual(expected_periods_cycles_zones, actual_periods_cycles_zones)

        # Set: ZONES_IN_PRD_CYCLE
        expected_zones = OrderedDict(
            sorted(
                {
                    (2020, 0): ["Zone1", "Zone2", "Zone3"],
                    (2030, 0): ["Zone1", "Zone2", "Zone3"],
                }.items()
            )
        )
        actual_zones = OrderedDict(
            sorted(
                {
                    (p, c): sorted([z for z in instance.ZONES_IN_PRD_CYCLE[(p, c)]])
                    for (p, c) in instance.PRDS_CYCLES
                }.items()
            )
        )
        self.assertDictEqual(expected_zones, actual_zones)

        # Set: PRDS_CYCLES
        expected_period_cycles = sorted([(2020, 0), (2030, 0)])
        actual_period_cycles = sorted([(p, c) for (p, c) in instance.PRDS_CYCLES])
        self.assertListEqual(expected_period_cycles, actual_period_cycles)

        # Set: PRDS_CYCLES_TX_DCOPF
        expected_cycles = sorted(
            [
                (2020, 0, "Tx1"),
                (2020, 0, "Tx2"),
                (2020, 0, "Tx3"),
                (2030, 0, "Tx1"),
                (2030, 0, "Tx2"),
                (2030, 0, "Tx3"),
            ]
        )
        actual_cycles = sorted(
            [(p, c, tx) for (p, c, tx) in instance.PRDS_CYCLES_TX_DCOPF]
        )
        self.assertListEqual(expected_cycles, actual_cycles)

        # Set: TX_DCOPF_IN_PRD_CYCLE
        expected_tx_lines = OrderedDict(
            sorted(
                {
                    (2020, 0): ["Tx1", "Tx2", "Tx3"],
                    (2030, 0): ["Tx1", "Tx2", "Tx3"],
                }.items()
            )
        )
        actual_tx_lines = OrderedDict(
            sorted(
                {
                    (p, c): sorted(
                        [tx for tx in instance.TX_DCOPF_IN_PRD_CYCLE[(p, c)]]
                    )
                    for (p, c) in instance.PRDS_CYCLES
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_lines, actual_tx_lines)

        # Set: CYCLES_OPR_TMPS
        expect_cycles_op_tmp = sorted(
            [
                (0, 20200101),
                (0, 20200102),
                (0, 20200103),
                (0, 20200104),
                (0, 20200105),
                (0, 20200106),
                (0, 20200107),
                (0, 20200108),
                (0, 20200109),
                (0, 20200110),
                (0, 20200111),
                (0, 20200112),
                (0, 20200113),
                (0, 20200114),
                (0, 20200115),
                (0, 20200116),
                (0, 20200117),
                (0, 20200118),
                (0, 20200119),
                (0, 20200120),
                (0, 20200121),
                (0, 20200122),
                (0, 20200123),
                (0, 20200124),
                (0, 20200201),
                (0, 20200202),
                (0, 20200203),
                (0, 20200204),
                (0, 20200205),
                (0, 20200206),
                (0, 20200207),
                (0, 20200208),
                (0, 20200209),
                (0, 20200210),
                (0, 20200211),
                (0, 20200212),
                (0, 20200213),
                (0, 20200214),
                (0, 20200215),
                (0, 20200216),
                (0, 20200217),
                (0, 20200218),
                (0, 20200219),
                (0, 20200220),
                (0, 20200221),
                (0, 20200222),
                (0, 20200223),
                (0, 20200224),
                (0, 20300101),
                (0, 20300102),
                (0, 20300103),
                (0, 20300104),
                (0, 20300105),
                (0, 20300106),
                (0, 20300107),
                (0, 20300108),
                (0, 20300109),
                (0, 20300110),
                (0, 20300111),
                (0, 20300112),
                (0, 20300113),
                (0, 20300114),
                (0, 20300115),
                (0, 20300116),
                (0, 20300117),
                (0, 20300118),
                (0, 20300119),
                (0, 20300120),
                (0, 20300121),
                (0, 20300122),
                (0, 20300123),
                (0, 20300124),
                (0, 20300201),
                (0, 20300202),
                (0, 20300203),
                (0, 20300204),
                (0, 20300205),
                (0, 20300206),
                (0, 20300207),
                (0, 20300208),
                (0, 20300209),
                (0, 20300210),
                (0, 20300211),
                (0, 20300212),
                (0, 20300213),
                (0, 20300214),
                (0, 20300215),
                (0, 20300216),
                (0, 20300217),
                (0, 20300218),
                (0, 20300219),
                (0, 20300220),
                (0, 20300221),
                (0, 20300222),
                (0, 20300223),
                (0, 20300224),
            ]
        )
        actual_cycles_op_tmp = sorted(
            [(c, tmp) for (c, tmp) in instance.CYCLES_OPR_TMPS]
        )
        self.assertListEqual(expect_cycles_op_tmp, actual_cycles_op_tmp)

        # Param: tx_dcopf_cycle_direction
        # Note: the direction of the cycle is random so we need to check both
        # directions (multiply by -1)
        expected_direction1 = OrderedDict(
            sorted(
                {
                    (2020, 0, "Tx1"): 1,
                    (2020, 0, "Tx2"): -1,
                    (2020, 0, "Tx3"): 1,
                    (2030, 0, "Tx1"): 1,
                    (2030, 0, "Tx2"): -1,
                    (2030, 0, "Tx3"): 1,
                }.items()
            )
        )
        expected_direction2 = OrderedDict(
            sorted(
                {
                    (2020, 0, "Tx1"): -1,
                    (2020, 0, "Tx2"): 1,
                    (2020, 0, "Tx3"): -1,
                    (2030, 0, "Tx1"): -1,
                    (2030, 0, "Tx2"): 1,
                    (2030, 0, "Tx3"): -1,
                }.items()
            )
        )

        actual_direction = OrderedDict(
            sorted(
                {
                    (p, c, tx): instance.tx_dcopf_cycle_direction[p, c, tx]
                    for (p, c, tx) in instance.PRDS_CYCLES_TX_DCOPF
                }.items()
            )
        )

        self.assertTrue(actual_direction in [expected_direction1, expected_direction2])

        # Param: tx_dcopf_reactance_ohms
        expected_reactance = OrderedDict(
            sorted({"Tx1": 0.5, "Tx2": 0.3, "Tx3": 0.4}.items())
        )
        actual_reactance = OrderedDict(
            sorted(
                {
                    tx: instance.tx_dcopf_reactance_ohms[tx] for tx in instance.TX_DCOPF
                }.items()
            )
        )
        self.assertDictEqual(expected_reactance, actual_reactance)


if __name__ == "__main__":
    unittest.main()
