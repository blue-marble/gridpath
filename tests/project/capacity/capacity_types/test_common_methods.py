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


from importlib import import_module
import unittest


NAME_OF_MODULE_BEING_TESTED = "project.capacity.capacity_types.gen_new_lin"
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module(
        "." + NAME_OF_MODULE_BEING_TESTED, package="gridpath"
    )
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED + " to test.")


class TestCapacityTypeCommonMethods(unittest.TestCase):
    """ """

    def test_relevant_periods_by_project_vintage(self):
        """

        :return:
        """
        test_case_numbers = [1, 2, 3, 4]
        test_case_params = {
            # within study period
            1: (
                [2020, 2030, 2040, 2050],
                {2020: 2020, 2030: 2030, 2040: 2040, 2050: 2050},
                {2020: 2029, 2030: 2039, 2040: 2049, 2050: 2059},
                2030,
                20,
            ),
            # within study period
            2: (
                [2020, 2030, 2040, 2050],
                {2020: 2020, 2030: 2030, 2040: 2040, 2050: 2050},
                {2020: 2029, 2030: 2039, 2040: 2049, 2050: 2059},
                2040,
                10,
            ),
            # all periods
            3: (
                [2020, 2030, 2040, 2050],
                {2020: 2020, 2030: 2030, 2040: 2040, 2050: 2050},
                {2020: 2029, 2030: 2039, 2040: 2049, 2050: 2059},
                2020,
                40,
            ),
            # outside study period
            4: (
                [2020, 2030, 2040, 2050],
                {2020: 2020, 2030: 2030, 2040: 2040, 2050: 2050},
                {2020: 2029, 2030: 2039, 2040: 2049, 2050: 2059},
                2060,
                10,
            ),
            # fractional years and lifetimes
            5: (
                [1, 2, 3, 4],
                {1: 2020.0, 2: 2020.5, 3: 2021, 4: 2021.5},
                {1: 2020.49, 2: 2020.99, 3: 2021.49, 4: 2021.99},
                2020.2,
                0.75,
            ),
        }
        expected_operational_periods_dict = {
            1: [2030, 2040],
            2: [2040],
            3: [2020, 2030, 2040, 2050],
            4: [],
            5: [1, 2, 3],
        }

        for test_case in test_case_numbers:
            expected_operational_periods = expected_operational_periods_dict[test_case]
            actual_operational_periods = (
                MODULE_BEING_TESTED.relevant_periods_by_project_vintage(
                    periods=test_case_params[test_case][0],
                    period_start_year=test_case_params[test_case][1],
                    period_end_year=test_case_params[test_case][2],
                    vintage=test_case_params[test_case][3],
                    lifetime_yrs=test_case_params[test_case][4],
                )
            )
            self.assertListEqual(
                expected_operational_periods, actual_operational_periods
            )

    def test_project_relevant_periods(self):
        """
        G1 has lifetime of 30 years, G2 has lifetime of 10 years,
        G3 has lifetime of 100 years
        :return:
        """
        project_vintages = [
            ("G1", 2020),
            ("G1", 2030),
            ("G1", 2040),
            ("G1", 2050),
            ("G2", 2030),
            ("G2", 2040),
            ("G3", 2020),
        ]
        relevant_periods_by_project_vintage = {
            ("G1", 2020): [2020, 2030, 2040],
            ("G1", 2030): [2030, 2040, 2050],
            ("G1", 2040): [2040, 2050],
            ("G1", 2050): [2050],
            ("G2", 2030): [2030],
            ("G2", 2040): [2040],
            ("G3", 2020): [2020, 2030, 2040, 2050],
        }

        expected_project_relevant_periods = sorted(
            [
                ("G1", 2020),
                ("G1", 2030),
                ("G1", 2040),
                ("G1", 2050),
                ("G2", 2030),
                ("G2", 2040),
                ("G3", 2020),
                ("G3", 2030),
                ("G3", 2040),
                ("G3", 2050),
            ]
        )

        actual_project_relevant_periods = sorted(
            list(
                MODULE_BEING_TESTED.project_relevant_periods(
                    project_vintages_set=project_vintages,
                    relevant_periods_by_project_vintage_set=relevant_periods_by_project_vintage,
                )
            )
        )

        self.assertListEqual(
            expected_project_relevant_periods, actual_project_relevant_periods
        )

    def test_project_vintages_relevant_in_period(self):
        """
        G1 has lifetime of 30 years, G2 has lifetime of 10 years,
        G3 has lifetime of 100 years
        :return:
        """
        project_vintages = [
            ("G1", 2020),
            ("G1", 2030),
            ("G1", 2040),
            ("G1", 2050),
            ("G2", 2030),
            ("G2", 2040),
            ("G3", 2020),
        ]
        relevant_periods_by_project_vintage = {
            ("G1", 2020): [2020, 2030, 2040],
            ("G1", 2030): [2030, 2040, 2050],
            ("G1", 2040): [2040, 2050],
            ("G1", 2050): [2050],
            ("G2", 2030): [2030],
            ("G2", 2040): [2040],
            ("G3", 2020): [2020, 2030, 2040, 2050],
        }

        expected_project_vintages_by_period = {
            2020: [("G1", 2020), ("G3", 2020)],
            2030: [("G1", 2020), ("G1", 2030), ("G2", 2030), ("G3", 2020)],
            2040: [
                ("G1", 2020),
                ("G1", 2030),
                ("G1", 2040),
                ("G2", 2040),
                ("G3", 2020),
            ],
            2050: [("G1", 2030), ("G1", 2040), ("G1", 2050), ("G3", 2020)],
        }

        for p in [2020, 2030, 2040, 2050]:
            expected_project_vintages = sorted(expected_project_vintages_by_period[p])
            actual_project_vintages = sorted(
                MODULE_BEING_TESTED.project_vintages_relevant_in_period(
                    project_vintage_set=project_vintages,
                    relevant_periods_by_project_vintage_set=relevant_periods_by_project_vintage,
                    period=p,
                )
            )
            self.assertListEqual(expected_project_vintages, actual_project_vintages)


if __name__ == "__main__":
    unittest.main()
