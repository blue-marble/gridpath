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
    "project.availability.availability",
    "project.fuels",
    "project.operations",
]
NAME_OF_MODULE_BEING_TESTED = "project.operations.operational_types.flex_load"
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


class TestFlexLoad(unittest.TestCase):
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

    def test_capacity_data_load_correctly(self):
        """
        Test that are data loaded are as expected
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

        # Sets: FLEX_LOAD
        expected_projects = ["Flex_Load"]
        actual_projects = sorted([p for p in instance.FLEX_LOAD])
        self.assertListEqual(expected_projects, actual_projects)

        # FLEX_LOAD_OPR_TMPS
        expected_tmps = sorted(get_project_operational_timepoints(expected_projects))
        actual_tmps = sorted([tmp for tmp in instance.FLEX_LOAD_OPR_TMPS])
        self.assertListEqual(expected_tmps, actual_tmps)

        # Param: flex_load_charging_efficiency
        expected_charging_efficiency = {
            "Flex_Load": 0.9,
        }
        actual_charging_efficiency = {
            prj: instance.flex_load_charging_efficiency[prj]
            for prj in instance.FLEX_LOAD
        }
        self.assertDictEqual(expected_charging_efficiency, actual_charging_efficiency)

        # Param: flex_load_discharging_efficiency
        expected_discharging_efficiency = {
            "Flex_Load": 0.8,
        }
        actual_discharging_efficiency = {
            prj: instance.flex_load_discharging_efficiency[prj]
            for prj in instance.FLEX_LOAD
        }
        self.assertDictEqual(
            expected_discharging_efficiency, actual_discharging_efficiency
        )

        # Param: flex_load_storage_efficiency
        expected_storage_efficiency = {
            "Flex_Load": 0.5,
        }
        actual_storage_efficiency = {
            prj: instance.flex_load_storage_efficiency[prj]
            for prj in instance.FLEX_LOAD
        }
        self.assertDictEqual(expected_storage_efficiency, actual_storage_efficiency)

        # Param: flex_load_static_profile_mw
        df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "flex_load_profiles.tab"),
            sep="\t",
        )

        expected_profile = df.set_index(["project", "timepoint"]).to_dict()[
            "static_profile_mw"
        ]

        actual_profile = {
            (prj, tmp): instance.flex_load_static_profile_mw[prj, tmp]
            for (prj, tmp) in instance.FLEX_LOAD_OPR_TMPS
        }
        self.assertDictEqual(expected_profile, actual_profile)

        # Param: flex_load_maximum_stored_energy_mwh
        expected_max_stor = df.set_index(["project", "timepoint"]).to_dict()[
            "maximum_stored_energy_mwh"
        ]

        actual_max_stor = {
            (prj, tmp): instance.flex_load_maximum_stored_energy_mwh[prj, tmp]
            for (prj, tmp) in instance.FLEX_LOAD_OPR_TMPS
        }
        self.assertDictEqual(expected_max_stor, actual_max_stor)


if __name__ == "__main__":
    unittest.main()
