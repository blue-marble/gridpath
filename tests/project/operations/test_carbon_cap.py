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
    "geography.carbon_cap_zones", "system.policy.carbon_cap.carbon_cap",
    "project", "project.capacity.capacity", "project.availability.availability",
    "project.fuels", "project.operations",
    "project.operations.operational_types",
    "project.operations.power", "project.operations.fuel_burn"]
NAME_OF_MODULE_BEING_TESTED = "project.operations.carbon_cap"
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


class TestCarbonEmissions(unittest.TestCase):
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

        # Set: CRBN_PRJS
        expected_carbonaceous_projects = sorted(
            ["Gas_CCGT", "Coal", "Gas_CT", "Gas_CCGT_New",
             "Gas_CCGT_New_Binary", "Gas_CT_New",
             "Gas_CCGT_z2", "Coal_z2", "Gas_CT_z2", "Disp_Binary_Commit",
             "Disp_Cont_Commit", "Disp_No_Commit", "Clunky_Old_Gen",
             "Clunky_Old_Gen2"])
        actual_carbonaceous_projects = \
            sorted([p for p in instance.CRBN_PRJS])
        self.assertListEqual(expected_carbonaceous_projects,
                             actual_carbonaceous_projects)

        # Param: carbon_cap_zone
        expected_cc_zone_by_prj = OrderedDict(sorted({
            "Gas_CCGT": "Carbon_Cap_Zone1",
            "Coal": "Carbon_Cap_Zone1",
            "Gas_CT": "Carbon_Cap_Zone1",
            "Gas_CCGT_New": "Carbon_Cap_Zone1",
            "Gas_CCGT_New_Binary": "Carbon_Cap_Zone1",
            "Gas_CT_New": "Carbon_Cap_Zone1",
            "Gas_CCGT_z2": "Carbon_Cap_Zone2",
            "Coal_z2": "Carbon_Cap_Zone2",
            "Gas_CT_z2": "Carbon_Cap_Zone2",
            "Disp_Binary_Commit": "Carbon_Cap_Zone1",
            "Disp_Cont_Commit": "Carbon_Cap_Zone1",
            "Disp_No_Commit": "Carbon_Cap_Zone1",
            "Clunky_Old_Gen": "Carbon_Cap_Zone1",
            "Clunky_Old_Gen2": "Carbon_Cap_Zone1",
            }.items())
        )
        actual_cc_zone_by_prj = OrderedDict(sorted({
            p: instance.carbon_cap_zone[p] for p in
            instance.CRBN_PRJS}.items()
                                                    )
                                             )
        self.assertDictEqual(expected_cc_zone_by_prj, actual_cc_zone_by_prj)

        # Set: CRBN_PRJS_BY_CARBON_CAP_ZONE
        expected_prj_by_zone = OrderedDict(sorted({
            "Carbon_Cap_Zone1": sorted([
                "Gas_CCGT", "Coal", "Gas_CT", "Gas_CCGT_New",
                "Gas_CCGT_New_Binary", "Gas_CT_New",
                "Disp_Binary_Commit", "Disp_Cont_Commit", "Disp_No_Commit",
                "Clunky_Old_Gen", "Clunky_Old_Gen2"
            ]),
            "Carbon_Cap_Zone2": sorted(["Gas_CCGT_z2", "Coal_z2", "Gas_CT_z2"])
                                                  }.items()
                                                  )
                                           )
        actual_prj_by_zone = OrderedDict(sorted({
            z: sorted([p for p in
                       instance.CRBN_PRJS_BY_CARBON_CAP_ZONE[z]
                ])
            for z in instance.CARBON_CAP_ZONES
                                                }.items()
                                                )
                                         )
        self.assertDictEqual(expected_prj_by_zone, actual_prj_by_zone)

        # Set: CRBN_PRJ_OPR_TMPS
        expected_carb_prj_op_tmp = sorted(
            get_project_operational_timepoints(expected_carbonaceous_projects)
        )

        actual_carb_prj_op_tmp = sorted([
            (prj, tmp) for (prj, tmp)
            in instance.CRBN_PRJ_OPR_TMPS
        ])
        self.assertListEqual(expected_carb_prj_op_tmp, actual_carb_prj_op_tmp)


if __name__ == "__main__":
    unittest.main()