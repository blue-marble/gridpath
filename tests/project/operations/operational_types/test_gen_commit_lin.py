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
    "project.operations.operational_types.gen_commit_lin"
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


class TestGenCommitLin(unittest.TestCase):
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
        Test that the data loaded are as expected
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

        # Set: GEN_COMMIT_LIN
        expected_gen_commit_lin_set = sorted([
            "Disp_Cont_Commit", "Clunky_Old_Gen", "Clunky_Old_Gen2"
        ])
        actual_gen_commit_lin_set = sorted([
            prj for prj in instance.GEN_COMMIT_LIN
            ])
        self.assertListEqual(expected_gen_commit_lin_set,
                             actual_gen_commit_lin_set)

        # Set: GEN_COMMIT_LIN_STR_RMP_PRJS
        expected_gen_commit_lin_str_rmp_prjs = sorted([
            "Disp_Cont_Commit",
            "Clunky_Old_Gen",
            "Clunky_Old_Gen2"
        ])
        actual_gen_commit_lin_str_rmp_prjs = sorted([
            prj for prj in instance.GEN_COMMIT_LIN_STR_RMP_PRJS
            ])
        self.assertListEqual(expected_gen_commit_lin_str_rmp_prjs,
                             actual_gen_commit_lin_str_rmp_prjs)

        # Set: GEN_COMMIT_LIN_STR_RMP_PRJS_TYPES
        expected_gen_commit_lin_str_rmp_prjs_types = sorted([
            ("Disp_Cont_Commit", 1.0),
            ("Clunky_Old_Gen", 1.0),
            ("Clunky_Old_Gen2", 1.0)
        ])
        actual_gen_commit_lin_str_rmp_prjs_types = sorted([
            (prj, s) for prj, s in instance.GEN_COMMIT_LIN_STR_RMP_PRJS_TYPES
            ])
        self.assertListEqual(expected_gen_commit_lin_str_rmp_prjs_types,
                             actual_gen_commit_lin_str_rmp_prjs_types)

        # Set: GEN_COMMIT_LIN_STR_TYPES_BY_PRJ
        str_types_by_prj_dict = dict()
        for prj_type in expected_gen_commit_lin_str_rmp_prjs_types:
            if prj_type[0] not in str_types_by_prj_dict.keys():
                str_types_by_prj_dict[prj_type[0]] = [prj_type[1]]
            else:
                str_types_by_prj_dict[prj_type[0]].append(prj_type[1])

        expected_str_types_by_prj = OrderedDict(
            sorted(
                str_types_by_prj_dict.items()
            )
        )
        actual_str_types_by_prj = OrderedDict(
            sorted(
                {prj: [type for type in
                       instance.GEN_COMMIT_LIN_STR_TYPES_BY_PRJ[prj]]
                 for prj in instance.GEN_COMMIT_LIN_STR_RMP_PRJS}.items()
            )
        )
        self.assertDictEqual(expected_str_types_by_prj,
                             actual_str_types_by_prj)

        # Set: GEN_COMMIT_LIN_OPR_TMPS
        expected_operational_timepoints_by_project = sorted(
            get_project_operational_timepoints(
                expected_gen_commit_lin_set
            )
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in instance.GEN_COMMIT_LIN_OPR_TMPS]
        )
        self.assertListEqual(expected_operational_timepoints_by_project,
                             actual_operational_timepoints_by_project)

        # Set: GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES
        expected_opr_tmps_str_types = sorted(
            [(g, tmp, 1.0) for (g, tmp) in
             expected_operational_timepoints_by_project
             if g in expected_gen_commit_lin_str_rmp_prjs]
        )
        actual_opr_tmps_str_types = sorted(
            [(g, tmp, s) for (g, tmp, s) in
             instance.GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES]
        )
        self.assertListEqual(expected_opr_tmps_str_types,
                             actual_opr_tmps_str_types)

        # Param: gen_commit_lin_min_stable_level_fraction
        expected_min_stable_fraction = {"Disp_Cont_Commit": 0.4,
                                        "Clunky_Old_Gen": 0.4,
                                        "Clunky_Old_Gen2": 0.4}
        actual_min_stable_fraction = {
            prj: instance.gen_commit_lin_min_stable_level_fraction[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_min_stable_fraction,
                             actual_min_stable_fraction)

        # Param: gen_commit_lin_startup_plus_ramp_up_rate
        expected_startup_plus_ramp_up_rate = {("Disp_Cont_Commit", 1.0): 0.6,
                                              ("Clunky_Old_Gen", 1.0): 1,
                                              ("Clunky_Old_Gen2", 1.0): 1
                                              }
        actual_startup_plus_ramp_up_rate = {
            (prj, s): instance.gen_commit_lin_startup_plus_ramp_up_rate[prj, s]
            for prj, s in instance.GEN_COMMIT_LIN_STR_RMP_PRJS_TYPES
        }
        self.assertDictEqual(expected_startup_plus_ramp_up_rate,
                             actual_startup_plus_ramp_up_rate)

        # Param: gen_commit_lin_shutdown_plus_ramp_down_rate
        expected_shutdown_plus_ramp_down_rate = {"Disp_Cont_Commit": 0.6,
                                                 "Clunky_Old_Gen": 1,
                                                 "Clunky_Old_Gen2": 1}
        actual_shutdown_plus_ramp_down_rate = {
            prj: instance.gen_commit_lin_shutdown_plus_ramp_down_rate[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_shutdown_plus_ramp_down_rate,
                             actual_shutdown_plus_ramp_down_rate)

        # Param: gen_commit_lin_ramp_up_when_on_rate
        expected_ramp_up_when_on_rate = {"Disp_Cont_Commit": 0.3,
                                         "Clunky_Old_Gen": 1,
                                         "Clunky_Old_Gen2": 1}
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_lin_ramp_up_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_ramp_up_when_on_rate,
                             actual_ramp_down_when_on_rate)

        # Param: gen_commit_lin_ramp_down_when_on_rate
        expected_ramp_down_when_on_rate = {"Disp_Cont_Commit": 0.5,
                                           "Clunky_Old_Gen": 1,
                                           "Clunky_Old_Gen2": 1}
        actual_ramp_down_when_on_rate = {
            prj: instance.gen_commit_lin_ramp_down_when_on_rate[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_ramp_down_when_on_rate,
                             actual_ramp_down_when_on_rate)

        # Param: gen_commit_lin_min_up_time_hours
        expected_min_up_time = {"Disp_Cont_Commit": 3,
                                "Clunky_Old_Gen": 0,
                                "Clunky_Old_Gen2": 0}
        actual_min_up_time = {
            prj: instance.gen_commit_lin_min_up_time_hours[prj]
            for prj in instance.GEN_COMMIT_LIN
        }

        self.assertDictEqual(expected_min_up_time,
                             actual_min_up_time)

        # Param: gen_commit_lin_min_down_time_hours
        expected_min_down_time = {"Disp_Cont_Commit": 7,
                                  "Clunky_Old_Gen": 0,
                                  "Clunky_Old_Gen2": 0}
        actual_min_down_time = {
            prj: instance.gen_commit_lin_min_down_time_hours[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_min_down_time,
                             actual_min_down_time)

        # Param: gen_commit_lin_startup_cost_per_mw
        expected_startup_costs = {
            ("Disp_Cont_Commit", 1.0): 1,
            ("Clunky_Old_Gen", 1.0): 1,
            ("Clunky_Old_Gen2", 1.0): 1
        }
        actual_startup_costs = {
            (prj, s): instance.gen_commit_lin_startup_cost_per_mw[prj, s]
            for prj, s in instance.GEN_COMMIT_LIN_STR_RMP_PRJS_TYPES
        }
        self.assertDictEqual(expected_startup_costs,
                             actual_startup_costs)

        # Param: gen_commit_lin_shutdown_cost_per_mw
        expected_shutdown_costs = {
            "Disp_Cont_Commit": 1,
            "Clunky_Old_Gen": 1,
            "Clunky_Old_Gen2": 1
        }
        actual_shutdown_costs = {
            prj: instance.gen_commit_lin_shutdown_cost_per_mw[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_shutdown_costs,
                             actual_shutdown_costs)

        # Param: gen_commit_lin_startup_fuel_mmbtu_per_mw
        expected_startup_fuel_mmbtu_per_mw = {
            "Disp_Cont_Commit": 10,
            "Clunky_Old_Gen": 10,
            "Clunky_Old_Gen2": 10}
        actual_startup_fuel_mmbtu_per_mw = {
            prj: instance.gen_commit_lin_startup_fuel_mmbtu_per_mw[prj]
            for prj in instance.GEN_COMMIT_LIN
        }
        self.assertDictEqual(expected_startup_fuel_mmbtu_per_mw,
                             actual_startup_fuel_mmbtu_per_mw)

        # Param: gen_commit_lin_down_time_cutoff_hours
        expected_down_time_cutoff_hours = {("Disp_Cont_Commit", 1.0): 7,
                                           ("Clunky_Old_Gen", 1.0): 0,
                                           ("Clunky_Old_Gen2", 1.0): 0}
        actual_down_time_cutoff_hours = {
            (prj, s): instance.gen_commit_lin_down_time_cutoff_hours[prj, s]
            for prj, s in instance.GEN_COMMIT_LIN_STR_RMP_PRJS_TYPES
        }
        self.assertDictEqual(expected_down_time_cutoff_hours,
                             actual_down_time_cutoff_hours)


if __name__ == "__main__":
    unittest.main()
