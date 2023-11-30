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

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "project",
    "project.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_groups"
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


class TestCapacityGroups(unittest.TestCase):
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

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected.
        Capacity-type modules should have added appropriate data;
        make sure it is all as expected.
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

        # Set: CAPACITY_GROUP_PERIODS
        expected_cap_group_periods = sorted(
            [("Capacity_Group1", 2020), ("Capacity_Group1", 2030)]
        )
        actual_cap_group_periods = sorted(
            [(prj, period) for (prj, period) in instance.CAPACITY_GROUP_PERIODS]
        )
        self.assertListEqual(expected_cap_group_periods, actual_cap_group_periods)

        # Set: CAPACITY_GROUPS
        expected_cap_group_periods = sorted(["Capacity_Group1"])
        actual_cap_group_periods = sorted([g for g in instance.CAPACITY_GROUPS])
        self.assertListEqual(expected_cap_group_periods, actual_cap_group_periods)

        # Set: PROJECTS_IN_CAPACITY_GROUP
        expected_prj_in_cap_group = {
            "Capacity_Group1": ["Gas_CCGT_New", "Gas_CCGT_New_Binary", "Gas_CT_New"]
        }
        actual_prj_in_cap_group = {
            g: [p for p in instance.PROJECTS_IN_CAPACITY_GROUP[g]]
            for g in instance.CAPACITY_GROUPS
        }
        self.assertDictEqual(expected_prj_in_cap_group, actual_prj_in_cap_group)

        # Params: capacity_group_new_capacity_min
        expected_new_min = {
            ("Capacity_Group1", 2020): 1,
            ("Capacity_Group1", 2030): 1,
        }
        actual_new_min = {
            (g, p): instance.capacity_group_new_capacity_min[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_new_min, actual_new_min)

        # Params: capacity_group_new_capacity_max
        expected_new_max = {
            ("Capacity_Group1", 2020): 10,
            ("Capacity_Group1", 2030): 10,
        }
        actual_new_max = {
            (g, p): instance.capacity_group_new_capacity_max[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_new_max, actual_new_max)

        # Params: capacity_group_total_capacity_min
        expected_total_min = {
            ("Capacity_Group1", 2020): 2,
            ("Capacity_Group1", 2030): 5,
        }
        actual_total_min = {
            (g, p): instance.capacity_group_total_capacity_min[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_total_min, actual_total_min)

        # Params: capacity_group_total_capacity_max
        expected_total_max = {
            ("Capacity_Group1", 2020): 20,
            ("Capacity_Group1", 2030): 50,
        }
        actual_total_max = {
            (g, p): instance.capacity_group_total_capacity_max[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_total_max, actual_total_max)
