# Copyright 2016-2020 Blue Marble Analytics LLC.
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

from __future__ import print_function

from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones",
    "geography.prm_zones", "project", "project.capacity.capacity",
    "project.reliability.prm", "project.reliability.prm.prm_types"
]
NAME_OF_MODULE_BEING_TESTED = "project.reliability.prm.elcc_surface"
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
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package="gridpath")
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestProjELCCSurface(unittest.TestCase):
    """

    """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
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
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     subproblem="",
                                     stage=""
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
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Param: contributes_to_elcc_surface
        expected_elcc_contr = OrderedDict(
            sorted(
                {"Coal": 0, "Coal_z2": 0,
                 "Gas_CCGT": 0, "Gas_CCGT_New": 0, "Gas_CCGT_New_Binary": 0,
                 "Gas_CCGT_z2": 0, "Gas_CT": 0,
                 "Gas_CT_New": 0, "Gas_CT_z2": 0,
                 "Nuclear": 1, "Nuclear_z2": 0,
                 "Wind": 1, "Wind_z2": 1,
                 "Battery": 0, "Battery_Binary": 0, "Battery_Specified": 0,
                 "Hydro": 0, 'Hydro_NonCurtailable': 0,
                 "Disp_Binary_Commit": 0,
                 "Disp_Cont_Commit": 0, "Disp_No_Commit": 0,
                 "Clunky_Old_Gen": 0, "Clunky_Old_Gen2": 0,
                 "Nuclear_Flexible": 0
                 }.items()
            )
        )

        actual_elcc_contr = OrderedDict(
            sorted(
                {p: instance.contributes_to_elcc_surface[p]
                 for p in instance.PRM_PROJECTS}.items()
            )
        )

        self.assertDictEqual(expected_elcc_contr, actual_elcc_contr)

        # Set: ELCC_SURFACE_PROJECTS
        expected_elcc_surf_prj = sorted([
            "Nuclear", "Wind", "Wind_z2"
        ])
        actual_elcc_surf_prj = sorted([
            p for p in instance.ELCC_SURFACE_PROJECTS
        ])
        self.assertListEqual(expected_elcc_surf_prj, actual_elcc_surf_prj)

        # Set: PROJECT_PERIOD_ELCC_SURFACE_FACETS
        expected_prj_p_f = sorted([
            ("Nuclear", 2020, 1), ("Nuclear", 2020, 2),
            ("Nuclear", 2030, 1), ("Nuclear", 2030, 2),
            ("Wind", 2020, 1), ("Wind", 2020, 2),
            ("Wind", 2030, 1), ("Wind", 2030, 2),
            ("Wind_z2", 2020, 1), ("Wind_z2", 2020, 2),
            ("Wind_z2", 2030, 1), ("Wind_z2", 2030, 2)
        ])

        actual_prj_p_f = sorted([
            (prj, p, f)
            for (prj, p, f) in instance.PROJECT_PERIOD_ELCC_SURFACE_FACETS
        ])

        self.assertListEqual(expected_prj_p_f, actual_prj_p_f)

        # Param: elcc_surface_cap_factor
        expected_elcc_cf = OrderedDict(
            sorted(
                {"Nuclear": 0.123, "Wind": 0.123,
                 "Wind_z2": 0.123, }.items()
            )
        )

        actual_elcc_cf = OrderedDict(
            sorted(
                {p: instance.elcc_surface_cap_factor[p]
                 for p in instance.ELCC_SURFACE_PROJECTS}.items()
            )
        )

        self.assertDictEqual(expected_elcc_cf, actual_elcc_cf)

        # Param: elcc_surface_coefficient
        expected_coeff = OrderedDict(sorted(
            {("Nuclear", 2020, 1): 0.9, ("Nuclear", 2020, 2): 0.9,
             ("Nuclear", 2030, 1): 0.9, ("Nuclear", 2030, 2): 0.9,
             ("Wind", 2020, 1): 0.3, ("Wind", 2020, 2): 0.2,
             ("Wind", 2030, 1): 0.25, ("Wind", 2030, 2): 0.2,
             ("Wind_z2", 2020, 1): 0.3, ("Wind_z2", 2020, 2): 0.25,
             ("Wind_z2", 2030, 1): 0.3, ("Wind_z2", 2030, 2): 0.25
             }.items()
        )
        )

        actual_coeff = OrderedDict(sorted(
            {(prj, p, f): instance.elcc_surface_coefficient[prj, p, f]
             for (prj, p, f) in instance.PROJECT_PERIOD_ELCC_SURFACE_FACETS
             }.items()
        )
        )
        self.assertDictEqual(expected_coeff, actual_coeff)

        # Param: prm_peak_load_mw
        expected_prm_peak_load = OrderedDict(sorted(
            {("PRM_Zone1", 2020): 49406.65942,
             ("PRM_Zone1", 2030): 49406.65942,
             ("PRM_Zone2", 2020): 49913.83791,
             ("PRM_Zone2", 2030): 49913.83791,
             }.items()
        )
        )

        actual_prm_peak_load = OrderedDict(sorted(
            {(z, p): instance.prm_peak_load_mw[z, p]
             for (z, p) in instance.PRM_ZONE_PERIODS_FOR_ELCC_SURFACE
             }.items()
        )
        )
        self.assertDictEqual(expected_prm_peak_load, actual_prm_peak_load)

        # Param: prm_peak_load_mw
        expected_annua_load = OrderedDict(sorted(
            {("PRM_Zone1", 2020): 242189141,
             ("PRM_Zone1", 2030): 242189141,
             ("PRM_Zone2", 2020): 244545760.8,
             ("PRM_Zone2", 2030): 244545760.8,
             }.items()
        )
        )

        actual_annual_load = OrderedDict(sorted(
            {(z, p): instance.prm_annual_load_mwh[z, p]
             for (z, p) in instance.PRM_ZONE_PERIODS_FOR_ELCC_SURFACE
             }.items()
        )
        )
        self.assertDictEqual(expected_annua_load, actual_annual_load)
