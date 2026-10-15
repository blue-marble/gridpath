# Copyright 2016-2024 Blue Marble Analytics LLC.
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
    "temporal.investment.periods",
    "temporal.operations.horizons",
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
            [
                ("Capacity_Group1", 2020),
                ("Capacity_Group1", 2030),
                ("Energy_Group", 2020),
                ("Energy_Group", 2030),
            ]
        )
        actual_cap_group_periods = sorted(
            [(prj, period) for (prj, period) in instance.CAPACITY_GROUP_PERIODS]
        )
        self.assertListEqual(expected_cap_group_periods, actual_cap_group_periods)

        # Set: CAPACITY_GROUPS
        expected_cap_group_periods = sorted(["Capacity_Group1", "Energy_Group"])
        actual_cap_group_periods = sorted([g for g in instance.CAPACITY_GROUPS])
        self.assertListEqual(expected_cap_group_periods, actual_cap_group_periods)

        # Set: PROJECTS_IN_CAPACITY_GROUP
        expected_prj_in_cap_group = {
            "Capacity_Group1": ["Gas_CCGT_New", "Gas_CCGT_New_Binary", "Gas_CT_New"],
            "Energy_Group": [
                "Energy_Spec",
                "Energy_Hrz_Shaping",
                "Energy_LF",
                "Energy_Slice_Hrz_Shaping",
            ],
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
            ("Energy_Group", 2020): 0,
            ("Energy_Group", 2030): 0,
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
            ("Energy_Group", 2020): float("inf"),
            ("Energy_Group", 2030): float("inf"),
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
            ("Energy_Group", 2020): 0,
            ("Energy_Group", 2030): 0,
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
            ("Energy_Group", 2020): float("inf"),
            ("Energy_Group", 2030): float("inf"),
        }
        actual_total_max = {
            (g, p): instance.capacity_group_total_capacity_max[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_total_max, actual_total_max)

        # Params: energy_group_new_energy_min
        expected_new_emin = {
            ("Capacity_Group1", 2020): 0,
            ("Capacity_Group1", 2030): 0,
            ("Energy_Group", 2020): 0,
            ("Energy_Group", 2030): 0,
        }
        actual_new_emin = {
            (g, p): instance.energy_group_new_energy_min[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }

        self.assertDictEqual(expected_new_emin, actual_new_emin)

        # Params: energy_group_new_energy_max
        expected_new_emax = {
            ("Capacity_Group1", 2020): float("inf"),
            ("Capacity_Group1", 2030): float("inf"),
            ("Energy_Group", 2020): float("inf"),
            ("Energy_Group", 2030): float("inf"),
        }
        actual_new_emax = {
            (g, p): instance.energy_group_new_energy_max[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_new_emax, actual_new_emax)

        # Params: energy_group_total_energy_min
        expected_total_emin = {
            ("Capacity_Group1", 2020): 0,
            ("Capacity_Group1", 2030): 0,
            ("Energy_Group", 2020): 0,
            ("Energy_Group", 2030): 0,
        }
        actual_total_emin = {
            (g, p): instance.energy_group_total_energy_min[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_total_emin, actual_total_emin)

        # Params: energy_group_total_energy_max
        expected_total_emax = {
            ("Capacity_Group1", 2020): float("inf"),
            ("Capacity_Group1", 2030): float("inf"),
            ("Energy_Group", 2020): 1000,
            ("Energy_Group", 2030): 1000,
        }
        actual_total_emax = {
            (g, p): instance.energy_group_total_energy_max[g, p]
            for (g, p) in instance.CAPACITY_GROUP_PERIODS
        }
        self.assertDictEqual(expected_total_emax, actual_total_emax)

    def test_limit_constraints_built_only_where_limits_are_specified(self):
        """
        A group-period whose limit is left at its default (0 for a minimum,
        infinity for a maximum) gets no constraint row at all: the energy
        maxima of the fixture are all unspecified, so the energy-build
        maximum has no indices, while the capacity constraints exist only
        for the group with capacity limits.
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

        capacity_group_periods = [("Capacity_Group1", 2020), ("Capacity_Group1", 2030)]
        energy_group_periods = [("Energy_Group", 2020), ("Energy_Group", 2030)]
        for constraint in [
            instance.Max_Group_Capacity_Build_in_Period_Constraint,
            instance.Min_Group_Capacity_Build_in_Period_Constraint,
            instance.Max_Group_Total_Capacity_in_Period_Constraint,
            instance.Min_Group_Total_Capacity_in_Period_Constraint,
        ]:
            self.assertListEqual(sorted(constraint.keys()), capacity_group_periods)
        # Energy_Group specifies only a total-energy maximum; Capacity_Group1
        # specifies no energy limits (the new-energy maximum used to be
        # gated on the capacity maximum and built rows with an infinite RHS)
        self.assertListEqual(
            sorted(instance.Max_Group_Total_Energy_in_Period_Constraint.keys()),
            energy_group_periods,
        )
        for constraint in [
            instance.Max_Group_Energy_Build_in_Period_Constraint,
            instance.Min_Group_Energy__Build_in_Period_Constraint,
            instance.Min_Group_Total_Energy_in_Period_Constraint,
        ]:
            self.assertEqual(len(constraint), 0)
