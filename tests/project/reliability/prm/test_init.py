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
    "geography.prm_zones",
    "project",
    "project.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "project.reliability.prm"
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


class TestProjPRMInit(unittest.TestCase):
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

        # Check data are as expected
        # Set: PRM_PROJECTS
        expected_projects = sorted(
            [
                "Coal",
                "Coal_z2",
                "Gas_CCGT",
                "Gas_CCGT_New",
                "Gas_CCGT_New_Binary",
                "Gas_CCGT_z2",
                "Gas_CT",
                "Gas_CT_New",
                "Gas_CT_z2",
                "Nuclear",
                "Nuclear_z2",
                "Wind",
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
                "Nuclear_Flexible",
            ]
        )
        actual_projects = sorted([prj for prj in instance.PRM_PROJECTS])

        self.assertListEqual(expected_projects, actual_projects)

        # Params: prm_zone
        expected_prm_zone = OrderedDict(
            sorted(
                {
                    "Coal": "PRM_Zone1",
                    "Coal_z2": "PRM_Zone2",
                    "Gas_CCGT": "PRM_Zone1",
                    "Gas_CCGT_New": "PRM_Zone1",
                    "Gas_CCGT_New_Binary": "PRM_Zone1",
                    "Gas_CCGT_z2": "PRM_Zone2",
                    "Gas_CT": "PRM_Zone1",
                    "Gas_CT_New": "PRM_Zone1",
                    "Gas_CT_z2": "PRM_Zone2",
                    "Nuclear": "PRM_Zone1",
                    "Nuclear_z2": "PRM_Zone2",
                    "Wind": "PRM_Zone1",
                    "Wind_z2": "PRM_Zone2",
                    "Battery": "PRM_Zone1",
                    "Battery_Binary": "PRM_Zone1",
                    "Battery_Specified": "PRM_Zone1",
                    "Hydro": "PRM_Zone1",
                    "Hydro_NonCurtailable": "PRM_Zone1",
                    "Disp_Binary_Commit": "PRM_Zone1",
                    "Disp_Cont_Commit": "PRM_Zone1",
                    "Disp_No_Commit": "PRM_Zone1",
                    "Clunky_Old_Gen": "PRM_Zone1",
                    "Clunky_Old_Gen2": "PRM_Zone1",
                    "Nuclear_Flexible": "PRM_Zone1",
                }.items()
            )
        )
        actual_prm_zone = OrderedDict(
            sorted(
                {prj: instance.prm_zone[prj] for prj in instance.PRM_PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_prm_zone, actual_prm_zone)

        # Params: prm_type
        expected_prm_type = OrderedDict(
            sorted(
                {
                    "Coal": "fully_deliverable",
                    "Coal_z2": "fully_deliverable",
                    "Gas_CCGT": "fully_deliverable",
                    "Gas_CCGT_New": "fully_deliverable",
                    "Gas_CCGT_New_Binary": "fully_deliverable",
                    "Gas_CCGT_z2": "fully_deliverable",
                    "Gas_CT": "fully_deliverable",
                    "Gas_CT_New": "fully_deliverable",
                    "Gas_CT_z2": "fully_deliverable",
                    "Nuclear": "fully_deliverable",
                    "Nuclear_z2": "fully_deliverable",
                    "Wind": "energy_only_allowed",
                    "Wind_z2": "energy_only_allowed",
                    "Battery": "fully_deliverable_energy_limited",
                    "Battery_Binary": "fully_deliverable_energy_limited",
                    "Battery_Specified": "fully_deliverable_energy_limited",
                    "Hydro": "fully_deliverable",
                    "Hydro_NonCurtailable": "fully_deliverable",
                    "Disp_Binary_Commit": "fully_deliverable",
                    "Disp_Cont_Commit": "fully_deliverable",
                    "Disp_No_Commit": "fully_deliverable",
                    "Clunky_Old_Gen": "fully_deliverable",
                    "Clunky_Old_Gen2": "fully_deliverable",
                    "Nuclear_Flexible": "fully_deliverable",
                }.items()
            )
        )
        actual_prm_type = OrderedDict(
            sorted(
                {prj: instance.prm_type[prj] for prj in instance.PRM_PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_prm_type, actual_prm_type)

        # Set: PRM_PROJECTS_BY_PRM_ZONE
        expected_projects_by_zone = {
            "PRM_Zone1": sorted(
                [
                    "Coal",
                    "Gas_CCGT",
                    "Gas_CCGT_New",
                    "Gas_CCGT_New_Binary",
                    "Gas_CT",
                    "Gas_CT_New",
                    "Nuclear",
                    "Wind",
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
                ]
            ),
            "PRM_Zone2": sorted(
                ["Coal_z2", "Gas_CCGT_z2", "Gas_CT_z2", "Nuclear_z2", "Wind_z2"]
            ),
        }
        actual_projects_by_zone = {
            z: sorted([prj for prj in instance.PRM_PROJECTS_BY_PRM_ZONE[z]])
            for z in instance.PRM_ZONES
        }

        self.assertDictEqual(expected_projects_by_zone, actual_projects_by_zone)

        # Set: PRM_PRJ_OPR_PRDS
        expected_proj_period_set = sorted(
            [
                ("Nuclear", 2020),
                ("Gas_CCGT", 2020),
                ("Coal", 2020),
                ("Gas_CT", 2020),
                ("Wind", 2020),
                ("Nuclear", 2030),
                ("Gas_CCGT", 2030),
                ("Coal", 2030),
                ("Gas_CT", 2030),
                ("Wind", 2030),
                ("Nuclear_z2", 2020),
                ("Gas_CCGT_z2", 2020),
                ("Coal_z2", 2020),
                ("Gas_CT_z2", 2020),
                ("Wind_z2", 2020),
                ("Nuclear_z2", 2030),
                ("Gas_CCGT_z2", 2030),
                ("Coal_z2", 2030),
                ("Gas_CT_z2", 2030),
                ("Wind_z2", 2030),
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
            ]
        )
        actual_proj_period_set = sorted(
            [(prj, period) for (prj, period) in instance.PRM_PRJ_OPR_PRDS]
        )

        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)


if __name__ == "__main__":
    unittest.main()
