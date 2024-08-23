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
NAME_OF_MODULE_BEING_TESTED = "project.operations.operational_types.gen_commit_cap"
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


class TestGenCommitCap(unittest.TestCase):
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

        # Set: GEN_COMMIT_CAP
        expected_disp_cap_commit_gen_set = sorted(
            [
                "Gas_CCGT",
                "Coal",
                "Gas_CT",
                "Gas_CCGT_New",
                "Gas_CCGT_New_Binary",
                "Gas_CT_New",
                "Gas_CCGT_z2",
                "Coal_z2",
                "Gas_CT_z2",
            ]
        )
        actual_disp_cap_commit_gen_set = sorted(
            [prj for prj in instance.GEN_COMMIT_CAP]
        )
        self.assertListEqual(
            expected_disp_cap_commit_gen_set, actual_disp_cap_commit_gen_set
        )

        # Set: GEN_COMMIT_CAP_OPR_TMPS
        expected_operational_timpoints_by_project = sorted(
            get_project_operational_timepoints(expected_disp_cap_commit_gen_set)
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in instance.GEN_COMMIT_CAP_OPR_TMPS]
        )
        self.assertListEqual(
            expected_operational_timpoints_by_project,
            actual_operational_timepoints_by_project,
        )

        # Param: gen_commit_cap_unit_size_mw
        expected_unit_size = {
            "Gas_CCGT": 6,
            "Coal": 6,
            "Gas_CT": 6,
            "Gas_CCGT_New": 6,
            "Gas_CCGT_New_Binary": 6,
            "Gas_CT_New": 6,
            "Gas_CCGT_z2": 6,
            "Coal_z2": 6,
            "Gas_CT_z2": 6,
        }
        actual_unit_size = {
            prj: instance.gen_commit_cap_unit_size_mw[prj]
            for prj in instance.GEN_COMMIT_CAP
        }
        self.assertDictEqual(expected_unit_size, actual_unit_size)

        # Param: gen_commit_cap_min_stable_level_fraction
        expected_min_stable_fraction = {
            "Gas_CCGT": 0.4,
            "Coal": 0.4,
            "Gas_CT": 0.4,
            "Gas_CCGT_New": 0.4,
            "Gas_CCGT_New_Binary": 0.4,
            "Gas_CT_New": 0.4,
            "Gas_CCGT_z2": 0.4,
            "Coal_z2": 0.4,
            "Gas_CT_z2": 0.4,
        }
        actual_min_stable_fraction = {
            prj: instance.gen_commit_cap_min_stable_level_fraction[prj]
            for prj in instance.GEN_COMMIT_CAP
        }
        self.assertDictEqual(expected_min_stable_fraction, actual_min_stable_fraction)

        # Param: gen_commit_cap_startup_plus_ramp_up_rate
        expected_startup_plus_ramp_up_rate = {
            "Gas_CCGT": 0.6,
            "Coal": 0.6,
            "Gas_CT": 0.6,
            "Gas_CCGT_New": 0.6,
            "Gas_CCGT_New_Binary": 0.6,
            "Gas_CT_New": 0.6,
            "Gas_CCGT_z2": 1,
            "Coal_z2": 1,
            "Gas_CT_z2": 1,
        }
        actual_startup_plus_ramp_up_rate = {
            prj: instance.gen_commit_cap_startup_plus_ramp_up_rate[prj]
            for prj in instance.GEN_COMMIT_CAP
        }
        self.assertDictEqual(
            expected_startup_plus_ramp_up_rate, actual_startup_plus_ramp_up_rate
        )

        # Param: gen_commit_cap_shutdown_plus_ramp_down_rate
        expected_shutdown_plus_ramp_down_rate = {
            "Gas_CCGT": 0.6,
            "Coal": 0.6,
            "Gas_CT": 0.6,
            "Gas_CCGT_New": 0.6,
            "Gas_CCGT_New_Binary": 0.6,
            "Gas_CT_New": 0.6,
            "Gas_CCGT_z2": 1,
            "Coal_z2": 1,
            "Gas_CT_z2": 1,
        }
        actual_shutdown_plus_ramp_down_rate = {
            prj: instance.gen_commit_cap_shutdown_plus_ramp_down_rate[prj]
            for prj in instance.GEN_COMMIT_CAP
        }
        self.assertDictEqual(
            expected_shutdown_plus_ramp_down_rate, actual_shutdown_plus_ramp_down_rate
        )

        # Param: gen_commit_cap_ramp_up_when_on_rate
        expected_ramp_up_when_on_rate = {
            "Gas_CCGT": 0.3,
            "Coal": 0.2,
            "Gas_CT": 0.5,
            "Gas_CCGT_New": 0.5,
            "Gas_CCGT_New_Binary": 0.5,
            "Gas_CT_New": 0.8,
            "Gas_CCGT_z2": 1,
            "Coal_z2": 1,
            "Gas_CT_z2": 1,
        }
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_cap_ramp_up_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_CAP
        }
        self.assertDictEqual(
            expected_ramp_up_when_on_rate, actual_ramp_down_when_on_rate
        )

        # Param: gen_commit_cap_ramp_down_when_on_rate
        expected_ramp_down_when_on_rate = {
            "Gas_CCGT": 0.5,
            "Coal": 0.3,
            "Gas_CT": 0.2,
            "Gas_CCGT_New": 0.8,
            "Gas_CCGT_New_Binary": 0.8,
            "Gas_CT_New": 0.5,
            "Gas_CCGT_z2": 1,
            "Coal_z2": 1,
            "Gas_CT_z2": 1,
        }
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_cap_ramp_down_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_CAP
        }
        self.assertDictEqual(
            expected_ramp_down_when_on_rate, actual_ramp_down_when_on_rate
        )

        # Param: gen_commit_cap_min_up_time_hours
        expected_min_up_time = OrderedDict(
            sorted(
                {
                    "Gas_CCGT": 3,
                    "Coal": 2,
                    "Gas_CT": 5,
                    "Gas_CCGT_New": 8,
                    "Gas_CCGT_New_Binary": 8,
                    "Gas_CT_New": 5,
                    "Gas_CCGT_z2": 1,
                    "Coal_z2": 1,
                    "Gas_CT_z2": 1,
                }.items()
            )
        )
        actual_min_up_time = OrderedDict(
            sorted(
                {
                    prj: instance.gen_commit_cap_min_up_time_hours[prj]
                    for prj in instance.GEN_COMMIT_CAP
                }.items()
            )
        )
        self.assertDictEqual(expected_min_up_time, actual_min_up_time)

        # Param: gen_commit_cap_min_down_time_hours
        expected_min_down_time = OrderedDict(
            sorted(
                {
                    "Gas_CCGT": 7,
                    "Coal": 10,
                    "Gas_CT": 3,
                    "Gas_CCGT_New": 5,
                    "Gas_CCGT_New_Binary": 5,
                    "Gas_CT_New": 2,
                    "Gas_CCGT_z2": 1,
                    "Coal_z2": 1,
                    "Gas_CT_z2": 1,
                }.items()
            )
        )
        actual_min_down_time = OrderedDict(
            sorted(
                {
                    prj: instance.gen_commit_cap_min_down_time_hours[prj]
                    for prj in instance.GEN_COMMIT_CAP
                }.items()
            )
        )
        self.assertDictEqual(expected_min_down_time, actual_min_down_time)


if __name__ == "__main__":
    unittest.main()
