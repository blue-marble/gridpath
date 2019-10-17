#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from builtins import object
from collections import OrderedDict
from importlib import import_module
import os.path
import pandas as pd
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


class TestProjectInit(unittest.TestCase):
    """

    """
    def test_determine_dynamic_components(self):
        """
        Test if dynamic components are loaded correctly
        :return:
        """

        # Create dynamic components class to use
        class DynamicComponents(object):
            def __init__(self):
                pass
        d = DynamicComponents()

        # Add dynamic components
        MODULE_BEING_TESTED.determine_dynamic_components(
            d, TEST_DATA_DIRECTORY, "", "")

        # NOTE: keeping these hard-coded for they should be easy to update
        # if new types are added
        # Check if capacity type modules are as expected
        expected_required_capacity_modules = sorted([
            "new_build_generator", "new_binary_build_generator",
            "new_build_storage",
            "existing_gen_no_economic_retirement",
            "storage_specified_no_economic_retirement",
            "existing_gen_linear_economic_retirement",
            "existing_gen_binary_economic_retirement",
            "new_shiftable_load_supply_curve"
        ])
        actual_required_capacity_modules = \
            sorted(getattr(d, "required_capacity_modules"))
        self.assertListEqual(expected_required_capacity_modules,
                             actual_required_capacity_modules)

        # Check if availability type modules are as expected
        expected_required_availability_modules = sorted(
            ["exogenous", "binary", "continuous"]
        )
        actual_required_availability_modules = \
            sorted(getattr(d, "required_availability_modules"))
        self.assertListEqual(expected_required_availability_modules,
                             actual_required_availability_modules)

        # Check if operational type modules are as expected
        expected_required_operational_modules = sorted([
            "dispatchable_capacity_commit", "hydro_curtailable",
            "hydro_noncurtailable", "must_run",
            "storage_generic", "variable", "dispatchable_binary_commit",
            "dispatchable_continuous_commit", "dispatchable_no_commit",
            "variable_no_curtailment", "always_on", "shiftable_load_generic"
        ])
        actual_required_operational_modules = \
            sorted(getattr(d, "required_operational_modules"))
        self.assertListEqual(expected_required_operational_modules,
                             actual_required_operational_modules)

        projects_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "projects.tab"),
                sep="\t", usecols=['project']
            )
        projects_list = projects_df['project'].tolist()
        # Check if headroom variables dictionaries are as expected
        expected_headroom_var_dict = {
            prj: [] for prj in projects_list
        }
        actual_headroom_var_dict = getattr(d, "headroom_variables")
        self.assertDictEqual(expected_headroom_var_dict,
                             actual_headroom_var_dict)

        # Check if footroom variables dictionaries are as expected
        expected_footroom_var_dict = {
            prj: [] for prj in projects_list
        }
        actual_footroom_var_dict = getattr(d, "footroom_variables")
        self.assertDictEqual(expected_footroom_var_dict,
                             actual_footroom_var_dict)

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
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
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
                                     )

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Load test data
        projects_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "projects.tab"),
                sep="\t", usecols=[
                    'project', 'load_zone', "capacity_type",
                    "availability_type", "operational_type",
                    "variable_om_cost_per_mwh"
                ]
            )

        # Check data are as expected
        # PROJECTS
        expected_projects = sorted(projects_df['project'].tolist())
        actual_projects = sorted([prj for prj in instance.PROJECTS])

        self.assertListEqual(expected_projects, actual_projects)

        # Params: load_zone
        expected_load_zone = OrderedDict(
            sorted(
                projects_df.set_index('project').to_dict()['load_zone'].items()
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
                projects_df.set_index('project').to_dict()[
                    'capacity_type'].items()
            )
        )

        actual_cap_type = OrderedDict(
            sorted(
                {prj: instance.capacity_type[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )

        self.assertDictEqual(expected_cap_type, actual_cap_type)

        # Params: availability_type
        expected_availability_type = OrderedDict(
            sorted(
                projects_df.set_index('project').to_dict()['availability_type']
                .items()
            )
        )
        actual_availability_type = OrderedDict(
            sorted(
                {prj: instance.availability_type[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )

        self.assertDictEqual(expected_availability_type,
                             actual_availability_type)

        # Params: operational_type
        expected_op_type = OrderedDict(
            sorted(
                projects_df.set_index('project').to_dict()[
                    'operational_type'].items()
            )
        )

        actual_op_type = OrderedDict(
            sorted(
                {prj: instance.operational_type[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )

        self.assertDictEqual(expected_op_type, actual_op_type)

        # Params: variable_om_cost_per_mwh
        expected_var_om_cost = OrderedDict(
            sorted(
                projects_df.set_index('project').to_dict()[
                    'variable_om_cost_per_mwh'].items()
            )
        )
        actual_var_om_cost = OrderedDict(
            sorted(
                {prj: instance.variable_om_cost_per_mwh[prj] for prj in
                 instance.PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_var_om_cost, actual_var_om_cost)

    def test_project_validations(self):
        cols = ["project", "capacity_type", "operational_type",
                "min_stable_level"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", "new_build_generator",
                           "dispatchable_capacity_commit", 0.5]
                          ]),
                "invalid_combos": [("invalid1", "invalid2")],
                "min_stable_level_error": [],
                "combo_error": [],
                },
            # Make sure invalid min_stable_level and invalid combo are flagged
            2: {"df": pd.DataFrame(
                columns=cols,
                data=[["gas_ct1", "cap1", "op2", 1.5],
                      ["gas_ct2", "cap1", "op3", 0]
                      ]),
                "invalid_combos": [("cap1", "op2")],
                "min_stable_level_error": ["Project(s) 'gas_ct1, gas_ct2': expected 0 < min_stable_level <= 1"],
                "combo_error": ["Project(s) 'gas_ct1': 'cap1' and 'op2'"],
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["min_stable_level_error"]
            actual_list = MODULE_BEING_TESTED.validate_min_stable_level(
                df=test_cases[test_case]["df"]
            )
            self.assertListEqual(expected_list, actual_list)

            expected_list = test_cases[test_case]["combo_error"]
            actual_list = MODULE_BEING_TESTED.validate_op_cap_combos(
                df=test_cases[test_case]["df"],
                invalid_combos=test_cases[test_case]["invalid_combos"]
            )
            self.assertListEqual(expected_list, actual_list)


if __name__ == "__main__":
    unittest.main()
