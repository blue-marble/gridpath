# Copyright 2016-2024 Blue Marble Analytics LLC.
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
    "project",
    "project.capacity.capacity",
    "project.capacity.potential",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
]
NAME_OF_MODULE_BEING_TESTED = (
    "project.operations.operational_types.energy_slice_hrz_shaping"
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


class TestEnergyHrzShaping(unittest.TestCase):
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

        # Set: ENERGY_SLICE_HRZ_SHAPING
        expected_gen_set = sorted(["Energy_Slice_Hrz_Shaping"])
        actual_gen_set = sorted([prj for prj in instance.ENERGY_SLICE_HRZ_SHAPING])
        self.assertListEqual(expected_gen_set, actual_gen_set)

        # Set: ENERGY_SLICE_HRZ_SHAPING_OPR_PRDS
        expected_op_prds = sorted(
            [("Energy_Slice_Hrz_Shaping", 2020), ("Energy_Slice_Hrz_Shaping", 2030)]
        )
        actual_op_prds = sorted(
            [(prj, prd) for (prj, prd) in instance.ENERGY_SLICE_HRZ_SHAPING_OPR_PRDS]
        )
        self.assertListEqual(
            expected_op_prds,
            actual_op_prds,
        )

        # Set: ENERGY_SLICE_HRZ_SHAPING_OPR_TMPS
        expected_operational_timepoints_by_project = sorted(
            get_project_operational_timepoints(expected_gen_set)
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in instance.ENERGY_SLICE_HRZ_SHAPING_OPR_TMPS]
        )

        self.assertListEqual(
            expected_operational_timepoints_by_project,
            actual_operational_timepoints_by_project,
        )

        # Set: ENERGY_SLICE_HRZ_SHAPING_OPR_BT_HRZS
        expected_bt_hrz = sorted(
            [
                ("Energy_Slice_Hrz_Shaping", "day", 202001),
                ("Energy_Slice_Hrz_Shaping", "day", 202002),
                ("Energy_Slice_Hrz_Shaping", "day", 203001),
                ("Energy_Slice_Hrz_Shaping", "day", 203002),
            ]
        )
        actual_bt_hrz = sorted(
            [
                (prj, bt, h)
                for (prj, bt, h) in instance.ENERGY_SLICE_HRZ_SHAPING_OPR_BT_HRZS
            ]
        )
        self.assertListEqual(
            expected_bt_hrz,
            actual_bt_hrz,
        )

        # Param: energy_slice_hrz_shaping_hrz_energy
        expected_frac = {
            ("Energy_Slice_Hrz_Shaping", "day", 202001): 1000,
            ("Energy_Slice_Hrz_Shaping", "day", 202002): 1000,
            ("Energy_Slice_Hrz_Shaping", "day", 203001): 1000,
            ("Energy_Slice_Hrz_Shaping", "day", 203002): 1000,
        }

        actual_frac = {
            (prj, bt, h): instance.energy_slice_hrz_shaping_hrz_energy[prj, bt, h]
            for (prj, bt, h) in instance.ENERGY_SLICE_HRZ_SHAPING_OPR_BT_HRZS
        }
        self.assertDictEqual(expected_frac, actual_frac)

        # Param: energy_slice_hrz_shaping_min_power
        expected_min = {
            ("Energy_Slice_Hrz_Shaping", "day", 202001): 1.000002,
            ("Energy_Slice_Hrz_Shaping", "day", 202002): 1.000002,
            ("Energy_Slice_Hrz_Shaping", "day", 203001): 1.000002,
            ("Energy_Slice_Hrz_Shaping", "day", 203002): 1.000002,
        }

        actual_min = {
            (prj, bt, h): instance.energy_slice_hrz_shaping_min_power[prj, bt, h]
            for (prj, bt, h) in instance.ENERGY_SLICE_HRZ_SHAPING_OPR_BT_HRZS
        }
        self.assertDictEqual(expected_min, actual_min)

        # Param: energy_slice_hrz_shaping_max_power
        expected_max = {
            ("Energy_Slice_Hrz_Shaping", "day", 202001): 6,
            ("Energy_Slice_Hrz_Shaping", "day", 202002): 6,
            ("Energy_Slice_Hrz_Shaping", "day", 203001): 6,
            ("Energy_Slice_Hrz_Shaping", "day", 203002): 6,
        }

        actual_max = {
            (prj, bt, h): instance.energy_slice_hrz_shaping_max_power[prj, bt, h]
            for (prj, bt, h) in instance.ENERGY_SLICE_HRZ_SHAPING_OPR_BT_HRZS
        }
        self.assertDictEqual(expected_max, actual_max)


if __name__ == "__main__":
    unittest.main()
