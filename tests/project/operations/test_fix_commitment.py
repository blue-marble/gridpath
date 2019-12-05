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

from tests.project.operations.common_functions import \
    get_project_operational_timepoints

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity", "project.availability.availability",
    "project.fuels", "project.operations",
    "project.operations.operational_types", "project.operations.power"]
NAME_OF_MODULE_BEING_TESTED = "project.operations.fix_commitment"
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


class TestFixCommitment(unittest.TestCase):
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
                              subproblem="202001",
                              stage="ha"
                              )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="202001",
                                     stage="ha"
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
            subproblem="202001",
            stage="ha"
        )
        instance = m.create_instance(data)

        # Set: FINAL_COMMITMENT_PROJECTS
        expected_final_projects = sorted([
            "Gas_CCGT", "Gas_CCGT_New", "Gas_CCGT_New_Binary", "Gas_CCGT_z2",
            "Disp_Binary_Commit", "Disp_Cont_Commit", "Clunky_Old_Gen",
            "Clunky_Old_Gen2", "Coal", "Coal_z2"
        ])
        actual_final_projects = sorted([
            prj for prj in instance.FINAL_COMMITMENT_PROJECTS
        ])
        self.assertListEqual(expected_final_projects, actual_final_projects)

        # Set: FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        # Note: this should be getting the timepoints from the
        # scenario-horizon-stage inputs directory, not the timepoints from the
        # root scenario directory. For simplicity we have made both inputs
        # the same though realistically in the horizon 202001 folder you
        # wouldn't have timepoints in period 2030 or horizon 202002.

        expected_final_prj_op_tmps = sorted(
            get_project_operational_timepoints(expected_final_projects)
        )
        actual_final_prj_op_tmps = sorted([
            (prj, tmp) for (prj, tmp)
            in instance.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_final_prj_op_tmps,
                             actual_final_prj_op_tmps)

        # Set: FIXED_COMMITMENT_PROJECTS
        expected_fixed_projects = sorted([
            "Coal", "Coal_z2"
        ])
        actual_fixed_projects = sorted([
            prj for prj in instance.FIXED_COMMITMENT_PROJECTS
        ])
        self.assertListEqual(expected_fixed_projects,
                             actual_fixed_projects)

        expected_fixed_prj_op_tmps = sorted(
            get_project_operational_timepoints(expected_fixed_projects)
        )
        actual_fixed_prj_op_tmps = sorted([
            (prj, tmp) for (prj, tmp) 
            in instance.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS
        ])

        self.assertListEqual(expected_fixed_prj_op_tmps,
                             actual_fixed_prj_op_tmps)

        # Param: fixed_commitment
        expected_fixed_commitment = OrderedDict(sorted(
            {(p, tmp): 6 for (p, tmp) in expected_fixed_prj_op_tmps}.items()))

        actual_fixed_commitment = OrderedDict(sorted({
            (prj, tmp): instance.fixed_commitment[prj, tmp] for (prj, tmp)
            in instance.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS}.items()
                                                     )
                                              )

        self.assertDictEqual(expected_fixed_commitment,
                             actual_fixed_commitment)


if __name__ == "__main__":
    unittest.main()
