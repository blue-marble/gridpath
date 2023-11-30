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

        # Params: gen_new_lin_fixed_cost_per_mw_yr
        expected_fcost = OrderedDict(
            sorted(
                {
                    ("Gas_CCGT_New", 2020): 1,
                    ("Gas_CCGT_New", 2030): 1,
                    ("Gas_CT_New", 2030): 1,
                }.items()
            )
        )
        actual_fcost = OrderedDict(
            sorted(
                {
                    (prj, v): instance.gen_new_lin_fixed_cost_per_mw_yr[prj, v]
                    for (prj, v) in instance.GEN_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_fcost, actual_fcost)

        # Params: gen_new_lin_financial_lifetime_yrs_by_vintage
        expected_flifetime = OrderedDict(
            sorted(
                {
                    ("Gas_CCGT_New", 2020): 10,
                    ("Gas_CCGT_New", 2030): 30,
                    ("Gas_CT_New", 2030): 30,
                }.items()
            )
        )
        actual_flifetime = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.gen_new_lin_financial_lifetime_yrs_by_vintage[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.GEN_NEW_LIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_flifetime, actual_flifetime)

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

    def test_derived_data(self):
        """
        Calculations
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

        # Set: FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE
        expected_fperiods_by_gen_vintage = {
            ("Gas_CCGT_New", 2020): [2020],
            ("Gas_CCGT_New", 2030): [2030],
            ("Gas_CT_New", 2030): [2030],
        }
        actual_fperiods_by_gen_vintage = {
            (prj, v): [
                period for period in instance.FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE[prj, v]
            ]
            for (prj, v) in instance.FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE
        }
        self.assertDictEqual(
            expected_fperiods_by_gen_vintage, actual_fperiods_by_gen_vintage
        )

        # Set: GEN_NEW_LIN_FIN_PRDS
        expected_gen_op_fperiods = [
            ("Gas_CCGT_New", 2020),
            ("Gas_CCGT_New", 2030),
            ("Gas_CT_New", 2030),
        ]
        actual_gen_op_fperiods = sorted(
            [(prj, period) for (prj, period) in instance.GEN_NEW_LIN_FIN_PRDS]
        )
        self.assertListEqual(expected_gen_op_fperiods, actual_gen_op_fperiods)

        # Set: GEN_NEW_LIN_VNTS_FIN_IN_PERIOD
        expected_gen_vintage_f_in_period = {
            2020: [("Gas_CCGT_New", 2020)],
            2030: [
                ("Gas_CCGT_New", 2030),
                ("Gas_CT_New", 2030),
            ],
        }
        actual_gen_vintage_f_in_period = {
            p: [(g, v) for (g, v) in sorted(instance.GEN_NEW_LIN_VNTS_FIN_IN_PERIOD[p])]
            for p in sorted(instance.PERIODS)
        }
        self.assertDictEqual(
            expected_gen_vintage_f_in_period, actual_gen_vintage_f_in_period
        )


if __name__ == "__main__":
    unittest.main()
