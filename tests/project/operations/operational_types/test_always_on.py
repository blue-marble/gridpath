#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data
from tests.project.operations.common_functions import \
    get_project_operational_timepoints

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity", "project.fuels", "project.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.always_on"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='gridpath')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestAlwaysOnOperationalType(unittest.TestCase):
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
        Test components initialized with data as expected
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

        # Set: ALWAYS_ON_GENERATORS
        expected_always_on_gen_set = sorted([
            "Nuclear_Flexible"
        ])
        actual_always_on_gen_set = sorted([
            prj for prj in instance.ALWAYS_ON_GENERATORS
        ])
        self.assertListEqual(expected_always_on_gen_set,
                             actual_always_on_gen_set)

        # Set: ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS
        expected_operational_timpoints_by_project = sorted(
            get_project_operational_timepoints(expected_always_on_gen_set)
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in
             instance.ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS]
        )
        self.assertListEqual(expected_operational_timpoints_by_project,
                             actual_operational_timepoints_by_project)

        # Param: always_on_unit_size_mw
        expected_unit_size = {
            "Nuclear_Flexible": 584
        }
        actual_unit_size = {
            prj: instance.always_on_unit_size_mw[prj]
            for prj in instance.ALWAYS_ON_GENERATORS
        }
        self.assertDictEqual(expected_unit_size,
                             actual_unit_size)

        # Param: always_on_min_stable_level_fraction
        expected_min_stable_fraction = {
            "Nuclear_Flexible": 0.72
        }
        actual_min_stable_fraction = {
            prj: instance.always_on_min_stable_level_fraction[prj]
            for prj in instance.ALWAYS_ON_GENERATORS
        }
        self.assertDictEqual(expected_min_stable_fraction,
                             actual_min_stable_fraction
                             )

        # Param: always_on_ramp_up_rate
        expected_ramp_up_when_on_rate = {
            "Nuclear_Flexible": 0.18
        }
        actual_ramp_down_when_on_rate = {
            prj: instance.always_on_ramp_up_rate[
                prj]
            for prj in instance.ALWAYS_ON_GENERATORS
        }
        self.assertDictEqual(expected_ramp_up_when_on_rate,
                             actual_ramp_down_when_on_rate
                             )

        # Param: always_on_ramp_down_rate
        expected_ramp_down_when_on_rate = {
            "Nuclear_Flexible": 0.18
        }
        actual_ramp_down_when_on_rate = {
            prj: instance.always_on_ramp_down_rate[
                prj]
            for prj in instance.ALWAYS_ON_GENERATORS
        }
        self.assertDictEqual(expected_ramp_down_when_on_rate,
                             actual_ramp_down_when_on_rate
                             )


if __name__ == "__main__":
    unittest.main()
