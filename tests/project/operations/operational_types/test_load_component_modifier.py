# Copyright 2016-2025 Blue Marble Analytics LLC.
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


from importlib import import_module
import os.path
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data
from tests.project.operations.common_functions import get_project_operational_timepoints

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "system.load_balance",
    "system.load_balance.static_load_requirement",
    "project",
    "project.capacity.capacity",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
]
NAME_OF_MODULE_BEING_TESTED = (
    "project.operations.operational_types.load_component_modifier"
)
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


class TestLoadComponentModifier(unittest.TestCase):
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

    def test_data_load_correctly(self):
        """
        Test that are data loaded are as expected
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

        # Sets: LOAD_COMPONENT_MODIFIER_PRJS
        expected_projects = ["DSM_Load_Component_Modifier"]
        actual_projects = sorted([p for p in instance.LOAD_COMPONENT_MODIFIER_PRJS])
        self.assertListEqual(expected_projects, actual_projects)

        # LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS
        expected_tmps = sorted(get_project_operational_timepoints(expected_projects))
        actual_tmps = sorted(
            [tmp for tmp in instance.LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS]
        )
        self.assertListEqual(expected_tmps, actual_tmps)

        # LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS
        expected_prds = [
            ("DSM_Load_Component_Modifier", 2020),
            ("DSM_Load_Component_Modifier", 2030),
        ]
        actual_prds = sorted(
            [prd for prd in instance.LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS]
        )
        self.assertListEqual(expected_prds, actual_prds)

        # Param: load_component_modifier_linked_load_component
        expected_load_component_modifier_linked_load_component = {
            "DSM_Load_Component_Modifier": "all",
        }
        actual_load_component_modifier_linked_load_component = {
            prj: instance.load_component_modifier_linked_load_component[prj]
            for prj in instance.LOAD_COMPONENT_MODIFIER_PRJS
        }
        self.assertDictEqual(
            expected_load_component_modifier_linked_load_component,
            actual_load_component_modifier_linked_load_component,
        )

        # Param: load_component_modifier_fraction
        all_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs", "load_component_modifier_fractions.tab"
            ),
            sep="\t",
        )

        vnc_df = all_df[all_df["project"].isin(expected_projects)]
        expected_fractions = vnc_df.set_index(["project", "timepoint"]).to_dict()[
            "fraction"
        ]

        actual_fractions = {
            (g, tmp): instance.load_component_modifier_fraction[g, tmp]
            for (g, tmp) in instance.LOAD_COMPONENT_MODIFIER_PRJS_OPR_TMPS
        }
        self.assertDictEqual(expected_fractions, actual_fractions)

        # Param: load_component_modifier_load_component_peak_load_in_period
        expected_peak = {
            ("DSM_Load_Component_Modifier", 2020): 50,
            ("DSM_Load_Component_Modifier", 2030): 50,
        }
        actual_peak = {
            (
                prj,
                prd,
            ): instance.load_component_modifier_load_component_peak_load_in_period[
                prj, prd
            ]
            for (prj, prd) in instance.LOAD_COMPONENT_MODIFIER_PRJS_OPR_PRDS
        }
        self.assertDictEqual(expected_peak, actual_peak)


if __name__ == "__main__":
    unittest.main()
