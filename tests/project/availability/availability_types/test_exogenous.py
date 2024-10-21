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
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "project",
    "project.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "project.availability.availability_types.exogenous"
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

        # Set: AVL_EXOG
        expected_project_subset = sorted(
            [
                "Nuclear",
                "Coal",
                "Wind",
                "Gas_CCGT_New",
                "Gas_CCGT_New_Binary",
                "Gas_CT_New",
                "Nuclear_z2",
                "Gas_CCGT_z2",
                "Coal_z2",
                "Gas_CT_z2",
                "Wind_z2",
                "Battery",
                "Battery_Binary",
                "Battery_Specified",
                "Hydro",
                "Hydro_NonCurtailable",
                "Disp_Binary_Commit",
                "Disp_Cont_Commit",
                "Disp_No_Commit",
                "Clunky_Old_Gen",
                "Clunky_Old_Gen2",
                "Customer_PV",
                "Nuclear_Flexible",
                "Shift_DR",
                "Wind_Battery_Hybrid",
                "Fuel_Prod",
                "Fuel_Prod_New",
                "DAC",
                "Flex_Load",
            ]
        )
        actual_project_subset = sorted([prj for prj in instance.AVL_EXOG])
        self.assertListEqual(expected_project_subset, actual_project_subset)

        # Set: AVL_EXOG_OPR_TMPS
        expected_operational_timepoints_by_project = sorted(
            get_project_operational_timepoints(expected_project_subset)
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in instance.AVL_EXOG_OPR_TMPS]
        )
        self.assertListEqual(
            expected_operational_timepoints_by_project,
            actual_operational_timepoints_by_project,
        )

        # Param: availability_derate_independent
        availability_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY,
                "inputs",
                "project_availability_exogenous_independent.tab",
            ),
            sep="\t",
        )
        defaults = {(p, tmp): 1 for (p, tmp) in instance.AVL_EXOG_OPR_TMPS}
        derates = {
            (p, tmp): avail
            for p, tmp, avail in zip(
                availability_df.project,
                availability_df.timepoint,
                availability_df.availability_derate_independent,
            )
        }
        expected_availability_derate = dict()
        for p, tmp in defaults.keys():
            if (p, tmp) in derates.keys():
                expected_availability_derate[p, tmp] = derates[p, tmp]
            else:
                expected_availability_derate[p, tmp] = defaults[p, tmp]
        actual_availability_derate = {
            (prj, tmp): instance.avl_exog_cap_derate_independent[prj, tmp]
            for (prj, tmp) in instance.AVL_EXOG_OPR_TMPS
        }

        self.assertDictEqual(expected_availability_derate, actual_availability_derate)

        # Param: availability_derate_weather
        availability_df_w = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY,
                "inputs",
                "project_availability_exogenous_weather.tab",
            ),
            sep="\t",
        )
        defaults = {(p, tmp): 1 for (p, tmp) in instance.AVL_EXOG_OPR_TMPS}
        derates = {
            (p, tmp): avail
            for p, tmp, avail in zip(
                availability_df_w.project,
                availability_df_w.timepoint,
                availability_df_w.availability_derate_weather,
            )
        }
        expected_availability_derate_w = dict()
        for p, tmp in defaults.keys():
            if (p, tmp) in derates.keys():
                expected_availability_derate_w[p, tmp] = derates[p, tmp]
            else:
                expected_availability_derate_w[p, tmp] = defaults[p, tmp]
        actual_availability_derate_w = {
            (prj, tmp): instance.avl_exog_cap_derate_weather[prj, tmp]
            for (prj, tmp) in instance.AVL_EXOG_OPR_TMPS
        }

        self.assertDictEqual(
            expected_availability_derate_w, actual_availability_derate_w
        )


if __name__ == "__main__":
    unittest.main()
