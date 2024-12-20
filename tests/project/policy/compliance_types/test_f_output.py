# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data
from tests.project.operations.common_functions import get_project_operational_timepoints

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "test_data",
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "system.load_balance.static_load_requirement",
    "geography.generic_policy",
    "system.policy.generic_policy.generic_policy_requirements",
    "geography.water_network",
    "system.water.water_system_params",
    "system.water.water_flows",
    "system.water.water_nodes",
    "system.water.reservoirs",
    "system.water.water_node_balance",
    "system.water.powerhouses",
    "project",
    "project.capacity.capacity",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
    "project.capacity.potential",
    "project.operations.operational_types",
    "project.operations.power",
]

# Note that we are checking f_output inputs have been added by the
# policy_contribution module, which loops over all required compliance types
NAME_OF_MODULE_BEING_TESTED = "project.policy.policy_contribution"
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
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestRECs(unittest.TestCase):
    """ """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
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
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: FOUTPUT_PROJECT_POLICY_ZONES
        expected_prj_policy_zones = sorted(
            [
                ("Wind", "RPS", "RPSZone1"),
                ("Wind_z2", "RPS", "RPSZone1"),
                ("Gas_CCGT", "Carbon", "CarbonZone1"),
                ("Coal", "Carbon", "CarbonZone1"),
            ]
        )
        actual_prj_policy_zones = sorted(
            [
                (prj, policy, zone)
                for (prj, policy, zone) in instance.FOUTPUT_PROJECT_POLICY_ZONES
            ]
        )
        self.assertListEqual(expected_prj_policy_zones, actual_prj_policy_zones)

        # Param: f_slope
        expected_f_slope = OrderedDict(
            sorted(
                {
                    ("Wind", "RPS", "RPSZone1"): 1,
                    ("Wind_z2", "RPS", "RPSZone1"): 1,
                    ("Gas_CCGT", "Carbon", "CarbonZone1"): 0.4,
                    ("Coal", "Carbon", "CarbonZone1"): 0.7,
                }.items()
            )
        )
        actual_f_slope = OrderedDict(
            sorted(
                {
                    (prj, policy, zone): instance.f_slope[prj, policy, zone]
                    for (prj, policy, zone) in instance.FOUTPUT_PROJECT_POLICY_ZONES
                }.items()
            )
        )

        self.assertDictEqual(expected_f_slope, actual_f_slope)

        # Param: f_intercept
        expected_f_intercept = OrderedDict(
            sorted(
                {
                    ("Wind", "RPS", "RPSZone1"): 0,
                    ("Wind_z2", "RPS", "RPSZone1"): 0,
                    ("Gas_CCGT", "Carbon", "CarbonZone1"): 10,
                    ("Coal", "Carbon", "CarbonZone1"): 100,
                }.items()
            )
        )
        actual_f_intercept = OrderedDict(
            sorted(
                {
                    (prj, policy, zone): instance.f_intercept[prj, policy, zone]
                    for (prj, policy, zone) in instance.FOUTPUT_PROJECT_POLICY_ZONES
                }.items()
            )
        )

        self.assertDictEqual(expected_f_intercept, actual_f_intercept)


if __name__ == "__main__":
    unittest.main()
