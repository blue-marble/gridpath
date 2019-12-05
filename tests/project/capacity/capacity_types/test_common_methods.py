#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from importlib import import_module
import unittest


NAME_OF_MODULE_BEING_TESTED = \
    "project.capacity.capacity_types.gen_new_lin"
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='gridpath')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestCapacityTypeCommonMethods(unittest.TestCase):
    """

    """
    def test_operational_periods_by_project_vintage(self):
        """

        :return:
        """
        test_case_numbers = [1, 2, 3, 4]
        test_case_params = {
            1: ([2020, 2030, 2040, 2050], 2030, 20),  # within study period
            2: ([2020, 2030, 2040, 2050], 2040, 10),  # within study period
            3: ([2020, 2030, 2040, 2050], 2020, 40),  # all periods
            4: ([2020, 2030, 2040, 2050], 2060, 10)  # outside study period
        }
        expected_operational_periods_dict = {
            1: [2030, 2040], 2: [2040], 3: [2020, 2030, 2040, 2050],
            4: []
        }

        for test_case in test_case_numbers:
            expected_operational_periods = \
                expected_operational_periods_dict[test_case]
            actual_operational_periods = \
                MODULE_BEING_TESTED.operational_periods_by_project_vintage(
                    periods=test_case_params[test_case][0],
                    vintage=test_case_params[test_case][1],
                    lifetime=test_case_params[test_case][2]
                )
            self.assertListEqual(expected_operational_periods,
                                 actual_operational_periods)

    def test_project_operational_periods(self):
        """
        G1 has lifetime of 30 years, G2 has lifetime of 10 years,
        G3 has lifetime of 100 years
        :return:
        """
        project_vintages = [
            ("G1", 2020), ("G1", 2030), ("G1", 2040), ("G1", 2050),
            ("G2", 2030), ("G2", 2040), ("G3", 2020)
        ]
        operational_periods_by_project_vintage = {
            ("G1", 2020): [2020, 2030, 2040], ("G1", 2030): [2030, 2040, 2050],
            ("G1", 2040): [2040, 2050], ("G1", 2050): [2050],
            ("G2", 2030): [2030], ("G2", 2040): [2040],
            ("G3", 2020): [2020, 2030, 2040, 2050]
        }

        expected_project_operational_periods = sorted([
            ("G1", 2020), ("G1", 2030), ("G1", 2040), ("G1", 2050),
            ("G2", 2030), ("G2", 2040),
            ("G3", 2020), ("G3", 2030), ("G3", 2040), ("G3", 2050)
        ])

        actual_project_operational_periods = sorted(
            list(
                MODULE_BEING_TESTED.project_operational_periods(
                project_vintages_set=project_vintages,
                operational_periods_by_project_vintage_set=
                operational_periods_by_project_vintage
                )
            )
        )

        self.assertListEqual(expected_project_operational_periods,
                             actual_project_operational_periods)

    def test_project_vintages_operational_in_period(self):
        """
        G1 has lifetime of 30 years, G2 has lifetime of 10 years,
        G3 has lifetime of 100 years
        :return:
        """
        project_vintages = [
            ("G1", 2020), ("G1", 2030), ("G1", 2040), ("G1", 2050),
            ("G2", 2030), ("G2", 2040), ("G3", 2020)
        ]
        operational_periods_by_project_vintage = {
            ("G1", 2020): [2020, 2030, 2040], ("G1", 2030): [2030, 2040, 2050],
            ("G1", 2040): [2040, 2050], ("G1", 2050): [2050],
            ("G2", 2030): [2030], ("G2", 2040): [2040],
            ("G3", 2020): [2020, 2030, 2040, 2050]
        }

        expected_project_vintages_by_period = {
            2020: [("G1", 2020), ("G3", 2020)],
            2030: [("G1", 2020), ("G1", 2030), ("G2", 2030), ("G3", 2020)],
            2040: [("G1", 2020), ("G1", 2030), ("G1", 2040), ("G2", 2040),
                   ("G3", 2020)],
            2050: [("G1", 2030), ("G1", 2040), ("G1", 2050), ("G3", 2020)]
        }

        for p in [2020, 2030, 2040, 2050]:
            expected_project_vintages = \
                sorted(expected_project_vintages_by_period[p])
            actual_project_vintages = sorted(
                MODULE_BEING_TESTED.project_vintages_operational_in_period(
                    project_vintage_set=project_vintages,
                    operational_periods_by_project_vintage_set=
                    operational_periods_by_project_vintage,
                    period=p
                )
            )
            self.assertListEqual(expected_project_vintages,
                                 actual_project_vintages)


if __name__ == "__main__":
    unittest.main()
