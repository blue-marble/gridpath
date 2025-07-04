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

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "geography.carbon_cap_zones",
    "system.policy.carbon_cap.carbon_cap",
    "transmission",
    "transmission.capacity",
    "transmission.capacity.capacity_types",
    "transmission.capacity.capacity",
    "transmission.availability.availability",
    "transmission.operations.operational_types",
    "transmission.operations.operations",
]
NAME_OF_MODULE_BEING_TESTED = "transmission.operations.carbon_emissions"
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


class TestTxAggregateCarbonEmissions(unittest.TestCase):
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

        # Set: CRB_TX_LINES
        expected_tx_lines = sorted(["Tx1", "Tx_New"])
        actual_tx_lines = sorted(tx for tx in instance.CRB_TX_LINES)
        self.assertListEqual(expected_tx_lines, actual_tx_lines)

        # Param: tx_carbon_cap_zone
        expected_zone = OrderedDict(
            sorted({"Tx1": "Carbon_Cap_Zone1", "Tx_New": "Carbon_Cap_Zone1"}.items())
        )
        actual_zone = OrderedDict(
            sorted(
                {
                    tx: instance.tx_carbon_cap_zone[tx] for tx in instance.CRB_TX_LINES
                }.items()
            )
        )
        self.assertDictEqual(expected_zone, actual_zone)

        # Param: carbon_cap_zone_import_direction
        expected_dir = OrderedDict(
            sorted({"Tx1": "negative", "Tx_New": "negative"}.items())
        )
        actual_dir = OrderedDict(
            sorted(
                {
                    tx: instance.carbon_cap_zone_import_direction[tx]
                    for tx in instance.CRB_TX_LINES
                }.items()
            )
        )
        self.assertDictEqual(expected_dir, actual_dir)

        # Param: tx_co2_intensity_tons_per_mwh
        expected_co2 = OrderedDict(sorted({"Tx1": 0.6, "Tx_New": 0.8}.items()))
        actual_co2 = OrderedDict(
            sorted(
                {
                    tx: instance.tx_co2_intensity_tons_per_mwh[tx]
                    for tx in instance.CRB_TX_LINES
                }.items()
            )
        )
        self.assertDictEqual(expected_co2, actual_co2)

        # Set: CRB_TX_LINES_BY_CARBON_CAP_ZONE
        expected_tx_by_z = OrderedDict(
            sorted(
                {
                    "Carbon_Cap_Zone1": sorted(["Tx1", "Tx_New"]),
                    "Carbon_Cap_Zone2": sorted([]),
                }.items()
            )
        )
        actual_tx_by_z = OrderedDict(
            sorted(
                {
                    z: sorted(
                        [tx for tx in instance.CRB_TX_LINES_BY_CARBON_CAP_ZONE[z]]
                    )
                    for z in instance.CARBON_CAP_ZONES
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_by_z, actual_tx_by_z)

        # Set: CRB_TX_OPR_TMPS
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
                ("Tx_New", 20200101),
                ("Tx_New", 20200102),
                ("Tx_New", 20200103),
                ("Tx_New", 20200104),
                ("Tx_New", 20200105),
                ("Tx_New", 20200106),
                ("Tx_New", 20200107),
                ("Tx_New", 20200108),
                ("Tx_New", 20200109),
                ("Tx_New", 20200110),
                ("Tx_New", 20200111),
                ("Tx_New", 20200112),
                ("Tx_New", 20200113),
                ("Tx_New", 20200114),
                ("Tx_New", 20200115),
                ("Tx_New", 20200116),
                ("Tx_New", 20200117),
                ("Tx_New", 20200118),
                ("Tx_New", 20200119),
                ("Tx_New", 20200120),
                ("Tx_New", 20200121),
                ("Tx_New", 20200122),
                ("Tx_New", 20200123),
                ("Tx_New", 20200124),
                ("Tx_New", 20200201),
                ("Tx_New", 20200202),
                ("Tx_New", 20200203),
                ("Tx_New", 20200204),
                ("Tx_New", 20200205),
                ("Tx_New", 20200206),
                ("Tx_New", 20200207),
                ("Tx_New", 20200208),
                ("Tx_New", 20200209),
                ("Tx_New", 20200210),
                ("Tx_New", 20200211),
                ("Tx_New", 20200212),
                ("Tx_New", 20200213),
                ("Tx_New", 20200214),
                ("Tx_New", 20200215),
                ("Tx_New", 20200216),
                ("Tx_New", 20200217),
                ("Tx_New", 20200218),
                ("Tx_New", 20200219),
                ("Tx_New", 20200220),
                ("Tx_New", 20200221),
                ("Tx_New", 20200222),
                ("Tx_New", 20200223),
                ("Tx_New", 20200224),
                ("Tx_New", 20300101),
                ("Tx_New", 20300102),
                ("Tx_New", 20300103),
                ("Tx_New", 20300104),
                ("Tx_New", 20300105),
                ("Tx_New", 20300106),
                ("Tx_New", 20300107),
                ("Tx_New", 20300108),
                ("Tx_New", 20300109),
                ("Tx_New", 20300110),
                ("Tx_New", 20300111),
                ("Tx_New", 20300112),
                ("Tx_New", 20300113),
                ("Tx_New", 20300114),
                ("Tx_New", 20300115),
                ("Tx_New", 20300116),
                ("Tx_New", 20300117),
                ("Tx_New", 20300118),
                ("Tx_New", 20300119),
                ("Tx_New", 20300120),
                ("Tx_New", 20300121),
                ("Tx_New", 20300122),
                ("Tx_New", 20300123),
                ("Tx_New", 20300124),
                ("Tx_New", 20300201),
                ("Tx_New", 20300202),
                ("Tx_New", 20300203),
                ("Tx_New", 20300204),
                ("Tx_New", 20300205),
                ("Tx_New", 20300206),
                ("Tx_New", 20300207),
                ("Tx_New", 20300208),
                ("Tx_New", 20300209),
                ("Tx_New", 20300210),
                ("Tx_New", 20300211),
                ("Tx_New", 20300212),
                ("Tx_New", 20300213),
                ("Tx_New", 20300214),
                ("Tx_New", 20300215),
                ("Tx_New", 20300216),
                ("Tx_New", 20300217),
                ("Tx_New", 20300218),
                ("Tx_New", 20300219),
                ("Tx_New", 20300220),
                ("Tx_New", 20300221),
                ("Tx_New", 20300222),
                ("Tx_New", 20300223),
                ("Tx_New", 20300224),
            ]
        )
        actual_tx_op_tmp = sorted([(tx, tmp) for (tx, tmp) in instance.CRB_TX_OPR_TMPS])
        self.assertListEqual(expect_tx_op_tmp, actual_tx_op_tmp)

        # Param: tx_co2_intensity_tons_per_mwh_hourly
        expected_hourly_co2 = OrderedDict()
        for tx, tmp in expect_tx_op_tmp:
            if tx == "Tx1":
                expected_hourly_co2[(tx, tmp)] = 0.1
            elif tx == "Tx_New":
                expected_hourly_co2[(tx, tmp)] = 0.2

        actual_hourly_co2 = OrderedDict(
            sorted(
                {
                    (tx, tmp): instance.tx_co2_intensity_tons_per_mwh_hourly[tx, tmp]
                    for (tx, tmp) in instance.CRB_TX_OPR_TMPS
                }.items()
            )
        )

        self.assertDictEqual(expected_hourly_co2, actual_hourly_co2)


if __name__ == "__main__":
    unittest.main()
