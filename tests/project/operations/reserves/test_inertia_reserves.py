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
from tests.project.operations.common_functions import get_project_operational_timepoints

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "geography.inertia_reserves_balancing_areas",
    "project",
    "project.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "project.operations.reserves.inertia_reserves"
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


class TestLFReservesUpProvision(unittest.TestCase):
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

        # Set: SPINNING_RESERVES_PROJECTS
        expected_projects = sorted(
            [
                "Nuclear",
                "Gas_CCGT",
                "Coal",
                "Gas_CT",
                "Gas_CCGT_New",
                "Gas_CCGT_New_Binary",
                "Gas_CT_New",
            ]
        )
        actual_projects = sorted([prj for prj in instance.INERTIA_RESERVES_PROJECTS])
        self.assertListEqual(expected_projects, actual_projects)

        # Param: inertia_reserves_zone
        expected_reserves_zone = OrderedDict(
            sorted(
                {
                    "Nuclear": "Zone1",
                    "Gas_CCGT": "Zone1",
                    "Coal": "Zone1",
                    "Gas_CT": "Zone1",
                    "Gas_CCGT_New": "Zone1",
                    "Gas_CCGT_New_Binary": "Zone1",
                    "Gas_CT_New": "Zone1",
                }.items()
            )
        )
        actual_reserves_zone = OrderedDict(
            sorted(
                {
                    prj: instance.inertia_reserves_zone[prj]
                    for prj in instance.INERTIA_RESERVES_PROJECTS
                }.items()
            )
        )
        self.assertDictEqual(expected_reserves_zone, actual_reserves_zone)

        # Set: INERTIA_RESERVES_PRJ_OPR_TMPS
        expected_prj_op_tmps = sorted(
            get_project_operational_timepoints(expected_projects)
        )
        actual_prj_op_tmps = sorted(
            [(prj, tmp) for (prj, tmp) in instance.INERTIA_RESERVES_PRJ_OPR_TMPS]
        )
        self.assertListEqual(expected_prj_op_tmps, actual_prj_op_tmps)

        # Param: inertia_reserves_derate (defaults to 1 if not specified)
        expected_derate = OrderedDict(
            sorted(
                {
                    "Nuclear": 1,
                    "Gas_CCGT": 1,
                    "Coal": 0.5,
                    "Gas_CT": 1,
                    "Gas_CCGT_New": 1,
                    "Gas_CCGT_New_Binary": 1,
                    "Gas_CT_New": 1,
                }.items()
            )
        )
        actual_derate = OrderedDict(
            sorted(
                {
                    prj: instance.inertia_reserves_derate[prj]
                    for prj in instance.INERTIA_RESERVES_PROJECTS
                }.items()
            )
        )
        self.assertDictEqual(expected_derate, actual_derate)


if __name__ == "__main__":
    unittest.main()
