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

TEST_DATA_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_data"
)

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.investment.periods",
    "temporal.operations.horizons",
    "geography.load_zones",
    "project",
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_types.energy_spec"
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


class TestStorSpec(unittest.TestCase):
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
        Test that the data loaded are as expected
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

        # Set: GEN_ENERGY_SPEC_OPR_PRDS
        expected_proj_period_set = sorted(
            [
                ("Energy_Hrz_Shaping", 2020),
                ("Energy_Hrz_Shaping", 2030),
                ("Energy_LF", 2020),
                ("Energy_LF", 2030),
                ("Energy_Spec", 2020),
                ("Energy_Spec", 2030),
            ]
        )
        actual_proj_period_set = sorted(
            [(prj, period) for (prj, period) in instance.GEN_ENERGY_SPEC_OPR_PRDS]
        )
        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)

        # Params: energy_spec_energy_mwh
        expected_specified_energy = OrderedDict(
            sorted(
                {
                    ("Energy_Spec", 2020): 1000,
                    ("Energy_Spec", 2030): 1000,
                    ("Energy_Hrz_Shaping", 2020): 1000,
                    ("Energy_Hrz_Shaping", 2030): 1000,
                    ("Energy_LF", 2020): 1000,
                    ("Energy_LF", 2030): 1000,
                }.items()
            )
        )
        actual_specified_energy = OrderedDict(
            sorted(
                {
                    (prj, period): instance.energy_spec_energy_mwh[prj, period]
                    for (prj, period) in instance.GEN_ENERGY_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_specified_energy, actual_specified_energy)

        # Params: shaping_capacity_mw
        expected_shaping_cap = OrderedDict(
            sorted(
                {
                    ("Energy_Spec", 2020): 0,
                    ("Energy_Spec", 2030): 0,
                    ("Energy_Hrz_Shaping", 2020): 0,
                    ("Energy_Hrz_Shaping", 2030): 0,
                    ("Energy_LF", 2020): 0,
                    ("Energy_LF", 2030): 0,
                }.items()
            )
        )
        actual_shaping_cap = OrderedDict(
            sorted(
                {
                    (prj, period): instance.shaping_capacity_mw[prj, period]
                    for (prj, period) in instance.GEN_ENERGY_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_shaping_cap, actual_shaping_cap)

        # Params: energy_spec_fixed_cost_per_energy_mwh_yr
        expected_fc = OrderedDict(
            sorted(
                {
                    ("Energy_Spec", 2020): 0,
                    ("Energy_Spec", 2030): 0,
                    ("Energy_Hrz_Shaping", 2020): 0,
                    ("Energy_Hrz_Shaping", 2030): 0,
                    ("Energy_LF", 2020): 0,
                    ("Energy_LF", 2030): 0,
                }.items()
            )
        )
        actual_fc = OrderedDict(
            sorted(
                {
                    (prj, period): instance.energy_spec_fixed_cost_per_energy_mwh_yr[
                        prj, period
                    ]
                    for (prj, period) in instance.GEN_ENERGY_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_fc, actual_fc)

        # Params: fixed_cost_per_shaping_mw_yr
        expected_shap_cap_fc = OrderedDict(
            sorted(
                {
                    ("Energy_Spec", 2020): 0,
                    ("Energy_Spec", 2030): 0,
                    ("Energy_Hrz_Shaping", 2020): 0,
                    ("Energy_Hrz_Shaping", 2030): 0,
                    ("Energy_LF", 2020): 0,
                    ("Energy_LF", 2030): 0,
                }.items()
            )
        )
        actual_shap_cap_fc = OrderedDict(
            sorted(
                {
                    (prj, period): instance.fixed_cost_per_shaping_mw_yr[prj, period]
                    for (prj, period) in instance.GEN_ENERGY_SPEC_OPR_PRDS
                }.items()
            )
        )
        self.assertDictEqual(expected_shap_cap_fc, actual_shap_cap_fc)


if __name__ == "__main__":
    unittest.main()
