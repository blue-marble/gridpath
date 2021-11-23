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

from importlib import import_module
import os.path
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data
from tests.project.operations.common_functions import get_project_operational_timepoints

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

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
    "project.operations.operational_types",
    "project.operations.power",
]
NAME_OF_MODULE_BEING_TESTED = "project.operations.fuel_burn"
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


class TestFuelBurn(unittest.TestCase):
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

        # Load test data as dataframes
        projects_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "projects.tab"), sep="\t"
        )

        hr_curve_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "heat_rate_curves.tab"),
            sep="\t",
        )

        timepoints_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
            sep="\t",
            usecols=["timepoint", "period"],
        )

        # Set: FUEL_PRJ_OPR_TMPS
        expected_fuel_projects = sorted(
            projects_df[projects_df["fuel"] != "."]["project"].tolist()
        )
        expected_fuel_prj_tmps = get_project_operational_timepoints(
            expected_fuel_projects
        )
        actual_fuel_prj_tmps = sorted(
            [(p, tmp) for (p, tmp) in instance.FUEL_PRJ_OPR_TMPS]
        )

        self.assertListEqual(expected_fuel_prj_tmps, actual_fuel_prj_tmps)

        # Set: HR_CURVE_PRJS_OPR_TMPS
        expected_hr_curve_projects = sorted(hr_curve_df["project"].unique().tolist())

        expected_hr_curve_prj_tmps = get_project_operational_timepoints(
            expected_hr_curve_projects
        )

        actual_hr_curve_prj_tmps = sorted(
            [(p, tmp) for (p, tmp) in instance.HR_CURVE_PRJS_OPR_TMPS]
        )

        self.assertListEqual(expected_hr_curve_prj_tmps, actual_hr_curve_prj_tmps)

        # Set: HR_CURVE_PRJS_OPR_TMPS_SGMS
        expected_segments_by_prj_period = {
            ("Coal", 2020): [0],
            ("Coal", 2030): [0],
            ("Gas_CCGT", 2020): [0],
            ("Gas_CCGT", 2030): [0],
            ("Gas_CT", 2020): [0],
            ("Gas_CT", 2030): [0],
            ("Nuclear", 2020): [0],
            ("Nuclear", 2030): [0],
            ("Gas_CCGT_New", 2020): [0],
            ("Gas_CCGT_New", 2030): [0],
            ("Gas_CCGT_New_Binary", 2020): [0],
            ("Gas_CCGT_New_Binary", 2030): [0],
            ("Gas_CT_New", 2020): [0],
            ("Gas_CT_New", 2030): [0],
            ("Coal_z2", 2020): [0],
            ("Coal_z2", 2030): [0],
            ("Gas_CCGT_z2", 2020): [0],
            ("Gas_CCGT_z2", 2030): [0],
            ("Gas_CT_z2", 2020): [0],
            ("Gas_CT_z2", 2030): [0],
            ("Nuclear_z2", 2020): [0],
            ("Nuclear_z2", 2030): [0],
            ("Disp_Binary_Commit", 2020): [0],
            ("Disp_Binary_Commit", 2030): [0],
            ("Disp_Cont_Commit", 2020): [0],
            ("Disp_Cont_Commit", 2030): [0],
            ("Disp_No_Commit", 2020): [0],
            ("Disp_No_Commit", 2030): [0],
            ("Clunky_Old_Gen", 2020): [0],
            ("Clunky_Old_Gen", 2030): [0],
            ("Clunky_Old_Gen2", 2020): [0],
            ("Clunky_Old_Gen2", 2030): [0],
            ("Nuclear_Flexible", 2020): [0],
            ("Nuclear_Flexible", 2030): [0],
        }
        expected_hr_curve_prj_tmp_sgms = list()
        for (prj, tmp) in expected_hr_curve_prj_tmps:
            prd = timepoints_df[timepoints_df["timepoint"] == tmp].iloc[0]["period"]
            segments = expected_segments_by_prj_period[prj, prd]
            for sgm in segments:
                expected_hr_curve_prj_tmp_sgms.append((prj, tmp, sgm))

        actual_hr_curve_prj_tmp_sgms = sorted(
            [
                (prj, tmp, sgm)
                for (prj, tmp, sgm) in instance.HR_CURVE_PRJS_OPR_TMPS_SGMS
            ]
        )

        self.assertListEqual(
            expected_hr_curve_prj_tmp_sgms, actual_hr_curve_prj_tmp_sgms
        )

        # Set: STARTUP_FUEL_PRJ_OPR_TMPS
        expected_startup_fuel_projects = sorted(
            projects_df[projects_df["startup_fuel_mmbtu_per_mw"] != "."][
                "project"
            ].tolist()
        )
        expected_startup_fuel_prj_tmps = get_project_operational_timepoints(
            expected_startup_fuel_projects
        )
        actual_startup_fuel_prj_tmps = sorted(
            [(p, tmp) for (p, tmp) in instance.STARTUP_FUEL_PRJ_OPR_TMPS]
        )

        self.assertListEqual(
            expected_startup_fuel_prj_tmps, actual_startup_fuel_prj_tmps
        )


if __name__ == "__main__":
    unittest.main()
