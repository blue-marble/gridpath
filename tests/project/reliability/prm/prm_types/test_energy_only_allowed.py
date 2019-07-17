#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                 "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones",
    "geography.prm_zones", "project", "project.capacity.capacity",
    "project.reliability.prm"
]
NAME_OF_MODULE_BEING_TESTED = \
    "project.reliability.prm.prm_types.energy_only_allowed"
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
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package="gridpath")
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestProjPRMTypeFullyDeliverable(unittest.TestCase):
    """

    """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=IMPORTED_PREREQ_MODULES,
                              module_to_test=MODULE_BEING_TESTED,
                              test_data_dir=TEST_DATA_DIRECTORY,
                              subproblem="",
                              stage=""
                              )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
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
            stage=""
        )
        instance = m.create_instance(data)

        # Set: EOA_PRM_PROJECTS
        expected_projects = sorted([
            "Wind", "Wind_z2"]
        )
        actual_projects = sorted([
            prj for prj in instance.EOA_PRM_PROJECTS
        ])

        self.assertListEqual(expected_projects, actual_projects)

        # Set: EOA_PRM_PROJECT_OPERATIONAL_PERIODS
        expected_proj_period_set = sorted([
            ("Wind", 2020), ("Wind_z2", 2020),
            ("Wind", 2030), ("Wind_z2", 2030)
        ])
        actual_proj_period_set = sorted([
            (prj, period) for (prj, period)
            in instance.EOA_PRM_PROJECT_OPERATIONAL_PERIODS
        ])

        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)

        # Set: DELIVERABILITY_GROUPS
        expected_deliverability_groups_set = sorted([
            "Threshold_Group_1", "Threshold_Group_2"
        ])
        actual_deliverability_groups_set = sorted([
            g for g in instance.DELIVERABILITY_GROUPS
        ])

        self.assertListEqual(expected_deliverability_groups_set,
                             actual_deliverability_groups_set)

        # Param: deliverability_group_no_cost_deliverable_capacity_mw
        expected_no_cost_deliv_cap = OrderedDict(
            sorted({
                "Threshold_Group_1": 2000.0, "Threshold_Group_2": 1140.0
            }.items()
                   )
        )
        actual_no_cost_deliv_cap = OrderedDict(sorted(
            {g: instance.deliverability_group_no_cost_deliverable_capacity_mw[
                g]
             for g in instance.DELIVERABILITY_GROUPS}.items()
        )
        )

        self.assertDictEqual(expected_no_cost_deliv_cap,
                             actual_no_cost_deliv_cap)

        # Param: deliverability_group_deliverability_cost_per_mw
        expected_deliv_cost = OrderedDict(
            sorted({
                "Threshold_Group_1": 37.0, "Threshold_Group_2": 147.0
                   }.items()
                   )
        )
        actual_deliv_cost = OrderedDict(sorted(
            {g: instance.deliverability_group_deliverability_cost_per_mw[g]
             for g in instance.DELIVERABILITY_GROUPS}.items()
        )
        )

        self.assertDictEqual(expected_deliv_cost,
                             actual_deliv_cost)

        # Param: deliverability_group_energy_only_capacity_limit_mw
        expected_energy_only_limit = OrderedDict(
            sorted({
                "Threshold_Group_1": 4000, "Threshold_Group_2": 5000
                   }.items()
                   )
        )
        actual_energy_only_limit = OrderedDict(sorted(
            {g: instance.deliverability_group_energy_only_capacity_limit_mw[g]
             for g in instance.DELIVERABILITY_GROUPS}.items()
        )
        )

        self.assertDictEqual(expected_energy_only_limit,
                             actual_energy_only_limit)

        # Set: DELIVERABILITY_GROUP_PROJECTS
        expected_deliverability_group_projects = sorted([
            ("Threshold_Group_1", "Wind"),
            ("Threshold_Group_2", "Wind_z2")
        ])
        actual_deliverability_group_projects = sorted([
            (g, p) for (g, p) in instance.DELIVERABILITY_GROUP_PROJECTS
        ])

        self.assertListEqual(expected_deliverability_group_projects,
                             actual_deliverability_group_projects)

        # Set: PROJECTS_BY_DELIVERABILITY_GROUP
        expected_prj_by_grp = OrderedDict(
            sorted({
                "Threshold_Group_1": ["Wind"], "Threshold_Group_2": ["Wind_z2"]
                   }.items()
                   )
        )
        actual_prj_by_grp = OrderedDict(sorted(
            {g: [p for p in instance.PROJECTS_BY_DELIVERABILITY_GROUP[g]]
             for g in instance.DELIVERABILITY_GROUPS}.items()
        )
        )

        self.assertDictEqual(expected_prj_by_grp,
                             actual_prj_by_grp)

if __name__ == "__main__":
    unittest.main()
