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
    "temporal.investment.periods",
    "geography.load_zones",
    "transmission",
]
NAME_OF_MODULE_BEING_TESTED = "transmission.capacity.capacity_types.tx_new_lin"
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


class TestSpecifiedTransmission(unittest.TestCase):
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

        # Set: TX_NEW_LIN_VNTS
        expected_tx_vintages = sorted([("Tx_New", 2020), ("Tx_New", 2030)])
        actual_tx_vintages = sorted([(tx, v) for (tx, v) in instance.TX_NEW_LIN_VNTS])
        self.assertListEqual(expected_tx_vintages, actual_tx_vintages)

        # Param: tx_new_lin_operational_lifetime_yrs_by_vintage
        expected_lifetime = OrderedDict(
            sorted({("Tx_New", 2020): 35, ("Tx_New", 2030): 35}.items())
        )
        actual_lifetime = OrderedDict(
            sorted(
                {
                    (tx, v): instance.tx_new_lin_operational_lifetime_yrs_by_vintage[
                        tx, v
                    ]
                    for (tx, v) in instance.TX_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Param: tx_new_lin_annualized_real_cost_per_mw_yr
        expected_cost = OrderedDict(
            sorted({("Tx_New", 2020): 10, ("Tx_New", 2030): 10}.items())
        )
        actual_cost = OrderedDict(
            sorted(
                {
                    (tx, v): instance.tx_new_lin_annualized_real_cost_per_mw_yr[tx, v]
                    for (tx, v) in instance.TX_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_cost, actual_cost)

        # Param: tx_new_lin_fixed_cost_per_mw_yr
        expected_fcost = OrderedDict(
            sorted({("Tx_New", 2020): 0, ("Tx_New", 2030): 5}.items())
        )
        actual_fcost = OrderedDict(
            sorted(
                {
                    (tx, v): instance.tx_new_lin_fixed_cost_per_mw_yr[tx, v]
                    for (tx, v) in instance.TX_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_fcost, actual_fcost)

        # Set: TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT
        expected_tx_vintage_min_set = sorted([("Tx_New", 2020), ("Tx_New", 2030)])
        actual_tx_vintage_min_set = sorted(
            [(tx, period) for (tx, period) in instance.TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT]
        )
        self.assertListEqual(expected_tx_vintage_min_set, actual_tx_vintage_min_set)

        # Params: tx_new_lin_min_cumulative_new_build_mw
        expected_min_new_mw = OrderedDict(
            sorted({("Tx_New", 2020): 0, ("Tx_New", 2030): 0}.items())
        )
        actual_min_new_mw = OrderedDict(
            sorted(
                {
                    (tx, v): instance.tx_new_lin_min_cumulative_new_build_mw[tx, v]
                    for (tx, v) in instance.TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT
                }.items()
            )
        )
        self.assertDictEqual(expected_min_new_mw, actual_min_new_mw)

        # Set: TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT
        expected_tx_vintage_max_set = sorted([("Tx_New", 2020), ("Tx_New", 2030)])
        actual_tx_vintage_max_set = sorted(
            [(tx, period) for (tx, period) in instance.TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT]
        )
        self.assertListEqual(expected_tx_vintage_max_set, actual_tx_vintage_max_set)

        # Params: tx_new_lin_max_cumulative_new_build_mw
        expected_max_new_mw = OrderedDict(
            sorted({("Tx_New", 2020): 30, ("Tx_New", 2030): 30}.items())
        )
        actual_max_new_mw = OrderedDict(
            sorted(
                {
                    (tx, v): instance.tx_new_lin_max_cumulative_new_build_mw[tx, v]
                    for (tx, v) in instance.TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT
                }.items()
            )
        )
        self.assertDictEqual(expected_max_new_mw, actual_max_new_mw)

    def test_derived_data(self):
        """
        Test in-model operations and calculations
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

        # Set: OPR_PRDS_BY_TX_NEW_LIN_VINTAGE
        expected_op_p_by_tx_v = OrderedDict(
            sorted({("Tx_New", 2020): [2020, 2030], ("Tx_New", 2030): [2030]}.items())
        )
        actual_op_p_by_tx_v = OrderedDict(
            sorted(
                {
                    (tx, v): [p for p in instance.OPR_PRDS_BY_TX_NEW_LIN_VINTAGE[tx, v]]
                    for (tx, v) in instance.TX_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_op_p_by_tx_v, actual_op_p_by_tx_v)

        # Set: TX_NEW_LIN_OPR_PRDS
        expected_tx_op_periods = sorted([("Tx_New", 2020), ("Tx_New", 2030)])
        actual_tx_op_periods = sorted(
            [(tx, p) for (tx, p) in instance.TX_NEW_LIN_OPR_PRDS]
        )
        self.assertListEqual(expected_tx_op_periods, actual_tx_op_periods)

        # Set: TX_NEW_LIN_VNTS_OPR_IN_PRD
        expected_tx_v_by_period = OrderedDict(
            sorted(
                {
                    2020: sorted([("Tx_New", 2020)]),
                    2030: sorted([("Tx_New", 2020), ("Tx_New", 2030)]),
                }.items()
            )
        )
        actual_tx_v_by_period = OrderedDict(
            sorted(
                {
                    p: sorted(
                        [(tx, v) for (tx, v) in instance.TX_NEW_LIN_VNTS_OPR_IN_PRD[p]]
                    )
                    for p in instance.PERIODS
                }.items()
            )
        )
        self.assertDictEqual(expected_tx_v_by_period, actual_tx_v_by_period)


if __name__ == "__main__":
    unittest.main()
