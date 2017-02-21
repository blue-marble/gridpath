#!/usr/bin/env python

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
     "system.load_balance.load_balance"]
NAME_OF_MODULE_BEING_TESTED = "system.load_balance.costs"
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


class TestCosts(unittest.TestCase):
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
        Test components initialized with expected data
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

        # Param: overgeneration_penalty_per_mw
        expected_overgen_penalty = OrderedDict(sorted({
            "Zone1": 99999999, "Zone2": 99999999
                                                      }.items()
                                                      )
                                               )
        actual_overgen_penalty = OrderedDict(sorted({
            z: instance.overgeneration_penalty_per_mw[z]
            for z in instance.LOAD_ZONES
                                                      }.items()
                                                    )
                                             )
        self.assertDictEqual(expected_overgen_penalty, actual_overgen_penalty)

        # Param: unserved_energy_penalty_per_mw
        expected_unserved_energy_penalty = OrderedDict(sorted({
             "Zone1": 99999999, "Zone2": 99999999
                                                      }.items()
                                                      )
                                               )
        actual_unserved_energy_penalty = OrderedDict(sorted({
            z: instance.unserved_energy_penalty_per_mw[z]
            for z in instance.LOAD_ZONES
                                                        }.items()
                                                    )
                                             )
        self.assertDictEqual(expected_unserved_energy_penalty,
                             actual_unserved_energy_penalty)

if __name__ == "__main__":
    unittest.main()
