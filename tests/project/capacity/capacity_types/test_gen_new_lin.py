# Copyright 2016-2020 Blue Marble Analytics LLC.
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

from __future__ import print_function
from builtins import str
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
    "project",
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_types.gen_new_lin"
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


class TestGenNewLin(unittest.TestCase):
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
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: GEN_NEW_LIN_VNTS
        expected_gen_vintage_set = sorted(
            [("Gas_CCGT_New", 2020), ("Gas_CCGT_New", 2030), ("Gas_CT_New", 2030)]
        )
        actual_gen_vintage_set = sorted(
            [(prj, period) for (prj, period) in instance.GEN_NEW_LIN_VNTS]
        )
        self.assertListEqual(expected_gen_vintage_set, actual_gen_vintage_set)

        # Params: gen_new_lin_operational_lifetime_yrs_by_vintage
        expected_lifetime = OrderedDict(
            sorted(
                {
                    ("Gas_CCGT_New", 2020): 30,
                    ("Gas_CCGT_New", 2030): 30,
                    ("Gas_CT_New", 2030): 30,
                }.items()
            )
        )
        actual_lifetime = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.gen_new_lin_operational_lifetime_yrs_by_vintage[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.GEN_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: gen_new_lin_annualized_real_cost_per_mw_yr
        expected_cost = OrderedDict(
            sorted(
                {
                    ("Gas_CCGT_New", 2020): 200000,
                    ("Gas_CCGT_New", 2030): 180000,
                    ("Gas_CT_New", 2030): 140000,
                }.items()
            )
        )
        actual_cost = OrderedDict(
            sorted(
                {
                    (prj, v): instance.gen_new_lin_annualized_real_cost_per_mw_yr[
                        prj, v
                    ]
                    for (prj, v) in instance.GEN_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_cost, actual_cost)

        # Set: GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT
        expected_gen_vintage_min_set = sorted([("Gas_CT_New", 2030)])
        actual_gen_vintage_min_set = sorted(
            [
                (prj, period)
                for (prj, period) in instance.GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT
            ]
        )
        self.assertListEqual(expected_gen_vintage_min_set, actual_gen_vintage_min_set)

        # Params: gen_new_lin_min_cumulative_new_build_mw
        expected_min_new_mw = OrderedDict(sorted({("Gas_CT_New", 2030): 10}.items()))
        actual_min_new_mw = OrderedDict(
            sorted(
                {
                    (prj, v): instance.gen_new_lin_min_cumulative_new_build_mw[prj, v]
                    for (prj, v) in instance.GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT
                }.items()
            )
        )
        self.assertDictEqual(expected_min_new_mw, actual_min_new_mw)

        # Set: GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT
        expected_gen_vintage_max_set = sorted(
            [("Gas_CCGT_New", 2020), ("Gas_CCGT_New", 2030)]
        )
        actual_gen_vintage_max_set = sorted(
            [
                (prj, period)
                for (prj, period) in instance.GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT
            ]
        )
        self.assertListEqual(expected_gen_vintage_max_set, actual_gen_vintage_max_set)

        # Params: gen_new_lin_max_cumulative_new_build_mw
        expected_max_new_mw = OrderedDict(
            sorted({("Gas_CCGT_New", 2020): 20, ("Gas_CCGT_New", 2030): 20}.items())
        )
        actual_max_new_mw = OrderedDict(
            sorted(
                {
                    (prj, v): instance.gen_new_lin_max_cumulative_new_build_mw[prj, v]
                    for (prj, v) in instance.GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT
                }.items()
            )
        )
        self.assertDictEqual(expected_max_new_mw, actual_max_new_mw)

    def test_derived_data(self):
        """
        Calculations
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE
        expected_periods_by_gen_vintage = {
            ("Gas_CCGT_New", 2020): [2020, 2030],
            ("Gas_CCGT_New", 2030): [2030],
            ("Gas_CT_New", 2030): [2030],
        }
        actual_periods_by_gen_vintage = {
            (prj, v): [
                period for period in instance.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE[prj, v]
            ]
            for (prj, v) in instance.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE
        }
        self.assertDictEqual(
            expected_periods_by_gen_vintage, actual_periods_by_gen_vintage
        )

        # Set: GEN_NEW_LIN_OPR_PRDS
        expected_gen_op_periods = [
            ("Gas_CCGT_New", 2020),
            ("Gas_CCGT_New", 2030),
            ("Gas_CT_New", 2030),
        ]
        actual_gen_op_periods = sorted(
            [(prj, period) for (prj, period) in instance.GEN_NEW_LIN_OPR_PRDS]
        )
        self.assertListEqual(expected_gen_op_periods, actual_gen_op_periods)

        # Set: GEN_NEW_LIN_VNTS_OPR_IN_PERIOD
        expected_gen_vintage_op_in_period = {
            2020: [("Gas_CCGT_New", 2020)],
            2030: [
                ("Gas_CCGT_New", 2020),
                ("Gas_CCGT_New", 2030),
                ("Gas_CT_New", 2030),
            ],
        }
        actual_gen_vintage_op_in_period = {
            p: [(g, v) for (g, v) in sorted(instance.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD[p])]
            for p in sorted(instance.PERIODS)
        }
        self.assertDictEqual(
            expected_gen_vintage_op_in_period, actual_gen_vintage_op_in_period
        )


if __name__ == "__main__":
    unittest.main()
