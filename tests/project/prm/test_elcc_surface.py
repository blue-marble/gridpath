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
    "geography.prm_zones", "project", "project.capacity.capacity",
    "project.prm"
]
NAME_OF_MODULE_BEING_TESTED = "project.prm.elcc_surface"
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


class TestProjELCCSurface(unittest.TestCase):
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

        # Param: contributes_to_elcc_surface
        expected_elcc_contr = OrderedDict(
            sorted(
                {"Coal": 0, "Coal_z2": 0,
                 "Gas_CCGT": 0, "Gas_CCGT_New": 0,
                 "Gas_CCGT_z2": 0, "Gas_CT": 0,
                 "Gas_CT_New": 0, "Gas_CT_z2": 0,
                 "Nuclear": 1, "Nuclear_z2": 0,
                 "Wind": 1, "Wind_z2": 1,
                 "Battery": 0, "Battery_Specified": 0,
                 "Hydro": 0, 'Hydro_NonCurtailable': 0,
                 "Disp_Binary_Commit": 0,
                 "Disp_Cont_Commit": 0,
                 "Disp_No_Commit": 0, "Clunky_Old_Gen": 0,
                 "Nuclear_Flexible": 0}.items()
            )
        )

        actual_elcc_contr = OrderedDict(
            sorted(
                {p: instance.contributes_to_elcc_surface[p]
                 for p in instance.PRM_PROJECTS}.items()
            )
        )

        self.assertDictEqual(expected_elcc_contr, actual_elcc_contr)

        # Set: ELCC_SURFACE_PROJECTS
        expected_elcc_surf_prj = sorted([
            "Nuclear", "Wind", "Wind_z2"
        ])
        actual_elcc_surf_prj = sorted([
            p for p in instance.ELCC_SURFACE_PROJECTS
        ])
        self.assertListEqual(expected_elcc_surf_prj, actual_elcc_surf_prj)

        # Set: PROJECT_PERIOD_ELCC_SURFACE_FACETS
        expected_prj_p_f = sorted([
            ("Nuclear", 2020, 1), ("Nuclear", 2020, 2),
            ("Nuclear", 2030, 1), ("Nuclear", 2030, 2),
            ("Wind", 2020, 1), ("Wind", 2020, 2),
            ("Wind", 2030, 1), ("Wind", 2030, 2),
            ("Wind_z2", 2020, 1), ("Wind_z2", 2020, 2),
            ("Wind_z2", 2030, 1), ("Wind_z2", 2030, 2)
        ])

        actual_prj_p_f = sorted([
            (prj, p, f)
            for (prj, p, f) in instance.PROJECT_PERIOD_ELCC_SURFACE_FACETS
        ])

        self.assertListEqual(expected_prj_p_f, actual_prj_p_f)

        # Param: elcc_surface_coefficient
        expected_coeff = OrderedDict(sorted(
            {("Nuclear", 2020, 1): 0.9, ("Nuclear", 2020, 2): 0.9,
             ("Nuclear", 2030, 1): 0.9, ("Nuclear", 2030, 2): 0.9,
             ("Wind", 2020, 1): 0.3, ("Wind", 2020, 2): 0.2,
             ("Wind", 2030, 1): 0.25, ("Wind", 2030, 2): 0.2,
             ("Wind_z2", 2020, 1): 0.3, ("Wind_z2", 2020, 2): 0.25,
             ("Wind_z2", 2030, 1): 0.3, ("Wind_z2", 2030, 2): 0.25
             }.items()
        )
        )

        actual_coeff = OrderedDict(sorted(
            {(prj, p, f): instance.elcc_surface_coefficient[prj, p, f]
             for (prj, p, f) in instance.PROJECT_PERIOD_ELCC_SURFACE_FACETS
             }.items()
        )
        )
        self.assertDictEqual(expected_coeff, actual_coeff)
