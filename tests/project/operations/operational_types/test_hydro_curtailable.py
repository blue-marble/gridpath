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
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
     "temporal.operations.timepoints", "temporal.operations.horizons",
     "temporal.investment.periods", "geography.load_zones", "project",
     "project.capacity.capacity", "project.availability.availability",
    "project.fuels", "project.operations"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.operations.operational_types.hydro_curtailable"
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


class TestHydroCurtailable(unittest.TestCase):
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

    def test_capacity_data_load_correctly(self):
        """
        Test that are data loaded are as expected
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

        # Sets: HYDRO_CURTAILABLE_PROJECTS
        expected_projects = ["Hydro"]
        actual_projects = [p for p in instance.HYDRO_CURTAILABLE_PROJECTS]
        self.assertListEqual(expected_projects, actual_projects)

        # Sets: HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
        expected_operational_horizons = sorted(
            [("Hydro", 202001), ("Hydro", 202002),
             ("Hydro", 203001), ("Hydro", 203002)]
        )
        actual_operational_horizons = sorted(
            [p for p in 
             instance
                .HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
             ]
            )
        self.assertListEqual(expected_operational_horizons,
                             actual_operational_horizons)

        # Param: hydro_curtailable_average_power_fraction
        expected_average_power = OrderedDict(
            sorted(
                {("Hydro", 202001): 0.5,
                 ("Hydro", 202002): 0.5,
                 ("Hydro", 203001): 0.5,
                 ("Hydro", 203002): 0.5}.items()
            )
        )
        actual_average_power = OrderedDict(
            sorted(
                {(prj, horizon):
                    instance.hydro_curtailable_average_power_fraction[prj,
                                                                 horizon]
                 for (prj, horizon) in
                 instance
                 .HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_average_power, actual_average_power)

        # Param: hydro_curtailable_min_power_fraction
        expected_min_power = OrderedDict(
            sorted(
                {("Hydro", 202001): 0.15,
                 ("Hydro", 202002): 0.15,
                 ("Hydro", 203001): 0.15,
                 ("Hydro", 203002): 0.15}.items()
            )
        )
        actual_min_power = OrderedDict(
            sorted(
                {(prj, horizon):
                    instance.hydro_curtailable_min_power_fraction[prj, horizon]
                 for (prj, horizon) in
                 instance
                 .HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_power, actual_min_power)

        # Param: hydro_curtailable_max_power_fraction
        expected_max_power = OrderedDict(
            sorted(
                {("Hydro", 202001): 1,
                 ("Hydro", 202002): 1,
                 ("Hydro", 203001): 1,
                 ("Hydro", 203002): 1}.items()
            )
        )
        actual_max_power = OrderedDict(
            sorted(
                {(prj, horizon):
                    instance.hydro_curtailable_max_power_fraction[prj, horizon]
                 for (prj, horizon) in
                 instance
                 .HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_power, actual_max_power)

        # HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps = sorted(
            get_project_operational_timepoints(
                expected_projects
            )
        )
        actual_tmps = sorted([
            tmp for tmp in
            instance.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS
            ])
        self.assertListEqual(expected_tmps, actual_tmps)

        # Param: hydro_curtailable_ramp_up_rate
        expected_ramp_up = OrderedDict(
            sorted({"Hydro": 0.5}.items())
        )
        actual_ramp_up = OrderedDict(
            sorted(
                {prj: instance.hydro_curtailable_ramp_up_rate[prj]
                 for prj in instance.HYDRO_CURTAILABLE_PROJECTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_ramp_up, actual_ramp_up)

        # Param: hydro_curtailable_ramp_down_rate
        expected_ramp_down = OrderedDict(
            sorted({"Hydro": 0.5}.items())
        )
        actual_ramp_down = OrderedDict(
            sorted(
                {prj: instance.hydro_curtailable_ramp_down_rate[prj]
                 for prj in instance.HYDRO_CURTAILABLE_PROJECTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_ramp_down, actual_ramp_down)


if __name__ == "__main__":
    unittest.main()
