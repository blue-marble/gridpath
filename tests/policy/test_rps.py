#!/usr/bin/env python

from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = ["temporal.operations.timepoints",
                             "temporal.operations.horizons",
                             "temporal.investment.periods",
                             "geography.load_zones",
                             "project", "project.capacity.capacity",
                             "project.operations.operational_types",
                             "project.operations.power",
                             "project.operations.curtailment"]
NAME_OF_MODULE_BEING_TESTED = "policy.rps"
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


class TestRPS(unittest.TestCase):
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

        # Set: RPS_ZONES
        expected_rps_zones = sorted(["RPS_Zone_1", "RPS_Zone_2"])
        actual_rps_zones = sorted([z for z in instance.RPS_ZONES])
        self.assertListEqual(expected_rps_zones, actual_rps_zones)

        # Set: RPS_ZONE_PERIODS_WITH_RPS
        expected_rps_zone_periods = sorted([
            ("RPS_Zone_1", 2020), ("RPS_Zone_1", 2030),
            ("RPS_Zone_2", 2020), ("RPS_Zone_2", 2030)
        ])
        actual_rps_zone_periods = sorted([
            (z, p) for (z, p) in instance.RPS_ZONE_PERIODS_WITH_RPS
        ])
        self.assertListEqual(expected_rps_zone_periods,
                             actual_rps_zone_periods)

        # Param: rps_target_mwh
        expected_rps_target = OrderedDict(sorted({
            ("RPS_Zone_1", 2020): 50, ("RPS_Zone_1", 2030): 50,
            ("RPS_Zone_2", 2020): 10, ("RPS_Zone_2", 2030): 10}.items()
                                                 )
                                          )
        actual_rps_target = OrderedDict(sorted({
            (z, p): instance.rps_target_mwh[z, p]
            for (z, p) in instance.RPS_ZONE_PERIODS_WITH_RPS}.items()
                                               )
                                        )
        self.assertDictEqual(expected_rps_target, actual_rps_target)

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

if __name__ == "__main__":
    unittest.main()
