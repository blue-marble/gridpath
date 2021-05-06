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
    "temporal.investment.periods", "geography.load_zones", "project"]
NAME_OF_MODULE_BEING_TESTED = \
    "project.capacity.capacity_types.new_lin"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='gridpath')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestCapacityTypeNewLin(unittest.TestCase):
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

        # Set: NEW_LIN
        expected_new_lin_project_set = sorted([
            "Gas_CCGT_New", "Gas_CT_New", "Battery"
        ])
        actual_new_lin_project_set = sorted(
            [prj for prj in instance.NEW_LIN]
        )
        self.assertListEqual(expected_new_lin_project_set,
                             actual_new_lin_project_set)

        # Set: NEW_LIN_VNTS
        expected_storage_vintage_set = sorted([
            ("Gas_CCGT_New", 2020),
            ("Gas_CCGT_New", 2030),
            ("Gas_CT_New", 2030),
            ("Battery", 2020),
            ("Battery", 2030)
        ])
        actual_storage_vintage_set = sorted(
            [(prj, period)
             for (prj, period) in instance.NEW_LIN_VNTS
             ]
        )
        self.assertListEqual(expected_storage_vintage_set,
                             actual_storage_vintage_set)

        # Params: new_lin_lifetime_yrs
        expected_lifetime = OrderedDict(
            sorted(
                {("Gas_CCGT_New", 2020): 30,
                 ("Gas_CCGT_New", 2030): 30,
                 ("Gas_CT_New", 2030): 30,
                 ("Battery", 2020): 10,
                 ("Battery", 2030): 10}.items())
        )
        actual_lifetime = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_lin_lifetime_yrs[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_LIN_VNTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_lifetime, actual_lifetime)

        # Params: new_lin_annualized_real_cost_per_mw_yr
        expected_mw_yr_cost = OrderedDict(
            sorted(
                {("Gas_CCGT_New", 2020): 200000,
                 ("Gas_CCGT_New", 2030): 180000,
                 ("Gas_CT_New", 2030): 140000,
                 ("Battery", 2020): 1,
                 ("Battery", 2030): 1}.items())
        )
        actual_mw_yr_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_lin_annualized_real_cost_per_mw_yr[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_LIN_VNTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_mw_yr_cost, actual_mw_yr_cost)

        # Params: new_lin_annualized_real_cost_per_mwh_yr
        expected_mwh_yr_cost = OrderedDict(
            sorted(
                {("Gas_CCGT_New", 2020): float("inf"),
                 ("Gas_CCGT_New", 2030): float("inf"),
                 ("Gas_CT_New", 2030): float("inf"),
                 ("Battery", 2020): 1,
                 ("Battery", 2030): 1}.items())
        )
        actual_mwh_yr_cost = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_lin_annualized_real_cost_per_mwh_yr[
                        prj, vintage]
                 for (prj, vintage) in instance.NEW_LIN_VNTS
                 }.items()
            )
        )
        self.assertDictEqual(expected_mwh_yr_cost, actual_mwh_yr_cost)

        # Set: NEW_LIN_VNTS_W_MIN_CAPACITY_CONSTRAINT
        expected_storage_vintage_min_capacity_set = sorted([
            ("Gas_CT_New", 2030), ("Battery", 2030)
        ])
        actual_storage_vintage_min_capacity_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_LIN_VNTS_W_MIN_CAPACITY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_min_capacity_set,
                             actual_storage_vintage_min_capacity_set)

        # Params: new_lin_min_cumulative_new_build_mw
        expected_min_capacity = OrderedDict(
            sorted({("Gas_CT_New", 2030): 10, ("Battery", 2030): 7}.items())
        )
        actual_min_capacity = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_lin_min_cumulative_new_build_mw[
                        prj, vintage]
                 for (prj, vintage) in
                 instance.
                 NEW_LIN_VNTS_W_MIN_CAPACITY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_capacity, actual_min_capacity)
        
        # Set: NEW_LIN_VNTS_W_MIN_ENERGY_CONSTRAINT
        expected_storage_vintage_min_energy_set = sorted([
            ("Battery", 2030)
        ])
        actual_storage_vintage_min_energy_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_LIN_VNTS_W_MIN_ENERGY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_min_energy_set,
                             actual_storage_vintage_min_energy_set)

        # Params: new_lin_min_cumulative_new_build_mw
        expected_min_energy = OrderedDict(
            sorted({("Battery", 2030): 10}.items())
        )
        actual_min_energy = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_lin_min_cumulative_new_build_mwh[
                        prj, vintage]
                 for (prj, vintage) in
                 instance.
                 NEW_LIN_VNTS_W_MIN_ENERGY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_min_energy, actual_min_energy)

        # Set: NEW_LIN_VNTS_W_MAX_CAPACITY_CONSTRAINT
        expected_storage_vintage_max_capacity_set = sorted([
            ("Battery", 2020), ('Gas_CCGT_New', 2020), ('Gas_CCGT_New', 2030)
        ])
        actual_storage_vintage_max_capacity_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_LIN_VNTS_W_MAX_CAPACITY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_max_capacity_set,
                             actual_storage_vintage_max_capacity_set)

        # Params: new_lin_max_cumulative_new_build_mw
        expected_max_capacity = OrderedDict(
            sorted({
                       ("Gas_CCGT_New", 2020): 20,
                       ("Gas_CCGT_New", 2030): 20,
                       ("Battery", 2020): 6
                   }.items())
        )
        actual_max_capacity = OrderedDict(
            sorted(
                {(prj, vintage):
                     instance.new_lin_max_cumulative_new_build_mw[
                         prj, vintage]
                 for (prj, vintage) in
                 instance.
                     NEW_LIN_VNTS_W_MAX_CAPACITY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_capacity, actual_max_capacity)

        # Set: NEW_LIN_VNTS_W_MAX_ENERGY_CONSTRAINT
        expected_storage_vintage_max_energy_set = sorted([
            ("Battery", 2020)
        ])
        actual_storage_vintage_max_energy_set = sorted(
            [(prj, period)
             for (prj, period) in
             instance.NEW_LIN_VNTS_W_MAX_ENERGY_CONSTRAINT
             ]
        )
        self.assertListEqual(expected_storage_vintage_max_energy_set,
                             actual_storage_vintage_max_energy_set)

        # Params: new_lin_max_cumulative_new_build_mw
        expected_max_energy = OrderedDict(
            sorted({("Battery", 2020): 7}.items())
        )
        actual_max_energy = OrderedDict(
            sorted(
                {(prj, vintage):
                    instance.new_lin_max_cumulative_new_build_mwh[
                         prj, vintage]
                 for (prj, vintage) in
                 instance.NEW_LIN_VNTS_W_MAX_ENERGY_CONSTRAINT
                 }.items()
            )
        )
        self.assertDictEqual(expected_max_energy, actual_max_energy)

        # Param: new_lin_min_duration_hrs
        expected_min_duration = OrderedDict(
            [('Battery', 1.0), ('Gas_CCGT_New', 0), ('Gas_CT_New', 0)]
        )
        actual_min_duration = OrderedDict(
            sorted(
                {prj: instance.new_lin_min_duration_hrs[prj]
                 for prj in instance.NEW_LIN}.items()
            )
        )
        self.assertDictEqual(expected_min_duration, actual_min_duration)

        # Param: new_lin_max_duration_hrs
        expected_max_duration = OrderedDict(
            [('Battery', 99.0),
             ('Gas_CCGT_New', float("inf")),
             ('Gas_CT_New', float("inf"))]
        )
        actual_max_duration = OrderedDict(
            sorted(
                {prj: instance.new_lin_max_duration_hrs[prj]
                 for prj in instance.NEW_LIN}.items()
            )
        )
        self.assertDictEqual(expected_max_duration, actual_max_duration)

    def test_derived_data(self):
        """
        Calculations
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

        # Sets: OPR_PRDS_BY_NEW_LIN_VINTAGE
        expected_op_periods_by_vintage = {
            ('Gas_CCGT_New', 2020): [2020, 2030],
            ('Gas_CCGT_New', 2030): [2030],
            ('Gas_CT_New', 2030): [2030],
            ("Battery", 2020): [2020],
            ("Battery", 2030): [2030]
        }
        actual_periods_by_vintage = {
            (prj, vintage):
                [period for period in
                 instance.OPR_PRDS_BY_NEW_LIN_VINTAGE[
                    prj, vintage]]
            for (prj, vintage) in
                instance.OPR_PRDS_BY_NEW_LIN_VINTAGE
        }
        self.assertDictEqual(expected_op_periods_by_vintage,
                             actual_periods_by_vintage)

        # Sets: NEW_LIN_OPR_PRDS
        expected_op_periods = sorted([
            ("Gas_CCGT_New", 2020),
            ("Gas_CCGT_New", 2030),
            ("Gas_CT_New", 2030),
            ("Battery", 2020),
            ("Battery", 2030)
        ])
        actual_op_periods = sorted([
            (prj, period) for (prj, period) in
            instance.NEW_LIN_OPR_PRDS
        ])
        self.assertListEqual(expected_op_periods, actual_op_periods)

        # Sets: NEW_LIN_VNTS_OPR_IN_PRD
        expected_vintage_op_in_period = {
            2020: [("Gas_CCGT_New", 2020), ("Battery", 2020)],
            2030: [("Gas_CCGT_New", 2020),
                   ("Gas_CCGT_New", 2030),
                   ("Gas_CT_New", 2030),
                   ("Battery", 2030)]
        }
        actual_vintage_op_in_period = {
            p: [(g, v) for (g, v) in
                instance.NEW_LIN_VNTS_OPR_IN_PRD[p]
                ] for p in instance.PERIODS
        }
        self.assertDictEqual(expected_vintage_op_in_period,
                             actual_vintage_op_in_period)


if __name__ == "__main__":
    unittest.main()
