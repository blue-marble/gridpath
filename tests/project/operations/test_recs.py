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
    "temporal.investment.periods", "geography.load_zones",
    "geography.rps_zones", "system.policy.rps.rps_requirement",
    "project", "project.capacity.capacity", "project.fuels",
    "project.operations", "project.operations.operational_types",
    "project.operations.power"]
NAME_OF_MODULE_BEING_TESTED = "project.operations.recs"
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


class TestRECs(unittest.TestCase):
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
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     horizon="",
                                     stage=""
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
            horizon="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: RPS_PROJECTS
        expected_rps_projects = sorted(["Wind", "Wind_z2"])
        actual_rps_projects = sorted([p for p in instance.RPS_PROJECTS])
        self.assertListEqual(expected_rps_projects, actual_rps_projects)

        # Param: rps_zone
        expected_rps_zone_by_prj = OrderedDict(sorted({
           "Wind": "RPS_Zone_1", "Wind_z2": "RPS_Zone_2"
                                                      }.items()
                                                      )
                                               )
        actual_rps_zone_by_prj = OrderedDict(sorted({
            p: instance.rps_zone[p] for p in instance.RPS_PROJECTS}.items()
                                                    )
                                             )
        self.assertDictEqual(expected_rps_zone_by_prj, actual_rps_zone_by_prj)

        # Set: RPS_PROJECTS_BY_RPS_ZONE
        expected_prj_by_zone = OrderedDict(sorted({
            "RPS_Zone_1": ["Wind"], "RPS_Zone_2": ["Wind_z2"]
                                                  }.items()
                                                  )
                                           )
        actual_prj_by_zone = OrderedDict(sorted({
            z: [p for p in instance.RPS_PROJECTS_BY_RPS_ZONE[z]]
            for z in instance.RPS_ZONES
                                                }.items()
                                                )
                                         )
        self.assertDictEqual(expected_prj_by_zone, actual_prj_by_zone)

        # Set: RPS_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_rps_prj_op_tmp = sorted(
            get_project_operational_timepoints(expected_rps_projects)
        )

        actual_rps_prj_op_tmp = sorted([
            (prj, tmp) for (prj, tmp)
            in instance.RPS_PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_rps_prj_op_tmp, actual_rps_prj_op_tmp)


if __name__ == "__main__":
    unittest.main()
