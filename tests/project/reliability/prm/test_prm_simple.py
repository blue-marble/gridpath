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
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones",
    "geography.prm_zones", "project", "project.capacity.capacity",
    "project.reliability.prm", "project.reliability.prm.prm_types"
]
NAME_OF_MODULE_BEING_TESTED = "project.reliability.prm.prm_simple"
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


class TestProjPRMSimple(unittest.TestCase):
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
        
        # Params: prm_simple_fraction
        expected_prm_frac = OrderedDict(
            sorted(
                {"Coal": 0.8, "Coal_z2": 0.8,
                 "Gas_CCGT": 0.8, "Gas_CCGT_New": 0.8,
                 "Gas_CCGT_z2": 0.8, "Gas_CT": 0.8,
                 "Gas_CT_New": 0.8, "Gas_CT_z2": 0.8,
                 "Nuclear": 0.8, "Nuclear_z2": 0.8,
                 "Wind": 0.8, "Wind_z2": 0.8,
                 "Battery": 0.8, "Battery_Specified": 0.8,
                 "Hydro": 0.8, 'Hydro_NonCurtailable': 0.8,
                 "Disp_Binary_Commit": 0.8,
                 "Disp_Cont_Commit": 0.8,
                 "Disp_No_Commit": 0.8, "Clunky_Old_Gen": 0.8,
                 "Nuclear_Flexible": 0.8}.items()
            )
        )
        actual_prm_frac = OrderedDict(
            sorted(
                {prj: instance.elcc_simple_fraction[prj] for prj in
                 instance.PRM_PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_prm_frac, actual_prm_frac)
