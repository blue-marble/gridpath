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

TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints",
    "temporal.operations.horizons",
    "temporal.investment.periods",
    "geography.load_zones",
    "project",
    "project.capacity",
    "project.capacity.capacity_types",
    "project.capacity.capacity",
    "project.capacity.costs",
]
NAME_OF_MODULE_BEING_TESTED = "system.policy.subsidies"
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


class TestSubsidies(unittest.TestCase):
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
            subproblem="",
            stage="",
        )
        instance = m.create_instance(data)

        # Set: PRJ_VNTS_FIN_IN_PERIOD
        expected_prj_v_fin_in_prd = {
            2020: sorted([("Battery", 2020), ("Gas_CCGT_New", 2020)]),
            2030: sorted(
                [("Gas_CCGT_New", 2030), ("Gas_CT_New", 2030), ("Battery", 2020)]
            ),
        }
        actual_prj_v_fin_in_prd = {
            p: sorted(list(instance.PRJ_VNTS_FIN_IN_PERIOD[p].data()))
            for p in instance.PERIODS
        }
        self.assertDictEqual(expected_prj_v_fin_in_prd, actual_prj_v_fin_in_prd)

        # Set: PROGRAM_PERIODS
        expectd_prg_prd = sorted([("ITC", 2020)])
        actual_prg_prd = sorted([(prg, prd) for (prg, prd) in instance.PROGRAM_PERIODS])
        self.assertListEqual(expectd_prg_prd, actual_prg_prd)

        # Param: program_budget
        expected_budget = OrderedDict(
            sorted(
                {
                    ("ITC", 2020): 1000,
                }.items()
            )
        )
        actual_budget = OrderedDict(
            sorted(
                {
                    (prg, prd): instance.program_budget[prg, prd]
                    for (prg, prd) in instance.PROGRAM_PERIODS
                }.items()
            )
        )
        self.assertDictEqual(expected_budget, actual_budget)

        # Set: PROGRAMS
        expectd_prg = sorted([("ITC")])
        actual_prg = sorted([prg for prg in instance.PROGRAMS])
        self.assertListEqual(expectd_prg, actual_prg)

        # Set: PROGRAM_PROJECT_VINTAGES
        expected_prg_prj_v = sorted([("ITC", "Battery", 2020)])
        actual_prg_prj_v = sorted(
            [(prg, prj, prd) for (prg, prj, prd) in instance.PROGRAM_PROJECT_VINTAGES]
        )
        self.assertListEqual(expected_prg_prj_v, actual_prg_prj_v)

        # Set: PROGRAM_ELIGIBLE_PROJECTS
        expected_eligible_prj = sorted([("Battery")])
        actual_eligible_prj = sorted(
            [prj for prj in instance.PROGRAM_ELIGIBLE_PROJECTS]
        )
        self.assertListEqual(expected_eligible_prj, actual_eligible_prj)

        # Set:PROGRAM_VINTAGES_BY_PROJECT
        expected_prg_v_by_prj = OrderedDict(
            sorted(
                {
                    "Battery": ("ITC", 2020),
                }.items()
            )
        )
        # Exclude projects with empty set
        actual_prg_v_by_prj = {}
        for prj in instance.PROJECTS:
            if instance.PROGRAM_VINTAGES_BY_PROJECT[prj].data() != ():
                actual_prg_v_by_prj[prj] = instance.PROGRAM_VINTAGES_BY_PROJECT[
                    prj
                ].data()[0]
        self.assertDictEqual(expected_prg_v_by_prj, actual_prg_v_by_prj)

        # Set:PROJECT_VINTAGES_BY_PROGRAM
        expected_prj_v_by_prg = OrderedDict(
            sorted(
                {
                    "ITC": ("Battery", 2020),
                }.items()
            )
        )
        # Exclude projects with empty set
        actual_prj_v_by_prg = {}
        for prg in instance.PROGRAMS:
            actual_prj_v_by_prg[prg] = instance.PROJECT_VINTAGES_BY_PROGRAM[prg].data()[
                0
            ]
        self.assertDictEqual(expected_prj_v_by_prg, actual_prj_v_by_prg)

        # Param: annual_payment_subsidy
        expected_subsidy = OrderedDict(
            sorted(
                {
                    ("ITC", "Battery", 2020): 20,
                }.items()
            )
        )
        actual_subsidy = OrderedDict(
            sorted(
                {
                    (prg, prj, v): instance.annual_payment_subsidy[prg, prj, v]
                    for (prg, prj, v) in instance.PROGRAM_PROJECT_VINTAGES
                }.items()
            )
        )
        self.assertDictEqual(expected_subsidy, actual_subsidy)


if __name__ == "__main__":
    unittest.main()
