#!/usr/bin/env python

from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data


TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
     "temporal.operations.timepoints", "temporal.operations.horizons",
     "temporal.investment.periods", "geography.load_zones"]
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
        expected_required_capacity_modules = sorted([
            "new_build_generator", "new_build_storage",
            "specified_no_economic_retirement",
            "storage_specified_no_economic_retirement",
            "existing_gen_linear_economic_retirement"
        ])
        actual_required_capacity_modules = \
            sorted(getattr(d, "required_capacity_modules"))
        self.assertListEqual(expected_required_capacity_modules,
                             actual_required_capacity_modules)

        # Check if operational type modules are as expected
        expected_required_operational_modules = sorted([
            "dispatchable_capacity_commit", "hydro_conventional", "must_run",
            "storage_generic", "variable", "dispatchable_binary_commit",
            "dispatchable_continuous_commit", "dispatchable_no_commit"
        ])
        actual_required_operational_modules = \
            sorted(getattr(d, "required_operational_modules"))
        self.assertListEqual(expected_required_operational_modules,
                             actual_required_operational_modules)

        # Check if headroom variables dictionaries are as expected
        expected_headroom_var_dict = {
            'Battery': [], 'Battery_Specified': [], 'Coal': [], 'Coal_z2': [],
            'Gas_CCGT': [], 'Gas_CCGT_New': [], 'Gas_CCGT_z2': [], 'Gas_CT': [],
            'Gas_CT_New': [], 'Gas_CT_z2': [], 'Hydro': [],
            'Nuclear': [], 'Nuclear_z2': [], 'Wind': [], 'Wind_z2': [],
            'Disp_Binary_Commit': [], "Disp_Cont_Commit": [],
            "Disp_No_Commit": [], "Clunky_Old_Gen": []
        }
        actual_headroom_var_dict = getattr(d, "headroom_variables")
        self.assertDictEqual(expected_headroom_var_dict,
                             actual_headroom_var_dict)

        # Check if footroom variables dictionaries are as expected
        expected_footroom_var_dict = {
            'Battery': [], 'Battery_Specified': [], 'Coal': [], 'Coal_z2': [],
            'Gas_CCGT': [], 'Gas_CCGT_New': [], 'Gas_CCGT_z2': [], 'Gas_CT': [],
            'Gas_CT_New': [], 'Gas_CT_z2': [], 'Hydro': [],
            'Nuclear': [], 'Nuclear_z2': [], 'Wind': [], 'Wind_z2': [],
            'Disp_Binary_Commit': [], "Disp_Cont_Commit": [],
            "Disp_No_Commit": [], "Clunky_Old_Gen": []
        }
        actual_footroom_var_dict = getattr(d, "footroom_variables")
        self.assertDictEqual(expected_footroom_var_dict,
                             actual_footroom_var_dict)

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

    def test_project_data_load_correctly(self):
        """

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

        # Check data are as expected
        # PROJECTS
        expected_projects = sorted([
            "Coal", "Coal_z2", "Gas_CCGT", "Gas_CCGT_New", "Gas_CCGT_z2",
            "Gas_CT", "Gas_CT_New", "Gas_CT_z2", "Nuclear", "Nuclear_z2",
            "Wind", "Wind_z2", "Battery", "Battery_Specified", "Hydro",
            "Disp_Binary_Commit", "Disp_Cont_Commit", "Disp_No_Commit",
            "Clunky_Old_Gen"]
            )
        actual_projects = sorted([prj for prj in instance.PROJECTS])

        self.assertListEqual(expected_projects, actual_projects)

        # Params: load_zone
        expected_load_zone = OrderedDict(
            sorted(
                {"Coal": "Zone1", "Coal_z2": "Zone2", "Gas_CCGT": "Zone1",
                 "Gas_CCGT_New": "Zone1", "Gas_CCGT_z2": "Zone2",
                 "Gas_CT": "Zone1",
                 "Gas_CT_New": "Zone1", "Gas_CT_z2": "Zone2",
                 "Nuclear": "Zone1",
                 "Nuclear_z2": "Zone2", "Wind": "Zone1",
                 "Wind_z2": "Zone2", "Battery": "Zone1",
                 "Battery_Specified": "Zone1", "Hydro": "Zone1",
                 "Disp_Binary_Commit": "Zone1", "Disp_Cont_Commit": "Zone1",
                 "Disp_No_Commit": "Zone1", "Clunky_Old_Gen": "Zone1"}.items()
            )
        )
        actual_load_zone = OrderedDict(
            sorted(
                {prj: instance.load_zone[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_load_zone, actual_load_zone)

        # Params: capacity_type
        expected_cap_type = OrderedDict(
            sorted(
                {"Coal": "specified_no_economic_retirement",
                 "Coal_z2": "specified_no_economic_retirement",
                 "Gas_CCGT": "specified_no_economic_retirement",
                 "Gas_CCGT_New": "new_build_generator",
                 "Gas_CCGT_z2": "specified_no_economic_retirement",
                 "Gas_CT": "specified_no_economic_retirement",
                 "Gas_CT_New": "new_build_generator",
                 "Gas_CT_z2": "specified_no_economic_retirement",
                 "Nuclear": "specified_no_economic_retirement",
                 "Nuclear_z2": "specified_no_economic_retirement",
                 "Wind": "specified_no_economic_retirement",
                 "Wind_z2": "specified_no_economic_retirement",
                 "Battery": "new_build_storage",
                 "Battery_Specified":
                     "storage_specified_no_economic_retirement",
                 "Hydro": "specified_no_economic_retirement",
                 "Disp_Binary_Commit": "specified_no_economic_retirement",
                 "Disp_Cont_Commit": "specified_no_economic_retirement",
                 "Disp_No_Commit": "specified_no_economic_retirement",
                 "Clunky_Old_Gen": "existing_gen_linear_economic_retirement"
                 }.items()
            )
        )
        actual_cap_type = OrderedDict(
            sorted(
                {prj: instance.capacity_type[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_cap_type, actual_cap_type)

        # Params: variable_om_cost_per_mwh
        expected_var_om_cost = OrderedDict(
            sorted(
                {"Coal": 1, "Coal_z2": 1, "Gas_CCGT": 2, "Gas_CCGT_New": 2,
                 "Gas_CCGT_z2": 2, "Gas_CT": 2, "Gas_CT_New": 2, "Gas_CT_z2": 2,
                 "Nuclear": 1, "Nuclear_z2": 1, "Wind": 0, "Wind_z2": 0,
                 "Battery": 0, "Battery_Specified": 0, "Hydro": 0,
                 "Disp_Binary_Commit": 0, "Disp_Cont_Commit": 0,
                 "Disp_No_Commit": 0, "Clunky_Old_Gen": 1
                 }.items()
            )
        )
        actual_var_om_cost = OrderedDict(
            sorted(
                {prj: instance.variable_om_cost_per_mwh[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_var_om_cost, actual_var_om_cost)


if __name__ == "__main__":
    unittest.main()
