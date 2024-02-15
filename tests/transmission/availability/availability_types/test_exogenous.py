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


from importlib import import_module
import os.path
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data
from tests.project.operations.common_functions import get_project_operational_timepoints

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "geography.load_zones",
    "transmission",
    "transmission.capacity.capacity_types",
    "transmission.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "transmission.availability.availability_types.exogenous"

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


class TestExogenousAvailabilityType(unittest.TestCase):
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

        # Set: TX_AVL_EXOG
        expected_tx_subset = sorted(["Tx1", "Tx_New", "Tx3", "Tx_binary_1"])
        actual_tx_subset = sorted([prj for prj in instance.TX_AVL_EXOG])
        self.assertListEqual(expected_tx_subset, actual_tx_subset)

        # Set: TX_AVL_EXOG_OPR_TMPS
        # TODO: we have a function to get op timepoints for project; we
        #  should make that flexible enough to accomodate transmission also
        #  instead of hardcoding this
        expected_operational_timepoints_by_tx = sorted(
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
        actual_operational_timepoints_by_tx = sorted(
            [(tx, tmp) for (tx, tmp) in instance.TX_AVL_EXOG_OPR_TMPS]
        )
        self.assertListEqual(
            expected_operational_timepoints_by_tx, actual_operational_timepoints_by_tx
        )

        # Param: availability_derate
        availability_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs", "transmission_availability_exogenous.tab"
            ),
            sep="\t",
        )
        defaults = {(tx, tmp): 1 for (tx, tmp) in instance.TX_AVL_EXOG_OPR_TMPS}
        derates = {
            (p, tmp): avail
            for p, tmp, avail in zip(
                availability_df.transmission_line,
                availability_df.timepoint,
                availability_df.availability_derate,
            )
        }
        expected_availability_derate = dict()
        for tx, tmp in defaults.keys():
            if (tx, tmp) in derates.keys():
                expected_availability_derate[tx, tmp] = derates[tx, tmp]
            else:
                expected_availability_derate[tx, tmp] = defaults[tx, tmp]
        actual_availability_derate = {
            (tx, tmp): instance.tx_avl_exog_derate[tx, tmp]
            for (tx, tmp) in instance.TX_AVL_EXOG_OPR_TMPS
        }

        self.assertDictEqual(expected_availability_derate, actual_availability_derate)


if __name__ == "__main__":
    unittest.main()
