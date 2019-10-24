#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from collections import OrderedDict
from importlib import import_module
import os.path
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "test_data")

# No prerequisite modules
NAME_OF_MODULE_BEING_TESTED = "geography.load_zones"

try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestLoadZones(unittest.TestCase):
    """

    """
    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=[],
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
        add_components_and_load_data(prereq_modules=[],
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
                                     )

    def test_load_zone_data_loads_correctly(self):
        """
        Create LOAD_ZONES set and load data; check resulting set is as expected
        :return:
        """
        m, data = \
            add_components_and_load_data(prereq_modules=[],
                                         module_to_test=MODULE_BEING_TESTED,
                                         test_data_dir=TEST_DATA_DIRECTORY,
                                         subproblem="",
                                         stage="")
        instance = m.create_instance(data)
        expected = sorted(["Zone1", "Zone2", "Zone3"])
        actual = sorted([z for z in instance.LOAD_ZONES])
        self.assertListEqual(expected, actual,
                             msg="LOAD_ZONES set data does not load correctly."
                             )

        # Param: allow_overgeneration
        expected_allow_overgen = OrderedDict(
            sorted({"Zone1": 1, "Zone2": 1}.items())
        )
        actual_allow_overgen = OrderedDict(
            sorted(
                {z: instance.allow_overgeneration[z]
                 for z in instance.LOAD_ZONES}.items()
            )
        )
        self.assertDictEqual(expected_allow_overgen, actual_allow_overgen)

        # Param: overgeneration_penalty_per_mw
        expected_overgen_penalty = OrderedDict(
            sorted({"Zone1": 99999999, "Zone2": 99999999}.items())
        )
        actual_overgen_penalty = OrderedDict(
            sorted(
                {z: instance.overgeneration_penalty_per_mw[z]
                 for z in instance.LOAD_ZONES}.items()
            )
        )
        self.assertDictEqual(expected_overgen_penalty, actual_overgen_penalty)

        # Param: allow_unserved_energy
        expected_allow_unserved_energy = OrderedDict(
            sorted({"Zone1": 1, "Zone2": 1}.items())
        )
        actual_allow_unserved_energy = OrderedDict(
            sorted(
                {z: instance.allow_overgeneration[z]
                 for z in instance.LOAD_ZONES}.items()
            )
        )
        self.assertDictEqual(expected_allow_unserved_energy,
                             actual_allow_unserved_energy)

        # Param: unserved_energy_penalty_per_mw
        expected_unserved_energy_penalty = OrderedDict(
            sorted({"Zone1": 99999999, "Zone2": 99999999}.items())
        )
        actual_unserved_energy_penalty = OrderedDict(
            sorted(
                {z: instance.unserved_energy_penalty_per_mw[z]
                 for z in instance.LOAD_ZONES}.items()
            )
        )
        self.assertDictEqual(expected_unserved_energy_penalty,
                             actual_unserved_energy_penalty)


if __name__ == "__main__":
    unittest.main()
