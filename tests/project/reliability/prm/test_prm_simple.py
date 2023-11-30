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
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "geography.prm_zones",
    "project",
    "project.capacity.capacity",
    "project.reliability.prm",
    "project.reliability.prm.prm_types",
]
NAME_OF_MODULE_BEING_TESTED = "project.reliability.prm.prm_simple"
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


class TestProjPRMSimple(unittest.TestCase):
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

        # Params: prm_simple_fraction
        expected_prm_frac = OrderedDict(
            sorted(
                {
                    ("Coal", 2020): 0.8,
                    ("Coal_z2", 2020): 0.8,
                    ("Gas_CCGT", 2020): 0.8,
                    ("Gas_CCGT_New", 2020): 0.8,
                    ("Gas_CCGT_New_Binary", 2020): 0.8,
                    ("Gas_CCGT_z2", 2020): 0.8,
                    ("Gas_CT", 2020): 0.8,
                    ("Gas_CT_New", 2020): 0.8,
                    ("Gas_CT_z2", 2020): 0.8,
                    ("Nuclear", 2020): 0.8,
                    ("Nuclear_z2", 2020): 0.8,
                    ("Wind", 2020): 0.8,
                    ("Wind_z2", 2020): 0.8,
                    ("Battery", 2020): 0.8,
                    ("Battery_Binary", 2020): 0.8,
                    ("Battery_Specified", 2020): 0.8,
                    ("Hydro", 2020): 0.8,
                    ("Hydro_NonCurtailable", 2020): 0.8,
                    ("Disp_Binary_Commit", 2020): 0.8,
                    ("Disp_Cont_Commit", 2020): 0.8,
                    ("Disp_No_Commit", 2020): 0.8,
                    ("Clunky_Old_Gen", 2020): 0.8,
                    ("Clunky_Old_Gen2", 2020): 0.8,
                    ("Nuclear_Flexible", 2020): 0.8,
                    ("Coal", 2030): 0.5,
                    ("Coal_z2", 2030): 0.5,
                    ("Gas_CCGT", 2030): 0.5,
                    ("Gas_CCGT_New", 2030): 0.5,
                    ("Gas_CCGT_New_Binary", 2030): 0.5,
                    ("Gas_CCGT_z2", 2030): 0.5,
                    ("Gas_CT", 2030): 0.5,
                    ("Gas_CT_New", 2030): 0.5,
                    ("Gas_CT_z2", 2030): 0.5,
                    ("Nuclear", 2030): 0.5,
                    ("Nuclear_z2", 2030): 0.5,
                    ("Wind", 2030): 0.5,
                    ("Wind_z2", 2030): 0.5,
                    ("Battery", 2030): 0.5,
                    ("Battery_Binary", 2030): 0.5,
                    ("Battery_Specified", 2030): 0.5,
                    ("Hydro", 2030): 0.5,
                    ("Hydro_NonCurtailable", 2030): 0.5,
                    ("Disp_Binary_Commit", 2030): 0.5,
                    ("Disp_Cont_Commit", 2030): 0.5,
                    ("Disp_No_Commit", 2030): 0.5,
                    ("Clunky_Old_Gen", 2030): 0,
                    ("Clunky_Old_Gen2", 2030): 0,
                    ("Nuclear_Flexible", 2030): 0.5,
                }.items()
            )
        )
        actual_prm_frac = OrderedDict(
            sorted(
                {
                    (prj, prd): instance.elcc_simple_fraction[prj, prd]
                    for prj in instance.PRM_PROJECTS
                    for prd in instance.PERIODS
                }.items()
            )
        )
        self.assertDictEqual(expected_prm_frac, actual_prm_frac)
