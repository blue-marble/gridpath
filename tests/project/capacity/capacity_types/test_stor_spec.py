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
    "project.capacity.capacity_types.stor_spec"
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


class TestStorageSpecifiedNoEconomicRetirement(unittest.TestCase):
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

        # Set: STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS
        expected_proj_period_set = sorted([
            ("Battery_Specified", 2020)
        ])
        actual_proj_period_set = \
            sorted([(prj, period) for (prj, period) in
                    instance.
                   STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS
                    ]
                   )
        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)

        # Params: storage_specified_power_capacity_mw
        expected_specified_power_cap = OrderedDict(
            sorted(
                {("Battery_Specified", 2020): 6}.items()
            )
        )
        actual_specified_power_cap = OrderedDict(
            sorted(
                {(prj, period):
                    instance.storage_specified_power_capacity_mw[prj, period]
                 for (prj, period) in
                 instance.
                    STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_specified_power_cap,
                             actual_specified_power_cap)

        # Params: storage_specified_energy_capacity_mw
        expected_specified_energy_cap = OrderedDict(
            sorted(
                {("Battery_Specified", 2020): 6}.items()
            )
        )
        actual_specified_energy_cap = OrderedDict(
            sorted(
                {(prj, period):
                    instance.storage_specified_energy_capacity_mwh[prj, period]
                 for (prj, period) in
                 instance.
                    STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_specified_energy_cap,
                             actual_specified_energy_cap)

        # Params: storage_specified_fixed_cost_per_mw_yr
        expected_fixed_cost_per_mw = OrderedDict(
            sorted(
                {("Battery_Specified", 2020): 10000}.items()
            )
        )
        actual_fixed_cost_per_mw = OrderedDict(
            sorted(
                {(prj, period):
                    instance.storage_specified_fixed_cost_per_mw_yr[prj,
                                                                    period]
                 for (prj, period) in
                 instance.
                    STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_fixed_cost_per_mw,
                             actual_fixed_cost_per_mw)

        # Params: storage_specified_fixed_cost_per_mwh_yr
        expected_fixed_cost_per_mwh = OrderedDict(
            sorted(
                {("Battery_Specified", 2020): 5000}.items()
            )
        )
        actual_fixed_cost_per_mwh = OrderedDict(
            sorted(
                {(prj, period):
                    instance.storage_specified_fixed_cost_per_mwh_yr[prj,
                                                                    period]
                 for (prj, period) in
                 instance.
                    STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS
                 }.items()
            )
        )
        self.assertDictEqual(expected_fixed_cost_per_mwh,
                             actual_fixed_cost_per_mwh)

if __name__ == "__main__":
    unittest.main()
