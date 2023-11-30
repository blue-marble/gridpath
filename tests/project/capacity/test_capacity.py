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
]
NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity"
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


class TestCapacity(unittest.TestCase):
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

    def test_initialized_components(self):
        """
        Create components; check they are initialized with data as expected.
        Capacity-type modules should have added appropriate data;
        make sure it is all as expected.
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

        # Set: PRJ_OPR_PRDS
        # We're expecting the capacity_type modules to have added sets to be
        # joined for the final PRJ_OPR_PRDS
        # The capacity_type modules use the
        # spec_capacity_period_params.tab,
        # new_build_generator_vintage_costs.tab,
        # new_build_storage_vintage_costs.tab,
        # and new_shiftable_load_supply_curve.tab files to determine
        # operational periods, so we'll load from those files directly here
        # and compare to the set the capacity_type modules have created

        eg_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs", "spec_capacity_period_params.tab"
            ),
            usecols=["project", "period"],
            sep="\t",
        )

        eg = [tuple(x) for x in eg_df.values]

        ng_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs", "new_build_generator_vintage_costs.tab"
            ),
            usecols=["project", "vintage"],
            sep="\t",
        )
        ng = [tuple(x) for x in ng_df.values]

        ngb_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY,
                "inputs",
                "new_binary_build_generator_vintage_costs.tab",
            ),
            usecols=["project", "vintage"],
            sep="\t",
        )
        ngb = [tuple(x) for x in ngb_df.values]

        ns_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs", "new_build_storage_vintage_costs.tab"
            ),
            usecols=["project", "vintage"],
            sep="\t",
        )
        ns = [tuple(x) for x in ns_df.values]

        nsb_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY,
                "inputs",
                "new_binary_build_storage_vintage_costs.tab",
            ),
            usecols=["project", "vintage"],
            sep="\t",
        )
        nsb = [tuple(x) for x in nsb_df.values]

        fp_df = pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs", "fuel_prod_new_vintage_costs.tab"
            ),
            usecols=["project", "vintage"],
            sep="\t",
        )
        fp = [tuple(x) for x in fp_df.values]

        # Manually add shiftable DR, which is available in all periods
        dr = [("Shift_DR", 2020), ("Shift_DR", 2030)]

        expected_proj_period_set = sorted(eg + ng + ngb + ns + nsb + fp + dr)
        actual_proj_period_set = sorted(
            [(prj, period) for (prj, period) in instance.PRJ_OPR_PRDS]
        )
        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)

        # Set: OPR_PRDS_BY_PRJ
        op_per_by_proj_dict = dict()
        for proj_per in expected_proj_period_set:
            if proj_per[0] not in op_per_by_proj_dict.keys():
                op_per_by_proj_dict[proj_per[0]] = [proj_per[1]]
            else:
                op_per_by_proj_dict[proj_per[0]].append(proj_per[1])

        expected_operational_periods_by_project = OrderedDict(
            sorted(op_per_by_proj_dict.items())
        )
        actual_operational_periods_by_project = OrderedDict(
            sorted(
                {
                    prj: [period for period in instance.OPR_PRDS_BY_PRJ[prj]]
                    for prj in instance.PROJECTS
                }.items()
            )
        )
        self.assertDictEqual(
            expected_operational_periods_by_project,
            actual_operational_periods_by_project,
        )

        # Set: PRJ_OPR_TMPS
        expected_operational_timepoints_by_project = list()
        timepoints_df = pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
            sep="\t",
            usecols=["timepoint", "period"],
        )
        expected_tmp_in_p = dict()
        for tmp in timepoints_df.values:
            if tmp[1] not in expected_tmp_in_p.keys():
                expected_tmp_in_p[tmp[1]] = [tmp[0]]
            else:
                expected_tmp_in_p[tmp[1]].append(tmp[0])

        for proj in expected_operational_periods_by_project:
            for period in expected_operational_periods_by_project[proj]:
                for tmp in expected_tmp_in_p[period]:
                    expected_operational_timepoints_by_project.append((proj, tmp))

        expected_operational_timepoints_by_project = sorted(
            expected_operational_timepoints_by_project
        )
        actual_operational_timepoints_by_project = sorted(
            [(g, tmp) for (g, tmp) in instance.PRJ_OPR_TMPS]
        )
        self.assertListEqual(
            expected_operational_timepoints_by_project,
            actual_operational_timepoints_by_project,
        )

        # Set: OPR_PRJS_IN_TMP
        op_projects_by_period = dict()
        for proj in expected_operational_periods_by_project.keys():
            for period in expected_operational_periods_by_project[proj]:
                if period not in op_projects_by_period.keys():
                    op_projects_by_period[period] = [proj]
                else:
                    op_projects_by_period[period].append(proj)

        expected_operational_projects_in_tmp = dict()
        for period in op_projects_by_period:
            for tmp in expected_tmp_in_p[period]:
                expected_operational_projects_in_tmp[tmp] = op_projects_by_period[
                    period
                ]

        expected_operational_projects_in_tmp = OrderedDict(
            sorted(expected_operational_projects_in_tmp.items())
        )

        actual_operational_projects_in_tmp = OrderedDict(
            sorted(
                {
                    tmp: sorted([prj for prj in instance.OPR_PRJS_IN_TMP[tmp]])
                    for tmp in instance.TMPS
                }.items()
            )
        )
        self.assertDictEqual(
            expected_operational_projects_in_tmp, actual_operational_projects_in_tmp
        )

    def test_operational_periods_by_project_method(self):
        """
        Test operational_periods_by_project method in capacity module
        """
        project_operational_periods_set = [
            ("Nuclear", 2020),
            ("Nuclear", 2030),
            ("Battery_Specified", 2020),
        ]

        expected_nuclear_periods = [2020, 2030]
        actual_nuclear_periods = list(
            MODULE_BEING_TESTED.operational_periods_by_project(
                prj="Nuclear",
                project_operational_periods=project_operational_periods_set,
            )
        )
        self.assertListEqual(expected_nuclear_periods, actual_nuclear_periods)

        expected_battery_specified_periods = [2020]
        actual_battery_specified_periods = list(
            MODULE_BEING_TESTED.operational_periods_by_project(
                prj="Battery_Specified",
                project_operational_periods=project_operational_periods_set,
            )
        )
        self.assertListEqual(
            expected_battery_specified_periods, actual_battery_specified_periods
        )


if __name__ == "__main__":
    unittest.main()
