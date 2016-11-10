#!/usr/bin/env python

from importlib import import_module
import os.path
import sys
import unittest


TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = []
NAME_OF_MODULE_BEING_TESTED = "project"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='modules')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='modules')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestProject(unittest.TestCase):
    """

    """
    def test_determine_dynamic_components(self):
        """
        Test if dynamic components are loaded correctly
        :return:
        """

        # Create dynamic components class to use
        class DynamicComponents:
            def __init__(self):
                pass
        d = DynamicComponents()

        # Add dynamic components
        MODULE_BEING_TESTED.determine_dynamic_components(
            d, TEST_DATA_DIRECTORY, "", "")

        # Check if capacity type modules are as expected
        expected_required_capacity_modules = [
            "new_build_generator", "specified_no_economic_retirement",
        ]
        actual_required_capacity_modules = \
            sorted(getattr(d, "required_capacity_modules"))
        self.assertListEqual(expected_required_capacity_modules,
                             actual_required_capacity_modules)

        # Check if operational type modules are as expected
        expected_required_operational_modules = [
            "dispatchable_capacity_commit", "must_run", "variable"
        ]
        actual_required_operational_modules = \
            sorted(getattr(d, "required_operational_modules"))
        self.assertListEqual(expected_required_operational_modules,
                             actual_required_operational_modules)

        # Check if headroom variables dictionaries are as expected
        expected_headroom_var_dict = {
            'Coal': [], 'Coal_z2': [], 'Gas_CCGT': [], 'Gas_CCGT_New': [],
            'Gas_CCGT_z2': [], 'Gas_CT': [], 'Gas_CT_New': [], 'Gas_CT_z2': [],
            'Nuclear': [], 'Nuclear_z2': [], 'Wind': [], 'Wind_z2': []
        }
        actual_headroom_var_dict = getattr(d, "headroom_variables")
        self.assertDictEqual(expected_headroom_var_dict,
                             actual_headroom_var_dict)

        # Check if footroom variables dictionaries are as expected
        expected_footroom_var_dict = {
            'Coal': [], 'Coal_z2': [], 'Gas_CCGT': [], 'Gas_CCGT_New': [],
            'Gas_CCGT_z2': [], 'Gas_CT': [], 'Gas_CT_New': [], 'Gas_CT_z2': [],
            'Nuclear': [], 'Nuclear_z2': [], 'Wind': [], 'Wind_z2': []
        }
        actual_footroom_var_dict = getattr(d, "footroom_variables")
        self.assertDictEqual(expected_footroom_var_dict,
                             actual_footroom_var_dict)


if __name__ == "__main__":
    unittest.main()
