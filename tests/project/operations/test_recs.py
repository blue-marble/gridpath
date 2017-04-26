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
        expected_rps_prj_op_tmp = sorted([
            ("Wind", 20200101), ("Wind", 20200102),
            ("Wind", 20200103), ("Wind", 20200104),
            ("Wind", 20200105), ("Wind", 20200106),
            ("Wind", 20200107), ("Wind", 20200108),
            ("Wind", 20200109), ("Wind", 20200110),
            ("Wind", 20200111), ("Wind", 20200112),
            ("Wind", 20200113), ("Wind", 20200114),
            ("Wind", 20200115), ("Wind", 20200116),
            ("Wind", 20200117), ("Wind", 20200118),
            ("Wind", 20200119), ("Wind", 20200120),
            ("Wind", 20200121), ("Wind", 20200122),
            ("Wind", 20200123), ("Wind", 20200124),
            ("Wind", 20200201), ("Wind", 20200202),
            ("Wind", 20200203), ("Wind", 20200204),
            ("Wind", 20200205), ("Wind", 20200206),
            ("Wind", 20200207), ("Wind", 20200208),
            ("Wind", 20200209), ("Wind", 20200210),
            ("Wind", 20200211), ("Wind", 20200212),
            ("Wind", 20200213), ("Wind", 20200214),
            ("Wind", 20200215), ("Wind", 20200216),
            ("Wind", 20200217), ("Wind", 20200218),
            ("Wind", 20200219), ("Wind", 20200220),
            ("Wind", 20200221), ("Wind", 20200222),
            ("Wind", 20200223), ("Wind", 20200224),
            ("Wind", 20300101), ("Wind", 20300102),
            ("Wind", 20300103), ("Wind", 20300104),
            ("Wind", 20300105), ("Wind", 20300106),
            ("Wind", 20300107), ("Wind", 20300108),
            ("Wind", 20300109), ("Wind", 20300110),
            ("Wind", 20300111), ("Wind", 20300112),
            ("Wind", 20300113), ("Wind", 20300114),
            ("Wind", 20300115), ("Wind", 20300116),
            ("Wind", 20300117), ("Wind", 20300118),
            ("Wind", 20300119), ("Wind", 20300120),
            ("Wind", 20300121), ("Wind", 20300122),
            ("Wind", 20300123), ("Wind", 20300124),
            ("Wind", 20300201), ("Wind", 20300202),
            ("Wind", 20300203), ("Wind", 20300204),
            ("Wind", 20300205), ("Wind", 20300206),
            ("Wind", 20300207), ("Wind", 20300208),
            ("Wind", 20300209), ("Wind", 20300210),
            ("Wind", 20300211), ("Wind", 20300212),
            ("Wind", 20300213), ("Wind", 20300214),
            ("Wind", 20300215), ("Wind", 20300216),
            ("Wind", 20300217), ("Wind", 20300218),
            ("Wind", 20300219), ("Wind", 20300220),
            ("Wind", 20300221), ("Wind", 20300222),
            ("Wind", 20300223), ("Wind", 20300224),
            ("Wind_z2", 20200101), ("Wind_z2", 20200102),
            ("Wind_z2", 20200103), ("Wind_z2", 20200104),
            ("Wind_z2", 20200105), ("Wind_z2", 20200106),
            ("Wind_z2", 20200107), ("Wind_z2", 20200108),
            ("Wind_z2", 20200109), ("Wind_z2", 20200110),
            ("Wind_z2", 20200111), ("Wind_z2", 20200112),
            ("Wind_z2", 20200113), ("Wind_z2", 20200114),
            ("Wind_z2", 20200115), ("Wind_z2", 20200116),
            ("Wind_z2", 20200117), ("Wind_z2", 20200118),
            ("Wind_z2", 20200119), ("Wind_z2", 20200120),
            ("Wind_z2", 20200121), ("Wind_z2", 20200122),
            ("Wind_z2", 20200123), ("Wind_z2", 20200124),
            ("Wind_z2", 20200201), ("Wind_z2", 20200202),
            ("Wind_z2", 20200203), ("Wind_z2", 20200204),
            ("Wind_z2", 20200205), ("Wind_z2", 20200206),
            ("Wind_z2", 20200207), ("Wind_z2", 20200208),
            ("Wind_z2", 20200209), ("Wind_z2", 20200210),
            ("Wind_z2", 20200211), ("Wind_z2", 20200212),
            ("Wind_z2", 20200213), ("Wind_z2", 20200214),
            ("Wind_z2", 20200215), ("Wind_z2", 20200216),
            ("Wind_z2", 20200217), ("Wind_z2", 20200218),
            ("Wind_z2", 20200219), ("Wind_z2", 20200220),
            ("Wind_z2", 20200221), ("Wind_z2", 20200222),
            ("Wind_z2", 20200223), ("Wind_z2", 20200224),
            ("Wind_z2", 20300101), ("Wind_z2", 20300102),
            ("Wind_z2", 20300103), ("Wind_z2", 20300104),
            ("Wind_z2", 20300105), ("Wind_z2", 20300106),
            ("Wind_z2", 20300107), ("Wind_z2", 20300108),
            ("Wind_z2", 20300109), ("Wind_z2", 20300110),
            ("Wind_z2", 20300111), ("Wind_z2", 20300112),
            ("Wind_z2", 20300113), ("Wind_z2", 20300114),
            ("Wind_z2", 20300115), ("Wind_z2", 20300116),
            ("Wind_z2", 20300117), ("Wind_z2", 20300118),
            ("Wind_z2", 20300119), ("Wind_z2", 20300120),
            ("Wind_z2", 20300121), ("Wind_z2", 20300122),
            ("Wind_z2", 20300123), ("Wind_z2", 20300124),
            ("Wind_z2", 20300201), ("Wind_z2", 20300202),
            ("Wind_z2", 20300203), ("Wind_z2", 20300204),
            ("Wind_z2", 20300205), ("Wind_z2", 20300206),
            ("Wind_z2", 20300207), ("Wind_z2", 20300208),
            ("Wind_z2", 20300209), ("Wind_z2", 20300210),
            ("Wind_z2", 20300211), ("Wind_z2", 20300212),
            ("Wind_z2", 20300213), ("Wind_z2", 20300214),
            ("Wind_z2", 20300215), ("Wind_z2", 20300216),
            ("Wind_z2", 20300217), ("Wind_z2", 20300218),
            ("Wind_z2", 20300219), ("Wind_z2", 20300220),
            ("Wind_z2", 20300221), ("Wind_z2", 20300222),
            ("Wind_z2", 20300223), ("Wind_z2", 20300224)
        ])

        actual_rps_prj_op_tmp = sorted([
            (prj, tmp) for (prj, tmp)
            in instance.RPS_PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_rps_prj_op_tmp, actual_rps_prj_op_tmp)


if __name__ == "__main__":
    unittest.main()
