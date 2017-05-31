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
PREREQUISITE_MODULE_NAMES = ["temporal.operations.timepoints",
                             "temporal.operations.horizons",
                             "temporal.investment.periods",
                             "geography.load_zones",
                             "geography.prm_zones",
                             "project", "project.capacity.capacity",
                             "system.prm.prm_requirement",
                             "project.prm",
                             "project.prm.prm_types",
                             "project.prm.elcc_surface"]
NAME_OF_MODULE_BEING_TESTED = \
    "system.prm.elcc_surface"
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


class TestELCCSurface(unittest.TestCase):
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

        # Set: PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS
        expected_z_p_f = sorted([
            ("PRM_Zone1", 2020, 1), ("PRM_Zone1", 2020, 2),
            ("PRM_Zone1", 2030, 1), ("PRM_Zone1", 2030, 2),
            ("PRM_Zone2", 2020, 1), ("PRM_Zone2", 2020, 2),
            ("PRM_Zone2", 2030, 1), ("PRM_Zone2", 2030, 2)
        ])

        actual_z_p_f = sorted([
            (z, p, f)
            for (z, p, f) in instance.PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS
        ])

        self.assertListEqual(expected_z_p_f, actual_z_p_f)

        # Param: elcc_surface_intercept
        expected_intercept = OrderedDict(sorted(
            {("PRM_Zone1", 2020, 1): 5000, ("PRM_Zone1", 2020, 2): 6000,
            ("PRM_Zone1", 2030, 1): 10000, ("PRM_Zone1", 2030, 2): 12000,
            ("PRM_Zone2", 2020, 1):1000, ("PRM_Zone2", 2020, 2): 1100,
            ("PRM_Zone2", 2030, 1): 1200, ("PRM_Zone2", 2030, 2): 1300
             }.items()
        )
        )

        actual_intercept = OrderedDict(sorted(
            {(z, p, f): instance.elcc_surface_intercept[z, p, f]
             for (z, p, f) in instance.PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS
            }.items()
        )
        )

        self.assertDictEqual(expected_intercept, actual_intercept)


if __name__ == "__main__":
    unittest.main()
