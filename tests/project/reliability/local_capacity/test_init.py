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
    "geography.local_capacity_zones",
    "project",
    "project.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "project.reliability.local_capacity"
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


class TestProjLocalCapacityInit(unittest.TestCase):
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

        # Check data are as expected
        # Set: LOCAL_CAPACITY_PROJECTS
        expected_projects = sorted(
            [
                "Nuclear",
                "Gas_CCGT",
                "Coal",
                "Gas_CT",
                "Gas_CCGT_New",
                "Gas_CCGT_New_Binary",
                "Gas_CT_New",
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
                "Nuclear_Flexible",
                "Shift_DR",
            ]
        )
        actual_projects = sorted([prj for prj in instance.LOCAL_CAPACITY_PROJECTS])

        self.assertListEqual(expected_projects, actual_projects)

        # Params: local_capacity_zone
        expected_zone = OrderedDict(
            sorted(
                {
                    "Nuclear": "Local_Capacity_Zone1",
                    "Gas_CCGT": "Local_Capacity_Zone1",
                    "Coal": "Local_Capacity_Zone2",
                    "Gas_CT": "Local_Capacity_Zone2",
                    "Gas_CCGT_New": "Local_Capacity_Zone1",
                    "Gas_CCGT_New_Binary": "Local_Capacity_Zone1",
                    "Gas_CT_New": "Local_Capacity_Zone2",
                    "Battery": "Local_Capacity_Zone1",
                    "Battery_Binary": "Local_Capacity_Zone1",
                    "Battery_Specified": "Local_Capacity_Zone2",
                    "Hydro": "Local_Capacity_Zone1",
                    "Hydro_NonCurtailable": "Local_Capacity_Zone2",
                    "Disp_Binary_Commit": "Local_Capacity_Zone1",
                    "Disp_Cont_Commit": "Local_Capacity_Zone2",
                    "Disp_No_Commit": "Local_Capacity_Zone1",
                    "Clunky_Old_Gen": "Local_Capacity_Zone2",
                    "Clunky_Old_Gen2": "Local_Capacity_Zone2",
                    "Nuclear_Flexible": "Local_Capacity_Zone1",
                    "Shift_DR": "Local_Capacity_Zone2",
                }.items()
            )
        )
        actual_zone = OrderedDict(
            sorted(
                {
                    prj: instance.local_capacity_zone[prj]
                    for prj in instance.LOCAL_CAPACITY_PROJECTS
                }.items()
            )
        )
        self.assertDictEqual(expected_zone, actual_zone)

        # Set: LOCAL_CAPACITY_PROJECTS_BY_LOCAL_CAPACITY_ZONE
        expected_projects_by_zone = {
            "Local_Capacity_Zone1": sorted(
                [
                    "Nuclear",
                    "Gas_CCGT",
                    "Gas_CCGT_New",
                    "Gas_CCGT_New_Binary",
                    "Battery",
                    "Battery_Binary",
                    "Hydro",
                    "Disp_Binary_Commit",
                    "Disp_No_Commit",
                    "Nuclear_Flexible",
                ]
            ),
            "Local_Capacity_Zone2": sorted(
                [
                    "Coal",
                    "Gas_CT",
                    "Gas_CT_New",
                    "Battery_Specified",
                    "Hydro_NonCurtailable",
                    "Disp_Cont_Commit",
                    "Clunky_Old_Gen",
                    "Clunky_Old_Gen2",
                    "Shift_DR",
                ]
            ),
        }
        actual_projects_by_zone = {
            z: sorted(
                [
                    prj
                    for prj in instance.LOCAL_CAPACITY_PROJECTS_BY_LOCAL_CAPACITY_ZONE[
                        z
                    ]
                ]
            )
            for z in instance.LOCAL_CAPACITY_ZONES
        }

        self.assertDictEqual(expected_projects_by_zone, actual_projects_by_zone)

        # Set: LOCAL_CAPACITY_PRJ_OPR_PRDS
        expected_proj_period_set = sorted(
            [
                ("Nuclear", 2020),
                ("Gas_CCGT", 2020),
                ("Coal", 2020),
                ("Gas_CT", 2020),
                ("Nuclear", 2030),
                ("Gas_CCGT", 2030),
                ("Coal", 2030),
                ("Gas_CT", 2030),
                ("Battery_Specified", 2020),
                ("Gas_CCGT_New", 2020),
                ("Gas_CCGT_New", 2030),
                ("Gas_CCGT_New_Binary", 2020),
                ("Gas_CCGT_New_Binary", 2030),
                ("Gas_CT_New", 2030),
                ("Battery", 2020),
                ("Battery", 2030),
                ("Battery_Binary", 2020),
                ("Battery_Binary", 2030),
                ("Hydro", 2020),
                ("Hydro", 2030),
                ("Hydro_NonCurtailable", 2020),
                ("Hydro_NonCurtailable", 2030),
                ("Disp_Binary_Commit", 2020),
                ("Disp_Binary_Commit", 2030),
                ("Disp_Cont_Commit", 2020),
                ("Disp_Cont_Commit", 2030),
                ("Disp_No_Commit", 2020),
                ("Disp_No_Commit", 2030),
                ("Clunky_Old_Gen", 2020),
                ("Clunky_Old_Gen", 2030),
                ("Clunky_Old_Gen2", 2020),
                ("Clunky_Old_Gen2", 2030),
                ("Nuclear_Flexible", 2030),
                ("Shift_DR", 2020),
                ("Shift_DR", 2030),
            ]
        )
        actual_proj_period_set = sorted(
            [(prj, period) for (prj, period) in instance.LOCAL_CAPACITY_PRJ_OPR_PRDS]
        )

        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)


if __name__ == "__main__":
    unittest.main()
