#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from collections import OrderedDict
from importlib import import_module
import os.path
import pandas as pd
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.operations.horizons",
    "temporal.investment.periods", "geography.load_zones", "project"]
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
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package="gridpath")
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestCapacity(unittest.TestCase):
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
            subproblem="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: PROJECT_OPERATIONAL_PERIODS
        # We're expecting the capacity_type modules to have added sets to be
        # joined for the final PROJECT_OPERATIONAL_PERIODS
        # The capacity_type modules use the
        # specified_generation_period_params.tab,
        # new_build_generator_vintage_costs.tab,
        # storage_specified_capacities.tab,
        # new_build_storage_vintage_costs.tab,
        # and new_shiftable_load_supply_curve.tab files to determine
        # operational periods, so we'll load from those files directly here
        # and compare to the set the capacity_type modules have created

        eg_df = \
            pd.read_csv(
                os.path.join(
                    TEST_DATA_DIRECTORY, "inputs",
                    "specified_generation_period_params.tab"
                ),
                usecols=['project', 'period'],
                sep="\t"
            )

        eg = [tuple(x) for x in eg_df.values]

        ng_df = \
            pd.read_csv(
                os.path.join(
                    TEST_DATA_DIRECTORY, "inputs",
                    "new_build_generator_vintage_costs.tab"
                ),
                usecols=['project', 'vintage'],
                sep="\t"
            )
        ng = [tuple(x) for x in ng_df.values]

        ngb_df = \
            pd.read_csv(
                os.path.join(
                    TEST_DATA_DIRECTORY, "inputs",
                    "new_binary_build_generator_vintage_costs.tab"
                ),
                usecols=['project', 'vintage'],
                sep="\t"
            )
        ngb = [tuple(x) for x in ngb_df.values]

        es_df = \
            pd.read_csv(
                os.path.join(
                    TEST_DATA_DIRECTORY, "inputs",
                    "storage_specified_capacities.tab"
                ),
                usecols=['project', 'period'],
                sep="\t"
            )
        es = [tuple(x) for x in es_df.values]

        ns_df = \
            pd.read_csv(
                os.path.join(
                    TEST_DATA_DIRECTORY, "inputs",
                    "new_build_storage_vintage_costs.tab"
                ),
                usecols=['project', 'vintage'],
                sep="\t"
            )
        ns = [tuple(x) for x in ns_df.values]

        nsb_df = \
            pd.read_csv(
                os.path.join(
                    TEST_DATA_DIRECTORY, "inputs",
                    "new_binary_build_storage_vintage_costs.tab"
                ),
                usecols=['project', 'vintage'],
                sep="\t"
            )
        nsb = [tuple(x) for x in nsb_df.values]

        # Manually add shiftable DR, which is available in all periods
        dr = [("Shift_DR", 2020), ("Shift_DR", 2030)]

        expected_proj_period_set = sorted(eg + ng + ngb + es + ns + nsb + dr)
        actual_proj_period_set = sorted([
            (prj, period) for (prj, period)
            in instance.PROJECT_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_proj_period_set, actual_proj_period_set)

        # Set: STORAGE_OPERATIONAL_PERIODS
        expected_storage_proj_period_set = sorted(es + ns + nsb + dr)
        actual_storage_proj_period_set = sorted([
            (prj, period) for (prj, period)
            in instance.STORAGE_OPERATIONAL_PERIODS
        ])
        self.assertListEqual(expected_storage_proj_period_set,
                             actual_storage_proj_period_set)

        # Set: OPERATIONAL_PERIODS_BY_PROJECT
        op_per_by_proj_dict = dict()
        for proj_per in expected_proj_period_set:
            if proj_per[0] not in op_per_by_proj_dict.keys():
                op_per_by_proj_dict[proj_per[0]] = [proj_per[1]]
            else:
                op_per_by_proj_dict[proj_per[0]].append(proj_per[1])

        expected_operational_periods_by_project = OrderedDict(
            sorted(
                op_per_by_proj_dict.items()
            )
        )
        actual_operational_periods_by_project = OrderedDict(
            sorted(
                {prj: [period for period in
                       instance.OPERATIONAL_PERIODS_BY_PROJECT[prj]
                       ] for prj in instance.PROJECTS}.items()
            )
        )
        self.assertDictEqual(expected_operational_periods_by_project,
                             actual_operational_periods_by_project)

        # Set: PROJECT_OPERATIONAL_TIMEPOINTS
        expected_operational_timepoints_by_project = list()
        timepoints_df = \
            pd.read_csv(
                os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
                sep="\t", usecols=['timepoint', 'period']
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
                    expected_operational_timepoints_by_project.append(
                        (proj, tmp)
                    )

        expected_operational_timepoints_by_project = sorted(
            expected_operational_timepoints_by_project
        )
        actual_operational_timepoints_by_project = sorted([
            (g, tmp) for (g, tmp) in instance.PROJECT_OPERATIONAL_TIMEPOINTS
        ])
        self.assertListEqual(expected_operational_timepoints_by_project,
                             actual_operational_timepoints_by_project)

        # Set: OPERATIONAL_PROJECTS_IN_TIMEPOINT
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
                expected_operational_projects_in_tmp[tmp] = \
                    op_projects_by_period[period]

        expected_operational_projects_in_tmp = OrderedDict(
            sorted(
                expected_operational_projects_in_tmp.items()
            )
        )

        actual_operational_projects_in_tmp = OrderedDict(sorted({
            tmp: sorted([prj for prj
                         in instance.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp]])
            for tmp in instance.TMPS
        }.items()
                                                                )
                                                         )
        self.assertDictEqual(expected_operational_projects_in_tmp,
                             actual_operational_projects_in_tmp)

    def test_operational_periods_by_project_method(self):
        """
        Test operational_periods_by_project method in capacity module
        """
        project_operational_periods_set = [
            ("Nuclear", 2020), ("Nuclear", 2030),
            ("Battery_Specified", 2020)
        ]

        expected_nuclear_periods = [2020, 2030]
        actual_nuclear_periods = \
            list(MODULE_BEING_TESTED.operational_periods_by_project(
                prj="Nuclear",
                project_operational_periods=project_operational_periods_set)
            )
        self.assertListEqual(expected_nuclear_periods, actual_nuclear_periods)

        expected_battery_specified_periods = [2020]
        actual_battery_specified_periods = \
            list(MODULE_BEING_TESTED.operational_periods_by_project(
                prj="Battery_Specified",
                project_operational_periods=project_operational_periods_set)
            )
        self.assertListEqual(expected_battery_specified_periods,
                             actual_battery_specified_periods)


if __name__ == "__main__":
    unittest.main()
