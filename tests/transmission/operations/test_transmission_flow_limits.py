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
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "transmission",
    "transmission.capacity",
    "transmission.capacity.capacity_types",
    "transmission.capacity.capacity",
    "transmission.availability.availability",
    "transmission.operations.operational_types",
    "transmission.operations.operations",
]
NAME_OF_MODULE_BEING_TESTED = "transmission.operations.transmission_flow_limits"

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

        # Set: TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT
        expect_tx_opr_tmps = sorted([("Tx_New", 20200101), ("Tx_New", 20200102)])
        actual_tx_opr_tmps = sorted(
            [(tx, tmp) for (tx, tmp) in instance.TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT]
        )
        self.assertListEqual(expect_tx_opr_tmps, actual_tx_opr_tmps)

        # Set: TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT
        expect_tx_opr_tmps = sorted([("Tx_New", 20200101), ("Tx_New", 20200102)])
        actual_tx_opr_tmps = sorted(
            [(tx, tmp) for (tx, tmp) in instance.TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT]
        )
        self.assertListEqual(expect_tx_opr_tmps, actual_tx_opr_tmps)

        # Param: tx_simple_min_flow_mw
        expected_min_flow = OrderedDict(
            sorted({("Tx_New", 20200101): -0.1, ("Tx_New", 20200102): -5.5}.items())
        )
        actual_min_flow = OrderedDict(
            sorted(
                {
                    (tx, tmp): instance.tx_simple_min_flow_mw[tx, tmp]
                    for (tx, tmp) in instance.TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT
                }.items()
            )
        )
        self.assertDictEqual(expected_min_flow, actual_min_flow)

        # Param: tx_simple_max_flow_mw
        expected_max_flow = OrderedDict(
            sorted({("Tx_New", 20200101): 2, ("Tx_New", 20200102): 2.5}.items())
        )
        actual_max_flow = OrderedDict(
            sorted(
                {
                    (tx, tmp): instance.tx_simple_max_flow_mw[tx, tmp]
                    for (tx, tmp) in instance.TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT
                }.items()
            )
        )
        self.assertDictEqual(expected_max_flow, actual_max_flow)


if __name__ == "__main__":
    unittest.main()
