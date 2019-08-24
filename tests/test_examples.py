#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from builtins import str
import os
import unittest

from gridpath import run_scenario

# Change directory to 'gridpath' directory, as that's what run_scenario.py
# expects
os.chdir(os.path.join(os.path.dirname(__file__), "..", "gridpath"))
EXAMPLES_DIRECTORY = os.path.join(os.getcwd(), "..", "examples")


class TestExamples(unittest.TestCase):
    """

    """
    def test_example_test(self):
        """
        Check objective function value of "test" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 866737242.3466034

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_build_storage(self):
        """
        Check objective function value of "test_new_build_storage" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_new_build_storage",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 102420.06359999996

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_build_storage_cumulative_min_max(self):
        """
        Check objective function value of
        "test_new_build_storage_cumulative_min_max" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario",
                               "test_new_build_storage_cumulative_min_max",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 104184.53965

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_no_reserves(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_no_reserves", "--quiet",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--mute_solver_output", "--testing"])

        expected_objective = 53381.74655000001

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_w_hydro(self):
        """
        Check objective function value of "test_w_hydro" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_w_hydro", "--quiet",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--mute_solver_output", "--testing"])

        expected_objective = 49067.079900000004

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_w_storage(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_w_storage", "--quiet",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--mute_solver_output", "--testing"])

        expected_objective = 54334.546550000014

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2horizons(self):
        """
        Check objective function value of "2horizons" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2horizons", "--quiet",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--mute_solver_output", "--testing"])

        expected_objective = 1733474484.6932068

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods(self):
        """
        Check objective function value of "2periods" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods", "--quiet",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--mute_solver_output", "--testing"])

        expected_objective = 17334744846.932064

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build(self):
        """
        Check objective function value of "2periods_new_build" example
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods_new_build",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 111439176.928

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones(self):
        """
        Check objective function value of "2periods_new_build_2zones" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods_new_build_2zones",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 222878353.856

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones_new_build_transmission(self
                                                                           ):
        """
        Check objective function value of
        "2periods_new_build_2zones_new_build_transmission" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_2zones_new_build_transmission",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 1821806657.8548598

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones_singleBA(self):
        """
        Check objective function value of "2periods_new_build_2zones_singleBA"
        example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_2zones_singleBA",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 222878353.857

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones_transmission(self):
        """
        Check objective function value of
        "2periods_new_build_2zones_transmission" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_2zones_transmission",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 50553647766.524

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_rps(self):
        """
        Check objective function value of "2periods_new_build_rps" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 972692908.1319999

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_cumulative_min_max(self):
        """
        Check objective function value of
        "2periods_new_build_cumulative_min_max" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario",
                               "2periods_new_build_cumulative_min_max",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 6296548240.926001

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_single_stage_prod_cost(self):
        """
        Check objective function values of "single_stage_prod_cost" example
        :return:
        """
        actual_objectives = \
            run_scenario.main(["--scenario", "single_stage_prod_cost",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: 866737242.3466034,
            2: 866737242.3466034,
            3: 866737242.3466034
        }

        for horizon in [1, 2, 3]:
            self.assertAlmostEqual(
                expected_objectives[horizon],
                actual_objectives[str(horizon)],
                places=1
            )

    def test_example_multi_stage_prod_cost(self):
        """
        Check objective function values of "multi_stage_prod_cost" example
        :return:
        """
        actual_objectives = \
            run_scenario.main(["--scenario", "multi_stage_prod_cost",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: {"da": 866737242.3466433,
                "ha": 866737242.3466433,
                "rt": 866737242.3466433},
            2: {"da": 866737242.3466433,
                "ha": 866737242.3466433,
                "rt": 866737242.3466433},
            3: {"da": 866737242.3466433,
                "ha": 866737242.3466433,
                "rt": 866737242.3466433}
        }

        for horizon in [1, 2, 3]:
            for stage in {"da", "ha", "rt"}:
                self.assertAlmostEqual(
                    expected_objectives[horizon][stage],
                    actual_objectives[str(horizon)][stage],
                    places=1
                )

    def test_example_multi_stage_prod_cost_w_hydro(self):
        """
        Check objective function values of "multi_stage_prod_cost_w_hydro"
        example
        :return:
        """
        actual_objectives = \
            run_scenario.main(["--scenario", "multi_stage_prod_cost_w_hydro",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: {"da": 966735355.3466533,
                "ha": 966735355.3466533,
                "rt": 966735355.3466533},
            2: {"da": 966735355.3466533,
                "ha": 966735355.3466533,
                "rt": 966735355.3466533},
            3: {"da": 966735355.3466533,
                "ha": 966735355.3466533,
                "rt": 966735355.3466533}
        }

        for horizon in [1, 2, 3]:
            for stage in {"da", "ha", "rt"}:
                self.assertAlmostEqual(
                    expected_objectives[horizon][stage],
                    actual_objectives[str(horizon)][stage],
                    places=1
                )

    def test_example_2periods_gen_lin_econ_retirement(self):
        """
        Check objective function value of "2periods_gen_lin_econ_retirement"
        example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_gen_lin_econ_retirement",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 17334744846.932064

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_gen_bin_econ_retirement(self):
        """
        Check objective function value of "2periods_gen_bin_econ_retirement"
        example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_gen_bin_econ_retirement",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 17334744846.932064

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_variable_gen_reserves(self):
        """
        Check objective function value of "variable_gen_reserves"
        example; this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_variable_gen_reserves",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 306735066.21341676

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_rps_variable_reserves(self):
        """
        Check objective function value of
        "2periods_new_build_rps_variable_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps_variable_reserves",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 844029554.4855622

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_rps_variable_reserves_subhourly_adj(
            self):
        """
        Check objective function value of
        "2periods_new_build_rps_variable_reserves_subhourly_adj" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps_variable_reserves_subhourly_adj",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 845462123.9605286

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_test_ramp_up_constraints(self):
        """
        Check objective function value of "test_ramp_up_constraints" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_ramp_up_constraints",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 866737242.3466034

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_ramp_up_and_down_constraints(self):
        """
        Check objective function value of "test_ramp_up_and_down_constraints"
        example; this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_ramp_up_and_down_constraints",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 1080081236.67995

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_rps_w_rps_ineligible_storage(self):
        """
        Check objective function value of
        "2periods_new_build_rps_w_rps_ineligible_storage" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps_w_rps_ineligible_storage",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 940358688.2807117

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_rps_w_rps_eligible_storage(self):
        """
        Check objective function value of
        "2periods_new_build_rps_w_rps_eligible_storage" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps_w_rps_eligible_storage",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 944988974.7999967

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_solar(self):
        """
        Check objective function value of "test_new_solar" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_new_solar",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 866736555.0133034

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_solar_carbon_cap(self):
        """
        Check objective function value of "test_new_solar_carbon_cap" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_new_solar_carbon_cap",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 3286733066.412322

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_solar_carbon_cap_2zones_tx(self):
        """
        Check objective function value of
        "test_new_solar_carbon_cap_2zones_tx" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_new_solar_carbon_cap_2zones_tx",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 3180162433.1252494

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_solar_carbon_cap_2zones_dont_count_tx(self):
        """
        Check objective function value of
        "test_new_solar_carbon_cap_2zones_dont_count_tx" example
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "test_new_solar_carbon_cap_2zones_dont_count_tx",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 3164472610.8364196

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_simple_prm(self):
        """
        Check objective function value of "2periods_new_build_simple_prm" 
        example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods_new_build_simple_prm",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 198677529.596

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_local_capacity(self):
        """
        Check objective function value of "2periods_new_build_local_capacity"
        example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario",
                               "2periods_new_build_local_capacity",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 114863176.928

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)


if __name__ == "__main__":
    unittest.main()
