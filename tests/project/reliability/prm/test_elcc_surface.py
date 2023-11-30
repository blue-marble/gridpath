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
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestProjELCCSurface(unittest.TestCase):
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

        # Set: ELCC_SURFACE_PRM_ZONE_PERIODS
        expected_surface_zone_periods = sorted(
            [
                ("Nuclear", "PRM_Zone1", 2020),
                ("Nuclear", "PRM_Zone1", 2030),
                ("Wind_Solar", "PRM_Zone1", 2020),
                ("Wind_Solar", "PRM_Zone1", 2030),
                ("Wind_Solar", "PRM_Zone2", 2020),
                ("Wind_Solar", "PRM_Zone2", 2030),
            ]
        )

        actual_surface_zone_periods = sorted(
            [(s, z, p) for (s, z, p) in instance.ELCC_SURFACE_PRM_ZONE_PERIODS]
        )

        self.assertListEqual(expected_surface_zone_periods, actual_surface_zone_periods)

        # Param: prm_peak_load_mw
        expected_peak_load = OrderedDict(
            sorted(
                {
                    ("Nuclear", "PRM_Zone1", 2020): 49406.65942,
                    ("Nuclear", "PRM_Zone1", 2030): 49406.65942,
                    ("Wind_Solar", "PRM_Zone1", 2020): 49406.65942,
                    ("Wind_Solar", "PRM_Zone1", 2030): 49406.65942,
                    ("Wind_Solar", "PRM_Zone2", 2020): 49913.83791,
                    ("Wind_Solar", "PRM_Zone2", 2030): 49913.83791,
                }.items()
            )
        )

        actual_peak_load = OrderedDict(
            sorted(
                {
                    (s, z, p): instance.prm_peak_load_mw[s, z, p]
                    for (s, z, p) in instance.ELCC_SURFACE_PRM_ZONE_PERIODS
                }.items()
            )
        )

        self.assertDictEqual(expected_peak_load, actual_peak_load)

        # Param: prm_annual_load_mwh
        expected_annual_load = OrderedDict(
            sorted(
                {
                    ("Nuclear", "PRM_Zone1", 2020): 242189141,
                    ("Nuclear", "PRM_Zone1", 2030): 242189141,
                    ("Wind_Solar", "PRM_Zone1", 2020): 242189141,
                    ("Wind_Solar", "PRM_Zone1", 2030): 242189141,
                    ("Wind_Solar", "PRM_Zone2", 2020): 244545760.8,
                    ("Wind_Solar", "PRM_Zone2", 2030): 244545760.8,
                }.items()
            )
        )

        actual_annual_load = OrderedDict(
            sorted(
                {
                    (s, z, p): instance.prm_annual_load_mwh[s, z, p]
                    for (s, z, p) in instance.ELCC_SURFACE_PRM_ZONE_PERIODS
                }.items()
            )
        )

        self.assertDictEqual(expected_annual_load, actual_annual_load)

        # Param: elcc_surface_name
        expected_elcc_surface_names = OrderedDict(
            sorted(
                {
                    "Coal": None,
                    "Coal_z2": None,
                    "Gas_CCGT": None,
                    "Gas_CCGT_New": None,
                    "Gas_CCGT_New_Binary": None,
                    "Gas_CCGT_z2": None,
                    "Gas_CT": None,
                    "Gas_CT_New": None,
                    "Gas_CT_z2": None,
                    "Nuclear": "Nuclear",
                    "Nuclear_z2": None,
                    "Wind": "Wind_Solar",
                    "Wind_z2": "Wind_Solar",
                    "Battery": None,
                    "Battery_Binary": None,
                    "Battery_Specified": None,
                    "Hydro": None,
                    "Hydro_NonCurtailable": None,
                    "Disp_Binary_Commit": None,
                    "Disp_Cont_Commit": None,
                    "Disp_No_Commit": None,
                    "Clunky_Old_Gen": None,
                    "Clunky_Old_Gen2": None,
                    "Nuclear_Flexible": None,
                }.items()
            )
        )

        actual_elcc_surface_names = OrderedDict(
            sorted(
                {
                    p: instance.elcc_surface_name[p] for p in instance.PRM_PROJECTS
                }.items()
            )
        )

        self.assertDictEqual(expected_elcc_surface_names, actual_elcc_surface_names)

        # Param: elcc_surface_cap_factor
        expected_elcc_cf = OrderedDict(
            sorted(
                {
                    "Coal": None,
                    "Coal_z2": None,
                    "Gas_CCGT": None,
                    "Gas_CCGT_New": None,
                    "Gas_CCGT_New_Binary": None,
                    "Gas_CCGT_z2": None,
                    "Gas_CT": None,
                    "Gas_CT_New": None,
                    "Gas_CT_z2": None,
                    "Nuclear": 0.123,
                    "Nuclear_z2": None,
                    "Wind": 0.123,
                    "Wind_z2": 0.123,
                    "Battery": None,
                    "Battery_Binary": None,
                    "Battery_Specified": None,
                    "Hydro": None,
                    "Hydro_NonCurtailable": None,
                    "Disp_Binary_Commit": None,
                    "Disp_Cont_Commit": None,
                    "Disp_No_Commit": None,
                    "Clunky_Old_Gen": None,
                    "Clunky_Old_Gen2": None,
                    "Nuclear_Flexible": None,
                }.items()
            )
        )

        actual_elcc_cf = OrderedDict(
            sorted(
                {
                    p: instance.elcc_surface_cap_factor[p]
                    for p in instance.PRM_PROJECTS
                }.items()
            )
        )

        self.assertDictEqual(expected_elcc_cf, actual_elcc_cf)

        # Set: ELCC_SURFACE_PROJECTS
        expected_elcc_surf_prj = sorted(
            [("Nuclear", "Nuclear"), ("Wind_Solar", "Wind"), ("Wind_Solar", "Wind_z2")]
        )
        actual_elcc_surf_prj = sorted(
            [(s, p) for (s, p) in instance.ELCC_SURFACE_PROJECTS]
        )
        self.assertListEqual(expected_elcc_surf_prj, actual_elcc_surf_prj)

        # Set: ELCC_SURFACE_PROJECTS_BY_PRM_ZONE
        expected_surface_projects_by_zone = OrderedDict(
            sorted(
                {
                    "PRM_Zone1": [("Nuclear", "Nuclear"), ("Wind_Solar", "Wind")],
                    "PRM_Zone2": [("Wind_Solar", "Wind_z2")],
                }.items()
            )
        )

        actual_surface_projects_by_zone = OrderedDict(
            sorted(
                {
                    z: [
                        (s, p)
                        for (s, p) in instance.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE[z]
                    ]
                    for z in instance.PRM_ZONES
                }.items()
            )
        )

        self.assertDictEqual(
            expected_surface_projects_by_zone, actual_surface_projects_by_zone
        )

        # Set: ELCC_SURFACE_PROJECT_PERIOD_FACETS
        expected_s_prj_p_f = sorted(
            [
                ("Nuclear", "Nuclear", 2020, 1),
                ("Nuclear", "Nuclear", 2020, 2),
                ("Nuclear", "Nuclear", 2030, 1),
                ("Nuclear", "Nuclear", 2030, 2),
                ("Wind_Solar", "Wind", 2020, 1),
                ("Wind_Solar", "Wind", 2020, 2),
                ("Wind_Solar", "Wind", 2030, 1),
                ("Wind_Solar", "Wind", 2030, 2),
                ("Wind_Solar", "Wind_z2", 2020, 1),
                ("Wind_Solar", "Wind_z2", 2020, 2),
                ("Wind_Solar", "Wind_z2", 2030, 1),
                ("Wind_Solar", "Wind_z2", 2030, 2),
            ]
        )

        actual_s_prj_p_f = sorted(
            [
                (s, prj, p, f)
                for (s, prj, p, f) in instance.ELCC_SURFACE_PROJECT_PERIOD_FACETS
            ]
        )

        self.assertListEqual(expected_s_prj_p_f, actual_s_prj_p_f)

        # Param: elcc_surface_coefficient
        expected_coeff = OrderedDict(
            sorted(
                {
                    ("Nuclear", "Nuclear", 2020, 1): 0.9,
                    ("Nuclear", "Nuclear", 2020, 2): 0.9,
                    ("Nuclear", "Nuclear", 2030, 1): 0.9,
                    ("Nuclear", "Nuclear", 2030, 2): 0.9,
                    ("Wind_Solar", "Wind", 2020, 1): 0.3,
                    ("Wind_Solar", "Wind", 2020, 2): 0.2,
                    ("Wind_Solar", "Wind", 2030, 1): 0.25,
                    ("Wind_Solar", "Wind", 2030, 2): 0.2,
                    ("Wind_Solar", "Wind_z2", 2020, 1): 0.3,
                    ("Wind_Solar", "Wind_z2", 2020, 2): 0.25,
                    ("Wind_Solar", "Wind_z2", 2030, 1): 0.3,
                    ("Wind_Solar", "Wind_z2", 2030, 2): 0.25,
                }.items()
            )
        )

        actual_coeff = OrderedDict(
            sorted(
                {
                    (s, prj, p, f): instance.elcc_surface_coefficient[s, prj, p, f]
                    for (s, prj, p, f) in instance.ELCC_SURFACE_PROJECT_PERIOD_FACETS
                }.items()
            )
        )
        self.assertDictEqual(expected_coeff, actual_coeff)
