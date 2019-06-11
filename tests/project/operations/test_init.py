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
    "temporal.investment.periods", "geography.load_zones", "project",
    "project.capacity.capacity", "project.fuels"
]
NAME_OF_MODULE_BEING_TESTED = "project.operations"
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


class TestOperationsInit(unittest.TestCase):
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

        # Set: STARTUP_COST_PROJECTS
        expected_startup_projects = sorted([
            "Gas_CCGT", "Coal", "Gas_CCGT_New", "Gas_CCGT_z2", "Coal_z2",
            "Disp_Binary_Commit", "Disp_Cont_Commit", "Clunky_Old_Gen",
            "Clunky_Old_Gen2"
        ])
        actual_startup_projects = sorted([
                                             prj for prj in
                                             instance.STARTUP_COST_PROJECTS
                                             ])
        self.assertListEqual(expected_startup_projects,
                             actual_startup_projects)

        # Param: startup_cost_per_mw
        expected_startup_costs = OrderedDict(sorted({
            "Gas_CCGT": 1,
            "Coal": 1,
            "Gas_CCGT_New": 1,
            "Gas_CCGT_z2": 1,
            "Coal_z2": 1,
            "Disp_Binary_Commit": 1,
            "Disp_Cont_Commit": 1,
            "Clunky_Old_Gen": 1,
            "Clunky_Old_Gen2": 1
                                                    }.items()
                                                    )
                                             )
        actual_startup_costs = OrderedDict(sorted(
            {prj: instance.startup_cost_per_mw[prj]
             for prj in instance.STARTUP_COST_PROJECTS}.items()
                                                  )
                                           )
        self.assertDictEqual(expected_startup_costs,
                             actual_startup_costs)

        # Set: SHUTDOWN_COST_PROJECTS
        expected_shutdown_projects = sorted([
            "Gas_CCGT", "Gas_CT", "Gas_CCGT_New", "Gas_CT_New", "Gas_CCGT_z2",
            "Gas_CT_z2", "Disp_Binary_Commit", "Disp_Cont_Commit",
            "Clunky_Old_Gen", "Clunky_Old_Gen2"
        ])
        actual_shutdown_projects = sorted([
            prj for prj in instance.SHUTDOWN_COST_PROJECTS])
        self.assertListEqual(expected_shutdown_projects,
                             actual_shutdown_projects)

        # Param: shutdown_cost_per_mw
        expected_shutdown_costs = OrderedDict(sorted({
            "Gas_CCGT": 2,
            "Gas_CT": 1,
            "Gas_CCGT_New": 2,
            "Gas_CT_New": 1,
            "Gas_CCGT_z2": 2,
            "Gas_CT_z2": 1,
            "Disp_Binary_Commit": 1,
            "Disp_Cont_Commit": 1,
            "Clunky_Old_Gen": 1,
            "Clunky_Old_Gen2": 1
                                                     }.items()
                                                     )
                                              )
        actual_shutdown_costs = OrderedDict(sorted(
            {prj: instance.shutdown_cost_per_mw[prj]
             for prj in instance.SHUTDOWN_COST_PROJECTS}.items()
                                                   )
                                            )
        self.assertDictEqual(expected_shutdown_costs,
                             actual_shutdown_costs)

        # Set: FUEL_COST_PROJECTS
        expected_fuel_projects = sorted([
            "Nuclear", "Gas_CCGT", "Coal", "Gas_CT", "Gas_CCGT_New",
            "Nuclear_z2", "Gas_CCGT_z2", "Coal_z2", "Gas_CT_z2", "Gas_CT_New",
            "Disp_Binary_Commit", "Disp_Cont_Commit", "Disp_No_Commit",
            "Clunky_Old_Gen", "Clunky_Old_Gen2", "Nuclear_Flexible"
        ])
        actual_fuel_projects = sorted([
            prj for prj in instance.FUEL_PROJECTS
            ])
        self.assertListEqual(expected_fuel_projects,
                             actual_fuel_projects)

        # Param: fuel
        expected_fuel = OrderedDict(sorted({
            "Nuclear": "Uranium",
            "Gas_CCGT": "Gas",
            "Coal": "Coal",
            "Gas_CT": "Gas",
            "Gas_CCGT_New": "Gas",
            "Nuclear_z2": "Uranium",
            "Gas_CCGT_z2": "Gas",
            "Coal_z2": "Coal",
            "Gas_CT_z2": "Gas",
            "Gas_CT_New": "Gas",
            "Disp_Binary_Commit": "Gas",
            "Disp_Cont_Commit": "Gas",
            "Disp_No_Commit": "Gas",
            "Clunky_Old_Gen": "Coal",
            "Clunky_Old_Gen2": "Coal",
            "Nuclear_Flexible": "Uranium"
                                           }.items()
                                           )
                                    )
        actual_fuel = OrderedDict(sorted(
            {prj: instance.fuel[prj] for prj in instance.FUEL_PROJECTS}.items()
        )
        )
        self.assertDictEqual(expected_fuel, actual_fuel)

        # Param: minimum_input_mmbtu_per_hr
        expected_min_input = OrderedDict(sorted({
            "Nuclear": 0,
            "Gas_CCGT": 1500,
            "Coal": 3000,
            "Gas_CT": 500,
            "Gas_CCGT_New": 1500,
            "Nuclear_z2": 10000,
            "Gas_CCGT_z2": 1500,
            "Coal_z2": 3000,
            "Gas_CT_z2": 500,
            "Gas_CT_New": 500,
            "Disp_Binary_Commit": 500,
            "Disp_Cont_Commit": 500,
            "Disp_No_Commit": 500,
            "Clunky_Old_Gen": 5000,
            "Clunky_Old_Gen2": 5000,
            "Nuclear_Flexible": 5500
                                                }.items()
                                                )
                                         )
        actual_min_input = OrderedDict(sorted(
            {prj: instance.minimum_input_mmbtu_per_hr[prj]
             for prj in instance.FUEL_PROJECTS}.items()
        )
        )
        self.assertDictEqual(expected_min_input, actual_min_input)

        # Param: inc_heat_rate_mmbtu_per_mwh
        expected_inc_heat_rate = OrderedDict(sorted({
            "Nuclear": 1666.67,
            "Gas_CCGT": 6,
            "Coal": 10,
            "Gas_CT": 8,
            "Gas_CCGT_New": 6,
            "Nuclear_z2": 0,
            "Gas_CCGT_z2": 6,
            "Coal_z2": 10,
            "Gas_CT_z2": 8,
            "Gas_CT_New": 8,
            "Disp_Binary_Commit": 8,
            "Disp_Cont_Commit": 8,
            "Disp_No_Commit": 8,
            "Clunky_Old_Gen": 15,
            "Clunky_Old_Gen2": 15,
            "Nuclear_Flexible": 450
                                                    }.items()
                                                    )
                                             )
        actual_inc_heat_rate = OrderedDict(sorted(
            {prj: instance.inc_heat_rate_mmbtu_per_mwh[prj]
             for prj in instance.FUEL_PROJECTS}.items()
        )
        )
        self.assertDictEqual(expected_inc_heat_rate, actual_inc_heat_rate)

        # Set: FUEL_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps_by_fuel_project = sorted(
            get_project_operational_timepoints(expected_fuel_projects)
        )
        actual_tmps_by_fuel_project = sorted([
            (prj, tmp) for (prj, tmp) in
            instance.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS
                                                 ])
        self.assertListEqual(expected_tmps_by_fuel_project,
                             actual_tmps_by_fuel_project)

        # Set: STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps_by_startup_project = sorted(
            get_project_operational_timepoints(expected_startup_projects)
        )
        actual_tmps_by_startup_project = sorted([
            (prj, tmp) for (prj, tmp) in
            instance.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS
                                                    ])
        self.assertListEqual(expected_tmps_by_startup_project,
                             actual_tmps_by_startup_project)

        # Set: SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps_by_shutdown_project = sorted(
            get_project_operational_timepoints(expected_shutdown_projects)
        )
        actual_tmps_by_shutdown_project = sorted([
            (prj, tmp) for (prj, tmp) in
            instance.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS
                                                     ])
        self.assertListEqual(expected_tmps_by_shutdown_project,
                             actual_tmps_by_shutdown_project)

        # Set: STARTUP_FUEL_PROJECTS
        expected_startup_fuel_projects = sorted([
            "Gas_CCGT", "Coal", "Gas_CT", "Gas_CCGT_New", "Gas_CT_New",
            "Gas_CCGT_z2", "Coal_z2", "Disp_Binary_Commit", "Disp_Cont_Commit",
            "Disp_No_Commit", "Clunky_Old_Gen", "Clunky_Old_Gen2"
        ])
        actual_startup_fuel_projects = sorted([
            prj for prj in instance.STARTUP_FUEL_PROJECTS
        ])
        self.assertListEqual(expected_startup_fuel_projects,
                             actual_startup_fuel_projects)

        # Param: startup_fuel_mmbtu_per_mw
        expected_startup_fuel_mmbtu_per_mw = OrderedDict(sorted({
            "Gas_CCGT": 6, "Coal": 6, "Gas_CT": 0.5, "Gas_CCGT_New": 6,
            "Gas_CT_New": 0.5, "Gas_CCGT_z2": 6, "Coal_z2": 6,
            "Disp_Binary_Commit": 10, "Disp_Cont_Commit": 10,
            "Disp_No_Commit": 10,
            "Clunky_Old_Gen": 10, "Clunky_Old_Gen2": 10
            }.items()
                )
            )
        actual_startup_fuel_mmbtu_per_mw = OrderedDict(sorted(
            {prj: instance.startup_fuel_mmbtu_per_mw[prj]
             for prj in instance.STARTUP_FUEL_PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_startup_fuel_mmbtu_per_mw,
                             actual_startup_fuel_mmbtu_per_mw)

        # Set: STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS
        expected_tmps_by_startup_fuel_project = sorted(
            get_project_operational_timepoints(expected_startup_fuel_projects)
        )

        actual_tmps_by_startup_fuel_project = sorted([
            (prj, tmp) for (prj, tmp) in
            instance.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS
                                                     ])

        self.assertListEqual(expected_tmps_by_startup_fuel_project,
                             actual_tmps_by_startup_fuel_project)

        # Param: availability_derate
        expected_availability = OrderedDict(sorted(
            {("Nuclear", 202001): 1, ("Nuclear", 202002): 0.5,
             ("Nuclear", 203001): 0.75, ("Nuclear", 203002): 1,
             ("Gas_CCGT", 202001): 1, ("Gas_CCGT", 202002): 1,
             ("Gas_CCGT", 203001): 1, ("Gas_CCGT", 203002): 1,
             ("Coal", 202001): 0.5, ("Coal", 202002): 1,
             ("Coal", 203001): 0.75, ("Coal", 203002): 1,
             ("Gas_CT", 202001): 1, ("Gas_CT", 202002): 1,
             ("Gas_CT", 203001): 1, ("Gas_CT", 203002): 1,
             ("Wind", 202001): 1, ("Wind", 202002): 1,
             ("Wind", 203001): 1, ("Wind", 203002): 1,
             ("Gas_CCGT_New", 202001): 1, ("Gas_CCGT_New", 202002): 1,
             ("Gas_CCGT_New", 203001): 1, ("Gas_CCGT_New", 203002): 1,
             ("Gas_CT_New", 202001): 1, ("Gas_CT_New", 202002): 1,
             ("Gas_CT_New", 203001): 1, ("Gas_CT_New", 203002): 1,
             ("Nuclear_z2", 202001): 1, ("Nuclear_z2", 202002): 0.5,
             ("Nuclear_z2", 203001): 0.75, ("Nuclear_z2", 203002): 1,
             ("Gas_CCGT_z2", 202001): 1, ("Gas_CCGT_z2", 202002): 1,
             ("Gas_CCGT_z2", 203001): 1, ("Gas_CCGT_z2", 203002): 1,
             ("Coal_z2", 202001): 0.5, ("Coal_z2", 202002): 1,
             ("Coal_z2", 203001): 0.75, ("Coal_z2", 203002): 1,
             ("Gas_CT_z2", 202001): 1, ("Gas_CT_z2", 202002): 1,
             ("Gas_CT_z2", 203001): 1, ("Gas_CT_z2", 203002): 1,
             ("Wind_z2", 202001): 1, ("Wind_z2", 202002): 1,
             ("Wind_z2", 203001): 1, ("Wind_z2", 203002): 1,
             ("Battery", 202001): 1, ("Battery", 202002): 1,
             ("Battery", 203001): 1, ("Battery", 203002): 1,
             ("Battery_Specified", 202001): 1,
             ("Battery_Specified", 202002): 1,
             ("Battery_Specified", 203001): 1,
             ("Battery_Specified", 203002): 1,
             ("Battery", 202001): 1, ("Battery", 202002): 1,
             ("Battery", 203001): 1, ("Battery", 203002): 1,
             ("Hydro", 202001): 1, ("Hydro", 202002): 1,
             ("Hydro", 203001): 1, ("Hydro", 203002): 1,
             ("Hydro_NonCurtailable", 202001): 1,
             ("Hydro_NonCurtailable", 202002): 1,
             ("Hydro_NonCurtailable", 203001): 1,
             ("Hydro_NonCurtailable", 203002): 1,
             ("Disp_Binary_Commit", 202001): 1,
             ("Disp_Binary_Commit", 202002): 1,
             ("Disp_Binary_Commit", 203001): 1,
             ("Disp_Binary_Commit", 203002): 1,
             ("Disp_Cont_Commit", 202001): 1, ("Disp_Cont_Commit", 202002): 1,
             ("Disp_Cont_Commit", 203001): 1, ("Disp_Cont_Commit", 203002): 1,
             ("Disp_No_Commit", 202001): 1, ("Disp_No_Commit", 202002): 1,
             ("Disp_No_Commit", 203001): 1, ("Disp_No_Commit", 203002): 1,
             ("Clunky_Old_Gen", 202001): 1, ("Clunky_Old_Gen", 202002): 1,
             ("Clunky_Old_Gen", 203001): 1, ("Clunky_Old_Gen", 203002): 1,
             ("Clunky_Old_Gen2", 202001): 1, ("Clunky_Old_Gen2", 202002): 1,
             ("Clunky_Old_Gen2", 203001): 1, ("Clunky_Old_Gen2", 203002): 1,
             ("Customer_PV", 202001): 1, ("Customer_PV", 202002): 1,
             ("Customer_PV", 203001): 1, ("Customer_PV", 203002): 1,
             ("Nuclear_Flexible", 202001): 1, ("Nuclear_Flexible", 202002): 1,
             ("Nuclear_Flexible", 203001): 1, ("Nuclear_Flexible", 203002): 1,
             ("Shift_DR", 202001): 1, ("Shift_DR", 202002): 1,
             ("Shift_DR", 203001): 1, ("Shift_DR", 203002): 1,
             }.items()
        )
        )

        actual_availability = OrderedDict(sorted(
            {(p, h): instance.availability_derate[p, h] for p in
             instance.PROJECTS for h in instance.HORIZONS}.items()
        )
        )

        self.assertDictEqual(expected_availability, actual_availability)


if __name__ == "__main__":
    unittest.main()
