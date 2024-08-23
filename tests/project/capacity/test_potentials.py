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
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, add_components_and_load_data

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "project",
    "project.capacity.capacity",
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.potential"
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


class TestCapacityCosts(unittest.TestCase):
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

        projects = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "projects.tab"), delimiter="\t"
        )["project"].tolist()
        periods = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "periods.tab"), delimiter="\t"
        )["period"].tolist()

        project_periods = [(prj, prd) for prj in projects for prd in periods]

        potentials = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "new_build_potentials.tab"),
            delimiter="\t",
        ).set_index(["project", "period"])

        # Param: min_new_build_power
        expected_min_new_build_power = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["min_new_build_power"] == ".":
                    expected_min_new_build_power[prj, prd] = 0
                else:
                    expected_min_new_build_power[prj, prd] = float(
                        potentials.loc[prj, prd]["min_new_build_power"]
                    )
            else:
                expected_min_new_build_power[prj, prd] = 0

        actual_min_new_build_power = {
            (prj, prd): instance.min_new_build_power[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_min_new_build_power, actual_min_new_build_power)

        # Param: max_new_build_power
        expected_max_new_build_power = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["max_new_build_power"] == ".":
                    expected_max_new_build_power[prj, prd] = float("inf")
                else:
                    expected_max_new_build_power[prj, prd] = float(
                        potentials.loc[prj, prd]["max_new_build_power"]
                    )
            else:
                expected_max_new_build_power[prj, prd] = float("inf")

        actual_max_new_build_power = {
            (prj, prd): instance.max_new_build_power[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_max_new_build_power, actual_max_new_build_power)

        # Param: min_capacity_power
        expected_min_capacity_power = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["min_capacity_power"] == ".":
                    expected_min_capacity_power[prj, prd] = 0
                else:
                    expected_min_capacity_power[prj, prd] = float(
                        potentials.loc[prj, prd]["min_capacity_power"]
                    )
            else:
                expected_min_capacity_power[prj, prd] = 0

        actual_min_capacity_power = {
            (prj, prd): instance.min_capacity_power[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_min_capacity_power, actual_min_capacity_power)

        # Param: max_capacity_power
        expected_max_capacity_power = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["max_capacity_power"] == ".":
                    expected_max_capacity_power[prj, prd] = float("inf")
                else:
                    expected_max_capacity_power[prj, prd] = float(
                        potentials.loc[prj, prd]["max_capacity_power"]
                    )
            else:
                expected_max_capacity_power[prj, prd] = float("inf")

        actual_max_capacity_power = {
            (prj, prd): instance.max_capacity_power[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_max_capacity_power, actual_max_capacity_power)

        # Param: min_new_build_energy
        expected_min_new_build_energy = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["min_new_build_energy"] == ".":
                    expected_min_new_build_energy[prj, prd] = 0
                else:
                    expected_min_new_build_energy[prj, prd] = float(
                        potentials.loc[prj, prd]["min_new_build_energy"]
                    )
            else:
                expected_min_new_build_energy[prj, prd] = 0

        actual_min_new_build_energy = {
            (prj, prd): instance.min_new_build_energy[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_min_new_build_energy, actual_min_new_build_energy)

        # Param: max_new_build_energy
        expected_max_new_build_energy = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["max_new_build_energy"] == ".":
                    expected_max_new_build_energy[prj, prd] = float("inf")
                else:
                    expected_max_new_build_energy[prj, prd] = float(
                        potentials.loc[prj, prd]["max_new_build_energy"]
                    )
            else:
                expected_max_new_build_energy[prj, prd] = float("inf")

        actual_max_new_build_energy = {
            (prj, prd): instance.max_new_build_energy[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_max_new_build_energy, actual_max_new_build_energy)

        # Param: min_capacity_energy
        expected_min_capacity_energy = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["min_capacity_energy"] == ".":
                    expected_min_capacity_energy[prj, prd] = 0
                else:
                    expected_min_capacity_energy[prj, prd] = float(
                        potentials.loc[prj, prd]["min_capacity_energy"]
                    )
            else:
                expected_min_capacity_energy[prj, prd] = 0

        actual_min_capacity_energy = {
            (prj, prd): instance.min_capacity_energy[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_min_capacity_energy, actual_min_capacity_energy)

        # Param: max_capacity_energy
        expected_max_capacity_energy = {}
        for prj, prd in project_periods:
            if (prj, prd) in potentials.index:
                if potentials.loc[prj, prd]["max_capacity_energy"] == ".":
                    expected_max_capacity_energy[prj, prd] = float("inf")
                else:
                    expected_max_capacity_energy[prj, prd] = float(
                        potentials.loc[prj, prd]["max_capacity_energy"]
                    )
            else:
                expected_max_capacity_energy[prj, prd] = float("inf")

        actual_max_capacity_energy = {
            (prj, prd): instance.max_capacity_energy[prj, prd]
            for prj in instance.PROJECTS
            for prd in instance.PERIODS
        }

        self.assertDictEqual(expected_max_capacity_energy, actual_max_capacity_energy)


if __name__ == "__main__":
    unittest.main()
