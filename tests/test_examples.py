#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from builtins import str
import os
import unittest

import run_scenario

# Change directory to base directory, as that"s what run_scenario.py expects
os.chdir(os.path.join(os.path.dirname(__file__), ".."))


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
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 65508.41333333334

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_build_storage(self):
        """
        Check objective function value of "test_new_build_storage" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_new_build_storage",
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 102420.064

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
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 104166.4775

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_no_reserves(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_no_reserves", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 53381.74666666667

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_w_hydro(self):
        """
        Check objective function value of "test_w_hydro" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_w_hydro", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 49067.08

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_w_storage(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_w_storage", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 53987.69666666667

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2horizons(self):
        """
        Check objective function value of "2horizons" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2horizons", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 131016.826635704

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods(self):
        """
        Check objective function value of "2periods" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 1310168.26635704

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build(self):
        """
        Check objective function value of "2periods_new_build" example;
        this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods_new_build",
                               "--scenario_location", "examples",
                               "--solver", "ipopt", "--quiet",
                               "--mute_solver_output", "--testing"])

        expected_objective = 110444138.79915327

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones(self):
        """
        Check objective function value of "2periods_new_build_2zones" example;
        this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods_new_build_2zones",
                               "--scenario_location", "examples",
                               "--solver", "ipopt", "--quiet",
                               "--mute_solver_output", "--testing"])

        expected_objective = 220088275.99830943

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 1820978464.266668

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones_singleBA(self):
        """
        Check objective function value of "2periods_new_build_2zones_singleBA"
        example; this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_2zones_singleBA",
                 "--scenario_location", "examples",
                 "--solver", "ipopt", "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 220045418.77450955

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 50552825588.933334

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_rps(self):
        """
        Check objective function value of "2periods_new_build_rps" example;
        this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps",
                 "--scenario_location", "examples",
                 "--solver", "ipopt", "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 972816224.0247171

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_cumulative_min_max(self):
        """
        Check objective function value of
        "2periods_new_build_cumulative_min_max" example;
        this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario",
                               "2periods_new_build_cumulative_min_max",
                               "--scenario_location", "examples",
                               "--solver", "ipopt", "--quiet",
                               "--mute_solver_output", "--testing"])

        expected_objective = 6295817592.20153

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_single_stage_prod_cost(self):
        """
        Check objective function values of "single_stage_prod_cost" example
        :return:
        """
        actual_objectives = \
            run_scenario.main(["--scenario", "single_stage_prod_cost",
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: 65508.413317852006,
            2: 65508.413317852006,
            3: 65508.413317852006
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
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: {"da": 65508.41333333334,
                "ha": 65508.41333333334,
                "rt": 65508.41333333334},
            2: {"da": 65508.41333333334,
                "ha": 65508.41333333334,
                "rt": 65508.41333333334},
            3: {"da": 65508.41333333334,
                "ha": 65508.41333333334,
                "rt": 65508.41333333334}
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
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: {"da": 60564.524391700004,
                "ha": 60564.524391700004,
                "rt": 60564.524391700004},
            2: {"da": 60564.524391700004,
                "ha": 60564.524391700004,
                "rt": 60564.524391700004},
            3: {"da": 60564.524391700004,
                "ha": 60564.524391700004,
                "rt": 60564.524391700004}
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
                 "--scenario_location", "examples",
                 "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 1276478.9355708

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
                 "--scenario_location", "examples",
                 "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 1310168.26635704

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
                 "--scenario_location", "examples",
                 "--solver", "ipopt", "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 64754.81343815058

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_rps_variable_reserves(self):
        """
        Check objective function value of
        "2periods_new_build_rps_variable_reserves" example; this example
        requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps_variable_reserves",
                 "--scenario_location", "examples",
                 "--solver", "ipopt", "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 844035709.4169273

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_rps_variable_reserves_subhourly_adj(
            self):
        """
        Check objective function value of
        "2periods_new_build_rps_variable_reserves_subhourly_adj" example;
        this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(
                ["--scenario",
                 "2periods_new_build_rps_variable_reserves_subhourly_adj",
                 "--scenario_location", "examples",
                 "--solver", "ipopt", "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 845532009.8435436

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
                 "--scenario_location", "examples",
                 "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 68097.61333333333

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
                 "--scenario_location", "examples",
                 "--quiet",
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 80071278.98

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 940371813.224

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 945001614.7954971

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 62139.69105836666

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 271066545.5944095

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 159168652.34777576

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
                 "--scenario_location", "examples",
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 142694332.4445429

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_simple_prm(self):
        """
        Check objective function value of "2periods_new_build_simple_prm" 
        example; this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods_new_build_simple_prm",
                               "--scenario_location", "examples",
                               "--solver", "ipopt", "--quiet",
                               "--mute_solver_output", "--testing"])

        expected_objective = 197078051.08634624

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_local_capacity(self):
        """
        Check objective function value of "2periods_new_build_local_capacity"
        example; this example requires a non-linear solver
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario",
                               "2periods_new_build_local_capacity",
                               "--scenario_location", "examples",
                               "--solver", "ipopt", "--quiet",
                               "--mute_solver_output", "--testing"])

        expected_objective = 113868138.8006254

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)


if __name__ == "__main__":
    unittest.main()
