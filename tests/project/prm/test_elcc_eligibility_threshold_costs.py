#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones",
    "geography.prm_zones", "project",
    "project.capacity.capacity", "project.prm"]
NAME_OF_MODULE_BEING_TESTED = "project.prm.elcc_eligibility_threshold_costs"
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


class TestELCCEligibilityThresholds(unittest.TestCase):
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
                              horizon="",
                              stage=""
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
            horizon="",
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
            horizon="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: ELCC_ELIGIBILITY_THRESHOLD_GROUPS
        expected_groups = sorted(["Threshold_Group_1", "Threshold_Group_2"])
        actual_groups = sorted([
            g for g in instance.ELCC_ELIGIBILITY_THRESHOLD_GROUPS
        ])
        self.assertListEqual(expected_groups, actual_groups)

        # Param: elcc_eligibility_threshold_mw
        expected_thresholds = OrderedDict(
            sorted({"Threshold_Group_1": 2000.0,
                    "Threshold_Group_2": 1140.0}.items()
                   )
        )
        actual_thresholds = OrderedDict(
            sorted({g: instance.elcc_eligibility_threshold_mw[g]
                    for g in instance.ELCC_ELIGIBILITY_THRESHOLD_GROUPS}.items()
                   )
        )
        self.assertDictEqual(expected_thresholds, actual_thresholds)

        # Param: elcc_eligibility_threshold_cost_per_mw
        expected_costs = OrderedDict(
            sorted({"Threshold_Group_1": 37.0,
                    "Threshold_Group_2": 147.0}.items()
                   )
        )
        actual_costs = OrderedDict(
            sorted({g: instance.elcc_eligibility_threshold_cost_per_mw[g]
                    for g in instance.ELCC_ELIGIBILITY_THRESHOLD_GROUPS
                    }.items()
                   )
        )
        self.assertDictEqual(expected_costs, actual_costs)

        # Param: energy_only_limit_mw
        expected_costs = OrderedDict(
            sorted({"Threshold_Group_1": 4000.0,
                    "Threshold_Group_2": 5000.0}.items()
                   )
        )
        actual_costs = OrderedDict(
            sorted({g: instance.energy_only_limit_mw[g]
                    for g in instance.ELCC_ELIGIBILITY_THRESHOLD_GROUPS
                    }.items()
                   )
        )
        self.assertDictEqual(expected_costs, actual_costs)

        # Set: ELCC_ELIGIBILITY_THRESHOLD_GROUP_PROJECTS
        expected_group_projects = sorted(
            [("Threshold_Group_1", "Wind"),
             ("Threshold_Group_1", "Battery"),
             ("Threshold_Group_2", "Wind_z2")])
        actual_group_projects = sorted(
            [(g, p) for (g, p)
             in instance.ELCC_ELIGIBILITY_THRESHOLD_GROUP_PROJECTS])
        self.assertListEqual(expected_group_projects, actual_group_projects)

        # Set: PROJECTS_BY_ELCC_ELIGIBILITY_THRESHOLD_GROUP
        expected_projects_by_group = OrderedDict(
            sorted(
                {"Threshold_Group_1": sorted(["Wind", "Battery"]),
                 "Threshold_Group_2": sorted(["Wind_z2"])}.items()
            )
        )
        actual_projets_by_group = OrderedDict(
            sorted(
                {g: sorted([p for p in
                            instance.
                           PROJECTS_BY_ELCC_ELIGIBILITY_THRESHOLD_GROUP[g]])
                 for g in instance.ELCC_ELIGIBILITY_THRESHOLD_GROUPS}.items()
            )
        )
        self.assertDictEqual(expected_projects_by_group,
                             actual_projets_by_group)


if __name__ == "__main__":
    unittest.main()
