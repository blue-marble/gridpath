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
    "project.capacity.capacity",
    "project.availability.availability",
    "project.fuels",
    "project.operations",
    "project.operations.operational_types",
    "project.operations.power",
]
NAME_OF_MODULE_BEING_TESTED = "project.operations.fix_commitment"
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


class TestFixCommitment(unittest.TestCase):
    """ """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=os.path.join(TEST_DATA_DIRECTORY, "subproblems"),
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="202001",
            stage="2",
        )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=os.path.join(TEST_DATA_DIRECTORY, "subproblems"),
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="202001",
            stage="2",
        )

    def test_data_loaded_correctly(self):
        """
        Test that the data loaded are as expected
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=os.path.join(TEST_DATA_DIRECTORY, "subproblems"),
            weather_iteration="",
            hydro_iteration="",
            availability_iteration="",
            subproblem="202001",
            stage="2",
        )
        instance = m.create_instance(data)

        # Set: FNL_COMMIT_PRJS
        expected_final_projects = sorted(
            [
                "Gas_CCGT",
                "Gas_CCGT_New",
                "Gas_CCGT_New_Binary",
                "Gas_CCGT_z2",
                "Disp_Binary_Commit",
                "Disp_Cont_Commit",
                "Clunky_Old_Gen",
                "Clunky_Old_Gen2",
                "Coal",
                "Coal_z2",
            ]
        )
        actual_final_projects = sorted([prj for prj in instance.FNL_COMMIT_PRJS])
        self.assertListEqual(expected_final_projects, actual_final_projects)

        # Set: FNL_COMMIT_PRJ_OPR_TMPS
        # Note: this should be getting the timepoints from the
        # scenario-horizon-stage inputs directory, not the timepoints from the
        # root scenario director (so 2030 and horizon 202002 shouldn't be here)
        expected_final_prj_op_tmps = sorted(
            [
                ("Gas_CCGT", 20200101),
                ("Gas_CCGT", 20200102),
                ("Gas_CCGT", 20200103),
                ("Gas_CCGT", 20200104),
                ("Gas_CCGT", 20200105),
                ("Gas_CCGT", 20200106),
                ("Gas_CCGT", 20200107),
                ("Gas_CCGT", 20200108),
                ("Gas_CCGT", 20200109),
                ("Gas_CCGT", 20200110),
                ("Gas_CCGT", 20200111),
                ("Gas_CCGT", 20200112),
                ("Gas_CCGT", 20200113),
                ("Gas_CCGT", 20200114),
                ("Gas_CCGT", 20200115),
                ("Gas_CCGT", 20200116),
                ("Gas_CCGT", 20200117),
                ("Gas_CCGT", 20200118),
                ("Gas_CCGT", 20200119),
                ("Gas_CCGT", 20200120),
                ("Gas_CCGT", 20200121),
                ("Gas_CCGT", 20200122),
                ("Gas_CCGT", 20200123),
                ("Gas_CCGT", 20200124),
                ("Gas_CCGT_z2", 20200101),
                ("Gas_CCGT_z2", 20200102),
                ("Gas_CCGT_z2", 20200103),
                ("Gas_CCGT_z2", 20200104),
                ("Gas_CCGT_z2", 20200105),
                ("Gas_CCGT_z2", 20200106),
                ("Gas_CCGT_z2", 20200107),
                ("Gas_CCGT_z2", 20200108),
                ("Gas_CCGT_z2", 20200109),
                ("Gas_CCGT_z2", 20200110),
                ("Gas_CCGT_z2", 20200111),
                ("Gas_CCGT_z2", 20200112),
                ("Gas_CCGT_z2", 20200113),
                ("Gas_CCGT_z2", 20200114),
                ("Gas_CCGT_z2", 20200115),
                ("Gas_CCGT_z2", 20200116),
                ("Gas_CCGT_z2", 20200117),
                ("Gas_CCGT_z2", 20200118),
                ("Gas_CCGT_z2", 20200119),
                ("Gas_CCGT_z2", 20200120),
                ("Gas_CCGT_z2", 20200121),
                ("Gas_CCGT_z2", 20200122),
                ("Gas_CCGT_z2", 20200123),
                ("Gas_CCGT_z2", 20200124),
                ("Gas_CCGT_New", 20200101),
                ("Gas_CCGT_New", 20200102),
                ("Gas_CCGT_New", 20200103),
                ("Gas_CCGT_New", 20200104),
                ("Gas_CCGT_New", 20200105),
                ("Gas_CCGT_New", 20200106),
                ("Gas_CCGT_New", 20200107),
                ("Gas_CCGT_New", 20200108),
                ("Gas_CCGT_New", 20200109),
                ("Gas_CCGT_New", 20200110),
                ("Gas_CCGT_New", 20200111),
                ("Gas_CCGT_New", 20200112),
                ("Gas_CCGT_New", 20200113),
                ("Gas_CCGT_New", 20200114),
                ("Gas_CCGT_New", 20200115),
                ("Gas_CCGT_New", 20200116),
                ("Gas_CCGT_New", 20200117),
                ("Gas_CCGT_New", 20200118),
                ("Gas_CCGT_New", 20200119),
                ("Gas_CCGT_New", 20200120),
                ("Gas_CCGT_New", 20200121),
                ("Gas_CCGT_New", 20200122),
                ("Gas_CCGT_New", 20200123),
                ("Gas_CCGT_New", 20200124),
                ("Gas_CCGT_New_Binary", 20200101),
                ("Gas_CCGT_New_Binary", 20200102),
                ("Gas_CCGT_New_Binary", 20200103),
                ("Gas_CCGT_New_Binary", 20200104),
                ("Gas_CCGT_New_Binary", 20200105),
                ("Gas_CCGT_New_Binary", 20200106),
                ("Gas_CCGT_New_Binary", 20200107),
                ("Gas_CCGT_New_Binary", 20200108),
                ("Gas_CCGT_New_Binary", 20200109),
                ("Gas_CCGT_New_Binary", 20200110),
                ("Gas_CCGT_New_Binary", 20200111),
                ("Gas_CCGT_New_Binary", 20200112),
                ("Gas_CCGT_New_Binary", 20200113),
                ("Gas_CCGT_New_Binary", 20200114),
                ("Gas_CCGT_New_Binary", 20200115),
                ("Gas_CCGT_New_Binary", 20200116),
                ("Gas_CCGT_New_Binary", 20200117),
                ("Gas_CCGT_New_Binary", 20200118),
                ("Gas_CCGT_New_Binary", 20200119),
                ("Gas_CCGT_New_Binary", 20200120),
                ("Gas_CCGT_New_Binary", 20200121),
                ("Gas_CCGT_New_Binary", 20200122),
                ("Gas_CCGT_New_Binary", 20200123),
                ("Gas_CCGT_New_Binary", 20200124),
                ("Disp_Binary_Commit", 20200101),
                ("Disp_Binary_Commit", 20200102),
                ("Disp_Binary_Commit", 20200103),
                ("Disp_Binary_Commit", 20200104),
                ("Disp_Binary_Commit", 20200105),
                ("Disp_Binary_Commit", 20200106),
                ("Disp_Binary_Commit", 20200107),
                ("Disp_Binary_Commit", 20200108),
                ("Disp_Binary_Commit", 20200109),
                ("Disp_Binary_Commit", 20200110),
                ("Disp_Binary_Commit", 20200111),
                ("Disp_Binary_Commit", 20200112),
                ("Disp_Binary_Commit", 20200113),
                ("Disp_Binary_Commit", 20200114),
                ("Disp_Binary_Commit", 20200115),
                ("Disp_Binary_Commit", 20200116),
                ("Disp_Binary_Commit", 20200117),
                ("Disp_Binary_Commit", 20200118),
                ("Disp_Binary_Commit", 20200119),
                ("Disp_Binary_Commit", 20200120),
                ("Disp_Binary_Commit", 20200121),
                ("Disp_Binary_Commit", 20200122),
                ("Disp_Binary_Commit", 20200123),
                ("Disp_Binary_Commit", 20200124),
                ("Disp_Cont_Commit", 20200101),
                ("Disp_Cont_Commit", 20200102),
                ("Disp_Cont_Commit", 20200103),
                ("Disp_Cont_Commit", 20200104),
                ("Disp_Cont_Commit", 20200105),
                ("Disp_Cont_Commit", 20200106),
                ("Disp_Cont_Commit", 20200107),
                ("Disp_Cont_Commit", 20200108),
                ("Disp_Cont_Commit", 20200109),
                ("Disp_Cont_Commit", 20200110),
                ("Disp_Cont_Commit", 20200111),
                ("Disp_Cont_Commit", 20200112),
                ("Disp_Cont_Commit", 20200113),
                ("Disp_Cont_Commit", 20200114),
                ("Disp_Cont_Commit", 20200115),
                ("Disp_Cont_Commit", 20200116),
                ("Disp_Cont_Commit", 20200117),
                ("Disp_Cont_Commit", 20200118),
                ("Disp_Cont_Commit", 20200119),
                ("Disp_Cont_Commit", 20200120),
                ("Disp_Cont_Commit", 20200121),
                ("Disp_Cont_Commit", 20200122),
                ("Disp_Cont_Commit", 20200123),
                ("Disp_Cont_Commit", 20200124),
                ("Clunky_Old_Gen", 20200101),
                ("Clunky_Old_Gen", 20200102),
                ("Clunky_Old_Gen", 20200103),
                ("Clunky_Old_Gen", 20200104),
                ("Clunky_Old_Gen", 20200105),
                ("Clunky_Old_Gen", 20200106),
                ("Clunky_Old_Gen", 20200107),
                ("Clunky_Old_Gen", 20200108),
                ("Clunky_Old_Gen", 20200109),
                ("Clunky_Old_Gen", 20200110),
                ("Clunky_Old_Gen", 20200111),
                ("Clunky_Old_Gen", 20200112),
                ("Clunky_Old_Gen", 20200113),
                ("Clunky_Old_Gen", 20200114),
                ("Clunky_Old_Gen", 20200115),
                ("Clunky_Old_Gen", 20200116),
                ("Clunky_Old_Gen", 20200117),
                ("Clunky_Old_Gen", 20200118),
                ("Clunky_Old_Gen", 20200119),
                ("Clunky_Old_Gen", 20200120),
                ("Clunky_Old_Gen", 20200121),
                ("Clunky_Old_Gen", 20200122),
                ("Clunky_Old_Gen", 20200123),
                ("Clunky_Old_Gen", 20200124),
                ("Clunky_Old_Gen2", 20200101),
                ("Clunky_Old_Gen2", 20200102),
                ("Clunky_Old_Gen2", 20200103),
                ("Clunky_Old_Gen2", 20200104),
                ("Clunky_Old_Gen2", 20200105),
                ("Clunky_Old_Gen2", 20200106),
                ("Clunky_Old_Gen2", 20200107),
                ("Clunky_Old_Gen2", 20200108),
                ("Clunky_Old_Gen2", 20200109),
                ("Clunky_Old_Gen2", 20200110),
                ("Clunky_Old_Gen2", 20200111),
                ("Clunky_Old_Gen2", 20200112),
                ("Clunky_Old_Gen2", 20200113),
                ("Clunky_Old_Gen2", 20200114),
                ("Clunky_Old_Gen2", 20200115),
                ("Clunky_Old_Gen2", 20200116),
                ("Clunky_Old_Gen2", 20200117),
                ("Clunky_Old_Gen2", 20200118),
                ("Clunky_Old_Gen2", 20200119),
                ("Clunky_Old_Gen2", 20200120),
                ("Clunky_Old_Gen2", 20200121),
                ("Clunky_Old_Gen2", 20200122),
                ("Clunky_Old_Gen2", 20200123),
                ("Clunky_Old_Gen2", 20200124),
                ("Coal", 20200101),
                ("Coal", 20200102),
                ("Coal", 20200103),
                ("Coal", 20200104),
                ("Coal", 20200105),
                ("Coal", 20200106),
                ("Coal", 20200107),
                ("Coal", 20200108),
                ("Coal", 20200109),
                ("Coal", 20200110),
                ("Coal", 20200111),
                ("Coal", 20200112),
                ("Coal", 20200113),
                ("Coal", 20200114),
                ("Coal", 20200115),
                ("Coal", 20200116),
                ("Coal", 20200117),
                ("Coal", 20200118),
                ("Coal", 20200119),
                ("Coal", 20200120),
                ("Coal", 20200121),
                ("Coal", 20200122),
                ("Coal", 20200123),
                ("Coal", 20200124),
                ("Coal_z2", 20200101),
                ("Coal_z2", 20200102),
                ("Coal_z2", 20200103),
                ("Coal_z2", 20200104),
                ("Coal_z2", 20200105),
                ("Coal_z2", 20200106),
                ("Coal_z2", 20200107),
                ("Coal_z2", 20200108),
                ("Coal_z2", 20200109),
                ("Coal_z2", 20200110),
                ("Coal_z2", 20200111),
                ("Coal_z2", 20200112),
                ("Coal_z2", 20200113),
                ("Coal_z2", 20200114),
                ("Coal_z2", 20200115),
                ("Coal_z2", 20200116),
                ("Coal_z2", 20200117),
                ("Coal_z2", 20200118),
                ("Coal_z2", 20200119),
                ("Coal_z2", 20200120),
                ("Coal_z2", 20200121),
                ("Coal_z2", 20200122),
                ("Coal_z2", 20200123),
                ("Coal_z2", 20200124),
            ]
        )
        actual_final_prj_op_tmps = sorted(
            [(prj, tmp) for (prj, tmp) in instance.FNL_COMMIT_PRJ_OPR_TMPS]
        )
        self.assertListEqual(expected_final_prj_op_tmps, actual_final_prj_op_tmps)

        # Set: FXD_COMMIT_PRJS
        expected_fixed_projects = sorted(["Coal", "Coal_z2"])
        actual_fixed_projects = sorted([prj for prj in instance.FXD_COMMIT_PRJS])
        self.assertListEqual(expected_fixed_projects, actual_fixed_projects)

        # Set: FXD_COMMIT_PRJ_OPR_TMPS
        expected_fixed_prj_op_tmps = sorted(
            [
                ("Coal", 20200101),
                ("Coal", 20200102),
                ("Coal", 20200103),
                ("Coal", 20200104),
                ("Coal", 20200105),
                ("Coal", 20200106),
                ("Coal", 20200107),
                ("Coal", 20200108),
                ("Coal", 20200109),
                ("Coal", 20200110),
                ("Coal", 20200111),
                ("Coal", 20200112),
                ("Coal", 20200113),
                ("Coal", 20200114),
                ("Coal", 20200115),
                ("Coal", 20200116),
                ("Coal", 20200117),
                ("Coal", 20200118),
                ("Coal", 20200119),
                ("Coal", 20200120),
                ("Coal", 20200121),
                ("Coal", 20200122),
                ("Coal", 20200123),
                ("Coal", 20200124),
                ("Coal_z2", 20200101),
                ("Coal_z2", 20200102),
                ("Coal_z2", 20200103),
                ("Coal_z2", 20200104),
                ("Coal_z2", 20200105),
                ("Coal_z2", 20200106),
                ("Coal_z2", 20200107),
                ("Coal_z2", 20200108),
                ("Coal_z2", 20200109),
                ("Coal_z2", 20200110),
                ("Coal_z2", 20200111),
                ("Coal_z2", 20200112),
                ("Coal_z2", 20200113),
                ("Coal_z2", 20200114),
                ("Coal_z2", 20200115),
                ("Coal_z2", 20200116),
                ("Coal_z2", 20200117),
                ("Coal_z2", 20200118),
                ("Coal_z2", 20200119),
                ("Coal_z2", 20200120),
                ("Coal_z2", 20200121),
                ("Coal_z2", 20200122),
                ("Coal_z2", 20200123),
                ("Coal_z2", 20200124),
            ]
        )
        actual_fixed_prj_op_tmps = sorted(
            [(prj, tmp) for (prj, tmp) in instance.FXD_COMMIT_PRJ_OPR_TMPS]
        )
        self.assertListEqual(expected_fixed_prj_op_tmps, actual_fixed_prj_op_tmps)

        # Param: fixed_commitment
        expected_fixed_commitment = OrderedDict(
            sorted(
                {
                    ("Coal", 20200101): 4,
                    ("Coal", 20200102): 6,
                    ("Coal", 20200103): 6,
                    ("Coal", 20200104): 6,
                    ("Coal", 20200105): 6,
                    ("Coal", 20200106): 6,
                    ("Coal", 20200107): 6,
                    ("Coal", 20200108): 6,
                    ("Coal", 20200109): 6,
                    ("Coal", 20200110): 6,
                    ("Coal", 20200111): 6,
                    ("Coal", 20200112): 6,
                    ("Coal", 20200113): 6,
                    ("Coal", 20200114): 6,
                    ("Coal", 20200115): 6,
                    ("Coal", 20200116): 6,
                    ("Coal", 20200117): 6,
                    ("Coal", 20200118): 6,
                    ("Coal", 20200119): 6,
                    ("Coal", 20200120): 6,
                    ("Coal", 20200121): 6,
                    ("Coal", 20200122): 6,
                    ("Coal", 20200123): 6,
                    ("Coal", 20200124): 6,
                    ("Coal_z2", 20200101): 6,
                    ("Coal_z2", 20200102): 6,
                    ("Coal_z2", 20200103): 6,
                    ("Coal_z2", 20200104): 6,
                    ("Coal_z2", 20200105): 6,
                    ("Coal_z2", 20200106): 6,
                    ("Coal_z2", 20200107): 6,
                    ("Coal_z2", 20200108): 6,
                    ("Coal_z2", 20200109): 6,
                    ("Coal_z2", 20200110): 6,
                    ("Coal_z2", 20200111): 6,
                    ("Coal_z2", 20200112): 6,
                    ("Coal_z2", 20200113): 6,
                    ("Coal_z2", 20200114): 6,
                    ("Coal_z2", 20200115): 6,
                    ("Coal_z2", 20200116): 6,
                    ("Coal_z2", 20200117): 6,
                    ("Coal_z2", 20200118): 6,
                    ("Coal_z2", 20200119): 6,
                    ("Coal_z2", 20200120): 6,
                    ("Coal_z2", 20200121): 6,
                    ("Coal_z2", 20200122): 6,
                    ("Coal_z2", 20200123): 6,
                    ("Coal_z2", 20200124): 6,
                }.items()
            )
        )
        actual_fixed_commitment = OrderedDict(
            sorted(
                {
                    (prj, tmp): instance.fixed_commitment[prj, tmp]
                    for (prj, tmp) in instance.FXD_COMMIT_PRJ_OPR_TMPS
                }.items()
            )
        )
        self.assertDictEqual(expected_fixed_commitment, actual_fixed_commitment)


if __name__ == "__main__":
    unittest.main()
