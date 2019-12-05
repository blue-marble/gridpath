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


TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
     "temporal.operations.timepoints", "temporal.operations.horizons",
     "temporal.investment.periods", "geography.load_zones", "project"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.capacity.capacity_types.gen_spec"
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


class TestExistingNoEconomicRetirement(unittest.TestCase):
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

        # Set: EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        expected_proj_period_set = sorted([
            ("Nuclear", 2020), ("Gas_CCGT", 2020), ("Coal", 2020),
            ("Gas_CT", 2020), ("Wind", 2020), ("Nuclear", 2030),
            ("Gas_CCGT", 2030), ("Coal", 2030), ("Gas_CT", 2030),
            ("Wind", 2030), ("Nuclear_z2", 2020), ("Gas_CCGT_z2", 2020),
            ("Coal_z2", 2020), ("Gas_CT_z2", 2020), ("Wind_z2", 2020),
            ("Nuclear_z2", 2030), ("Gas_CCGT_z2", 2030), ("Coal_z2", 2030),
            ("Gas_CT_z2", 2030), ("Wind_z2", 2030), ("Hydro", 2020),
            ("Hydro", 2030), ("Hydro_NonCurtailable", 2020),
            ("Hydro_NonCurtailable", 2030), ("Disp_Binary_Commit", 2020),
            ("Disp_Binary_Commit", 2030), ("Disp_Cont_Commit", 2020),
            ("Disp_Cont_Commit", 2030), ("Disp_No_Commit", 2020),
            ("Disp_No_Commit", 2030),
            ("Customer_PV", 2020), ("Customer_PV", 2030),
            ("Nuclear_Flexible", 2030)
        ])
        actual_proj_period_set = sorted([
            (prj, period) for (prj, period) in
                 instance.
                     EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
            ])
        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)
        
        # Params: existing_gen_no_econ_ret_capacity_mw
        expected_existing_cap = OrderedDict(
            sorted(
                {("Nuclear", 2020): 6, ("Gas_CCGT", 2020): 6,
                 ("Coal", 2020): 6, ("Gas_CT", 2020): 6,
                 ("Wind", 2020): 2, ("Nuclear", 2030): 6,
                 ("Gas_CCGT", 2030): 6, ("Coal", 2030): 6,
                 ("Gas_CT", 2030): 6, ("Wind", 2030): 2,
                 ("Nuclear_z2", 2020): 6, ("Gas_CCGT_z2", 2020): 6,
                 ("Coal_z2", 2020): 6, ("Gas_CT_z2", 2020): 6,
                 ("Wind_z2", 2020): 2, ("Nuclear_z2", 2030): 6,
                 ("Gas_CCGT_z2", 2030): 6, ("Coal_z2", 2030): 6,
                 ("Gas_CT_z2", 2030): 6, ("Wind_z2", 2030): 2,
                 ("Hydro", 2020): 6, ("Hydro", 2030): 6,
                 ("Hydro_NonCurtailable", 2020): 6,
                 ("Hydro_NonCurtailable", 2030): 6,
                 ("Disp_Binary_Commit", 2020): 6,
                 ("Disp_Binary_Commit", 2030): 6,
                 ("Disp_Cont_Commit", 2020): 6, ("Disp_Cont_Commit", 2030): 6,
                 ("Disp_No_Commit", 2020): 6, ("Disp_No_Commit", 2030): 6,
                 ("Customer_PV", 2020): 1, ("Customer_PV", 2030): 1,
                 ("Nuclear_Flexible", 2030): 1000
        }.items()
            )
        )
        actual_existing_cap = OrderedDict(
            sorted(
                {(prj, period):
                     instance.existing_gen_no_econ_ret_capacity_mw[prj, period]
                 for (prj, period) in
                 instance.
                    EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_existing_cap, actual_existing_cap)
        
        # Params: existing_no_econ_ret_fixed_cost_per_mw_yr
        expected_fixed_cost = OrderedDict(
            sorted(
                {("Nuclear", 2020): 0, ("Gas_CCGT", 2020): 0,
                 ("Coal", 2020): 0, ("Gas_CT", 2020): 0,
                 ("Wind", 2020): 0, ("Nuclear", 2030): 0,
                 ("Gas_CCGT", 2030): 0, ("Coal", 2030): 0,
                 ("Gas_CT", 2030): 0, ("Wind", 2030): 0,
                 ("Nuclear_z2", 2020): 0, ("Gas_CCGT_z2", 2020): 0,
                 ("Coal_z2", 2020): 0, ("Gas_CT_z2", 2020): 0,
                 ("Wind_z2", 2020): 0, ("Nuclear_z2", 2030): 0,
                 ("Gas_CCGT_z2", 2030): 0, ("Coal_z2", 2030): 0,
                 ("Gas_CT_z2", 2030): 0, ("Wind_z2", 2030): 0,
                 ("Hydro", 2020): 0, ("Hydro", 2030): 0,
                 ("Hydro_NonCurtailable", 2020): 0,
                 ("Hydro_NonCurtailable", 2030): 0,
                 ("Disp_Binary_Commit", 2020): 0,
                 ("Disp_Binary_Commit", 2030): 0,
                 ("Disp_Cont_Commit", 2020): 0, ("Disp_Cont_Commit", 2030): 0,
                 ("Disp_No_Commit", 2020): 0, ("Disp_No_Commit", 2030): 0,
                 ("Customer_PV", 2020): 0, ("Customer_PV", 2030): 0,
                 ("Nuclear_Flexible", 2030): 1
        }.items()
            )
        )
        actual_fixed_cost = OrderedDict(
            sorted(
                {(prj, period): instance.existing_no_econ_ret_fixed_cost_per_mw_yr[prj, period]
                 for (prj, period) in
                 instance.
                     EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_fixed_cost, actual_fixed_cost)

if __name__ == "__main__":
    unittest.main()
