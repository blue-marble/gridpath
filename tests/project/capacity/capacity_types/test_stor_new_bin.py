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
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_types.stor_new_bin"
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


class TestStorNewBin(unittest.TestCase):
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

        # Set: STOR_NEW_BIN
        expected_stor_new_bin_project_set = ["Battery_Binary"]
        actual_stor_new_bin_project_set = sorted([prj for prj in instance.STOR_NEW_BIN])
        self.assertListEqual(
            expected_stor_new_bin_project_set, actual_stor_new_bin_project_set
        )

        # Param: stor_new_bin_build_size_mw
        expected_stor_new_bin_build_size_mw = OrderedDict(
            sorted({"Battery_Binary": 10}.items())
        )
        actual_stor_new_bin_build_size_mw = OrderedDict(
            sorted(
                {
                    prj: instance.stor_new_bin_build_size_mw[prj]
                    for prj in instance.STOR_NEW_BIN
                }.items()
            )
        )
        self.assertDictEqual(
            expected_stor_new_bin_build_size_mw, actual_stor_new_bin_build_size_mw
        )

        # Param: stor_new_bin_build_size_mwh
        expected_stor_new_bin_build_size_mwh = OrderedDict(
            sorted({"Battery_Binary": 40}.items())
        )
        actual_stor_new_bin_build_size_mwh = OrderedDict(
            sorted(
                {
                    prj: instance.stor_new_bin_build_size_mwh[prj]
                    for prj in instance.STOR_NEW_BIN
                }.items()
            )
        )
        self.assertDictEqual(
            expected_stor_new_bin_build_size_mwh, actual_stor_new_bin_build_size_mwh
        )

        # Set: STOR_NEW_BIN_VNTS
        expected_storage_vintage_set = sorted(
            [("Battery_Binary", 2020), ("Battery_Binary", 2030)]
        )
        actual_storage_vintage_set = sorted(
            [(prj, period) for (prj, period) in instance.STOR_NEW_BIN_VNTS]
        )
        self.assertListEqual(expected_storage_vintage_set, actual_storage_vintage_set)

        # Params: stor_new_bin_operational_lifetime_yrs
        expected_lifetime = OrderedDict(
            sorted({("Battery_Binary", 2020): 10, ("Battery_Binary", 2030): 10}.items())
        )
        actual_lifetime = OrderedDict(
            sorted(
                {
                    (prj, vintage): instance.stor_new_bin_operational_lifetime_yrs[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.STOR_NEW_BIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: stor_new_bin_fixed_cost_per_mw_yr
        expected_mw_yr_fcost = OrderedDict(
            sorted({("Battery_Binary", 2020): 0, ("Battery_Binary", 2030): 0}.items())
        )
        actual_mw_yr_fcost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.stor_new_bin_fixed_cost_per_mw_yr[prj, vintage]
                    for (prj, vintage) in instance.STOR_NEW_BIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_mw_yr_fcost, actual_mw_yr_fcost)

        # Params: stor_new_bin_fixed_cost_per_mwh_yr
        expected_mwh_yr_fcost = OrderedDict(
            sorted({("Battery_Binary", 2020): 0, ("Battery_Binary", 2030): 0}.items())
        )
        actual_mwh_yr_fcost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.stor_new_bin_fixed_cost_per_mwh_yr[prj, vintage]
                    for (prj, vintage) in instance.STOR_NEW_BIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_mwh_yr_fcost, actual_mwh_yr_fcost)

        # Params: stor_new_bin_financial_lifetime_yrs_by_vintage
        expected_flifetime = OrderedDict(
            sorted({("Battery_Binary", 2020): 10, ("Battery_Binary", 2030): 10}.items())
        )
        actual_flifetime = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.stor_new_bin_financial_lifetime_yrs_by_vintage[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.STOR_NEW_BIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_flifetime, actual_flifetime)

        # Params: stor_new_bin_annualized_real_cost_per_mw_yr
        expected_mw_yr_cost = OrderedDict(
            sorted({("Battery_Binary", 2020): 1, ("Battery_Binary", 2030): 1}.items())
        )
        actual_mw_yr_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.stor_new_bin_annualized_real_cost_per_mw_yr[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.STOR_NEW_BIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_mw_yr_cost, actual_mw_yr_cost)

        # Params: stor_new_bin_annualized_real_cost_per_mw_yr
        expected_mwh_yr_cost = OrderedDict(
            sorted({("Battery_Binary", 2020): 1, ("Battery_Binary", 2030): 1}.items())
        )
        actual_mwh_yr_cost = OrderedDict(
            sorted(
                {
                    (
                        prj,
                        vintage,
                    ): instance.stor_new_bin_annualized_real_cost_per_mwh_yr[
                        prj, vintage
                    ]
                    for (prj, vintage) in instance.STOR_NEW_BIN_VNTS
                }.items()
            )
        )
        self.assertDictEqual(expected_mwh_yr_cost, actual_mwh_yr_cost)

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

        # Sets: OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE
        expected_op_periods_by_stor_vintage = {
            ("Battery_Binary", 2020): [2020],
            ("Battery_Binary", 2030): [2030],
        }
        actual_periods_by_stor_vintage = {
            (prj, vintage): [
                period
                for period in instance.OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE[prj, vintage]
            ]
            for (prj, vintage) in instance.OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE
        }
        self.assertDictEqual(
            expected_op_periods_by_stor_vintage, actual_periods_by_stor_vintage
        )

        # Sets: STOR_NEW_BIN_OPR_PRDS
        expected_stor_op_periods = sorted(
            [("Battery_Binary", 2020), ("Battery_Binary", 2030)]
        )
        actual_stor_op_periods = sorted(
            [(prj, period) for (prj, period) in instance.STOR_NEW_BIN_OPR_PRDS]
        )
        self.assertListEqual(expected_stor_op_periods, actual_stor_op_periods)

        # Sets: STOR_NEW_BIN_VNTS_OPR_IN_PRD
        expected_stor_vintage_op_in_period = {
            2020: [("Battery_Binary", 2020)],
            2030: [("Battery_Binary", 2030)],
        }
        actual_stor_vintage_op_in_period = {
            p: [(g, v) for (g, v) in instance.STOR_NEW_BIN_VNTS_OPR_IN_PRD[p]]
            for p in instance.PERIODS
        }
        self.assertDictEqual(
            expected_stor_vintage_op_in_period, actual_stor_vintage_op_in_period
        )

        # Sets: FIN_PRDS_BY_STOR_NEW_BIN_VINTAGE
        expected_fperiods_by_stor_vintage = {
            ("Battery_Binary", 2020): [2020],
            ("Battery_Binary", 2030): [2030],
        }
        actual_fperiods_by_stor_vintage = {
            (prj, vintage): [
                period
                for period in instance.FIN_PRDS_BY_STOR_NEW_BIN_VINTAGE[prj, vintage]
            ]
            for (prj, vintage) in instance.FIN_PRDS_BY_STOR_NEW_BIN_VINTAGE
        }
        self.assertDictEqual(
            expected_fperiods_by_stor_vintage, actual_fperiods_by_stor_vintage
        )

        # Sets: STOR_NEW_BIN_FIN_PRDS
        expected_stor_fperiods = sorted(
            [("Battery_Binary", 2020), ("Battery_Binary", 2030)]
        )
        actual_stor_fperiods = sorted(
            [(prj, period) for (prj, period) in instance.STOR_NEW_BIN_FIN_PRDS]
        )
        self.assertListEqual(expected_stor_fperiods, actual_stor_fperiods)

        # Sets: STOR_NEW_BIN_VNTS_FIN_IN_PRD
        expected_stor_vintage_f_in_period = {
            2020: [("Battery_Binary", 2020)],
            2030: [("Battery_Binary", 2030)],
        }
        actual_stor_vintage_f_in_period = {
            p: [(g, v) for (g, v) in instance.STOR_NEW_BIN_VNTS_FIN_IN_PRD[p]]
            for p in instance.PERIODS
        }
        self.assertDictEqual(
            expected_stor_vintage_f_in_period, actual_stor_vintage_f_in_period
        )


if __name__ == "__main__":
    unittest.main()
