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
    "project.availability.availability",
    "project.fuels",
    "project.operations",
    "geography.water_network",
    "system.water.water_system_params",
    "system.water.water_nodes",
    "system.water.water_flows",
    "system.water.water_node_inflows_outflows",
    "system.water.reservoirs",
    "system.water.water_node_balance",
    "system.water.powerhouses",
]
NAME_OF_MODULE_BEING_TESTED = "project.operations.operational_types.gen_hydro_water"
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


class TestStor(unittest.TestCase):
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

    def test_capacity_data_load_correctly(self):
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

        # Sets: GEN_HYDRO_WATER
        expected_projects = ["Hydro_System_Gen1"]
        actual_projects = sorted([p for p in instance.GEN_HYDRO_WATER])
        self.assertListEqual(expected_projects, actual_projects)

        # GEN_HYDRO_WATER_OPR_TMPS
        expected_tmps = sorted(get_project_operational_timepoints(expected_projects))
        actual_tmps = sorted([tmp for tmp in instance.GEN_HYDRO_WATER_OPR_TMPS])
        self.assertListEqual(expected_tmps, actual_tmps)

        # Param: gen_hydro_water_powerhouse
        expected_powerhouses = {
            "Hydro_System_Gen1": "Powerhouse1",
        }
        actual_powerhouses = {
            prj: instance.gen_hydro_water_powerhouse[prj]
            for prj in instance.GEN_HYDRO_WATER
        }
        self.assertDictEqual(expected_powerhouses, actual_powerhouses)

        # Param: gen_hydro_water_generator_efficiency
        expected_eff = {
            "Hydro_System_Gen1": 0.95,
        }
        actual_eff = {
            prj: instance.gen_hydro_water_generator_efficiency[prj]
            for prj in instance.GEN_HYDRO_WATER
        }
        self.assertDictEqual(expected_eff, actual_eff)

        # GEN_HYDRO_WATER_BT_HRZ_W_TOTAL_RAMP_UP_LIMITS
        expected_bh_ramp_up = [("Hydro_System_Gen1", "day", 202001)]
        actual_bh_ramp_up = sorted(
            [
                (prj, bt, hrz)
                for (
                    prj,
                    bt,
                    hrz,
                ) in instance.GEN_HYDRO_WATER_BT_HRZ_W_TOTAL_RAMP_UP_LIMITS
            ]
        )
        self.assertListEqual(expected_bh_ramp_up, actual_bh_ramp_up)

        # Param: gen_hydro_water_total_ramp_up_limit_mw
        expected_gen_hydro_water_total_ramp_up_limit_mw = {
            ("Hydro_System_Gen1", "day", 202001): 0
        }
        actual_gen_hydro_water_total_ramp_up_limit_mw = {
            (prj, bt, hrz): instance.gen_hydro_water_total_ramp_up_limit_mw[
                prj, bt, hrz
            ]
            for (prj, bt, hrz) in instance.GEN_HYDRO_WATER_BT_HRZ_W_TOTAL_RAMP_UP_LIMITS
        }
        self.assertDictEqual(
            expected_gen_hydro_water_total_ramp_up_limit_mw,
            actual_gen_hydro_water_total_ramp_up_limit_mw,
        )


if __name__ == "__main__":
    unittest.main()
