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
from tests.project.operations.common_functions import get_project_operational_timepoints

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
    "project.capacity.capacity",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
]
NAME_OF_MODULE_BEING_TESTED = "project.operations.operational_types.gen_commit_bin"
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


class TestGenCommitBin(unittest.TestCase):
    """ """

    def assertDictAlmostEqual(self, d1, d2, msg=None, places=7):
        # check if both inputs are dicts
        self.assertIsInstance(d1, dict, "First argument is not a dictionary")
        self.assertIsInstance(d2, dict, "Second argument is not a dictionary")

        # check if both inputs have the same keys
        self.assertEqual(d1.keys(), d2.keys())

        # check each key
        for key, value in d1.items():
            if isinstance(value, dict):
                self.assertDictAlmostEqual(d1[key], d2[key], msg=msg)
            else:
                self.assertAlmostEqual(d1[key], d2[key], places=places, msg=msg)

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

        # Set: GEN_COMMIT_BIN
        expected_disp_bin_commit_gen_set = sorted(["Disp_Binary_Commit"])
        actual_disp_bin_commit_gen_set = sorted(
            [prj for prj in instance.GEN_COMMIT_BIN]
        )
        self.assertListEqual(
            expected_disp_bin_commit_gen_set, actual_disp_bin_commit_gen_set
        )

        # Set: GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS
        expected_gen_commit_bin_str_rmp_prjs = sorted(["Disp_Binary_Commit"])
        actual_gen_commit_bin_str_rmp_prjs = sorted(
            [prj for prj in instance.GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS]
        )
        self.assertListEqual(
            expected_gen_commit_bin_str_rmp_prjs, actual_gen_commit_bin_str_rmp_prjs
        )

        # Set: GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS_TYPES
        expected_gen_commit_bin_str_rmp_prjs_types = sorted(
            [("Disp_Binary_Commit", 1.0)]
        )
        actual_gen_commit_bin_str_rmp_prjs_types = sorted(
            [(prj, s) for prj, s in instance.GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS_TYPES]
        )
        self.assertListEqual(
            expected_gen_commit_bin_str_rmp_prjs_types,
            actual_gen_commit_bin_str_rmp_prjs_types,
        )

        # Set: GEN_COMMIT_BIN_STR_TYPES_BY_PRJ
        str_types_by_prj_dict = dict()
        for prj_type in expected_gen_commit_bin_str_rmp_prjs_types:
            if prj_type[0] not in str_types_by_prj_dict.keys():
                str_types_by_prj_dict[prj_type[0]] = [prj_type[1]]
            else:
                str_types_by_prj_dict[prj_type[0]].append(prj_type[1])

        expected_str_types_by_prj = OrderedDict(sorted(str_types_by_prj_dict.items()))
        actual_str_types_by_prj = OrderedDict(
            sorted(
                {
                    prj: [
                        type for type in instance.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[prj]
                    ]
                    for prj in instance.GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS
                }.items()
            )
        )
        self.assertDictEqual(expected_str_types_by_prj, actual_str_types_by_prj)

        # Set: GEN_COMMIT_BIN_OPR_TMPS
        expected_operational_timepoints_by_project = sorted(
            get_project_operational_timepoints(expected_disp_bin_commit_gen_set)
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in instance.GEN_COMMIT_BIN_OPR_TMPS]
        )
        self.assertListEqual(
            expected_operational_timepoints_by_project,
            actual_operational_timepoints_by_project,
        )

        # Set: GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES
        expected_opr_tmps_str_types = sorted(
            [
                (g, tmp, 1.0)
                for (g, tmp) in expected_operational_timepoints_by_project
                if g in expected_gen_commit_bin_str_rmp_prjs
            ]
        )
        actual_opr_tmps_str_types = sorted(
            [(g, tmp, s) for (g, tmp, s) in instance.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES]
        )
        self.assertListEqual(expected_opr_tmps_str_types, actual_opr_tmps_str_types)

        # Param: gen_commit_bin_min_stable_level_fraction
        expected_min_stable_fraction = {"Disp_Binary_Commit": 0.4}
        actual_min_stable_fraction = {
            prj: instance.gen_commit_bin_min_stable_level_fraction[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_min_stable_fraction, actual_min_stable_fraction)

        # Param: gen_commit_bin_startup_plus_ramp_up_rate_by_st
        expected_startup_plus_ramp_up_rate_by_st = {("Disp_Binary_Commit", 1.0): 0.6}
        actual_startup_plus_ramp_up_rate_by_st = {
            (prj, s): instance.gen_commit_bin_startup_plus_ramp_up_rate_by_st[prj, s]
            for prj, s in instance.GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS_TYPES
        }
        self.assertDictEqual(
            expected_startup_plus_ramp_up_rate_by_st,
            actual_startup_plus_ramp_up_rate_by_st,
        )

        # Param: gen_commit_bin_shutdown_plus_ramp_down_rate
        expected_shutdown_plus_ramp_down_rate = {"Disp_Binary_Commit": 0.6}
        actual_shutdown_plus_ramp_down_rate = {
            prj: instance.gen_commit_bin_shutdown_plus_ramp_down_rate[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(
            expected_shutdown_plus_ramp_down_rate, actual_shutdown_plus_ramp_down_rate
        )

        # Param: gen_commit_bin_ramp_up_when_on_rate
        expected_ramp_up_when_on_rate = {"Disp_Binary_Commit": 0.3}
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_bin_ramp_up_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(
            expected_ramp_up_when_on_rate, actual_ramp_down_when_on_rate
        )

        # Param: gen_commit_bin_ramp_down_when_on_rate
        expected_ramp_down_when_on_rate = {"Disp_Binary_Commit": 0.5}
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_bin_ramp_down_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(
            expected_ramp_down_when_on_rate, actual_ramp_down_when_on_rate
        )

        # Param: gen_commit_bin_ramp_down_when_on_rate
        expected_ramp_down_when_on_rate = {"Disp_Binary_Commit": 0.5}
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_bin_ramp_down_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(
            expected_ramp_down_when_on_rate, actual_ramp_down_when_on_rate
        )

        # Param: gen_commit_bin_allow_ramp_up_violation
        expected_ramp_up_viol = {"Disp_Binary_Commit": 1.0}
        actual_ramp_up_viol = {
            prj: instance.gen_commit_bin_allow_ramp_up_violation[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_ramp_up_viol, actual_ramp_up_viol)

        # Param: gen_commit_bin_allow_ramp_down_violation
        expected_ramp_down_viol = {"Disp_Binary_Commit": 0}
        actual_ramp_down_viol = {
            prj: instance.gen_commit_bin_allow_ramp_down_violation[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_ramp_down_viol, actual_ramp_down_viol)

        # Param: gen_commit_bin_min_up_time_hours
        expected_min_up_time = {"Disp_Binary_Commit": 3}
        actual_min_up_time = {
            prj: instance.gen_commit_bin_min_up_time_hours[prj]
            for prj in instance.GEN_COMMIT_BIN
        }

        self.assertDictEqual(expected_min_up_time, actual_min_up_time)

        # Param: gen_commit_bin_allow_min_up_time_violation
        expected_min_up_time_viol = {"Disp_Binary_Commit": 1.0}
        actual_min_up_time_viol = {
            prj: instance.gen_commit_bin_allow_min_up_time_violation[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_min_up_time_viol, actual_min_up_time_viol)

        # Param: gen_commit_bin_min_down_time_hours
        expected_min_down_time = {"Disp_Binary_Commit": 7}
        actual_min_down_time = {
            prj: instance.gen_commit_bin_min_down_time_hours[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_min_down_time, actual_min_down_time)

        # Param: gen_commit_bin_allow_min_down_time_violation
        expected_min_down_time_viol = {"Disp_Binary_Commit": 0.0}
        actual_min_down_time_viol = {
            prj: instance.gen_commit_bin_allow_min_down_time_violation[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_min_down_time_viol, actual_min_down_time_viol)

        # Param: gen_commit_bin_down_time_cutoff_hours
        expected_down_time_cutoff_hours = {("Disp_Binary_Commit", 1.0): 7}
        actual_down_time_cutoff_hours = {
            (prj, s): instance.gen_commit_bin_down_time_cutoff_hours[prj, s]
            for prj, s in instance.GEN_COMMIT_BIN_STARTUP_BY_ST_PRJS_TYPES
        }
        self.assertDictEqual(
            expected_down_time_cutoff_hours, actual_down_time_cutoff_hours
        )

        # Param: gen_commit_bin_partial_availability_threshold
        expected_threshold = {"Disp_Binary_Commit": 0.01}
        actual_threshold = {
            prj: instance.gen_commit_bin_partial_availability_threshold[prj]
            for prj in instance.GEN_COMMIT_BIN
        }
        self.assertDictEqual(expected_threshold, actual_threshold)


if __name__ == "__main__":
    unittest.main()
