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

        expected_objective = 65494.41333

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_new_build_storage(self):
        """
        Check objective function value of "test_new_build_storage" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_new_build_storage",
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 102384.02400

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_no_reserves(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_no_reserves", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 53362.74667

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_w_hydro(self):
        """
        Check objective function value of "test_w_hydro" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_w_hydro", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 49049.58000

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_w_storage(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "test_w_storage", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 51437.89250

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2horizons(self):
        """
        Check objective function value of "2horizons" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2horizons", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 130988.82664

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods(self):
        """
        Check objective function value of "2periods" example
        :return:
        """
        actual_objective = \
            run_scenario.main(["--scenario", "2periods", "--quiet",
                               "--scenario_location", "examples",
                               "--mute_solver_output", "--testing"])

        expected_objective = 1309888.26636

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods_new_build(self):
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

        expected_objective = 110443853.67752

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods_new_build_2zones(self):
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

        expected_objective = 220087705.75504

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods_new_build_2zones_new_build_transmission(self
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

        expected_objective = 1941106539.62229

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods_new_build_2zones_singleBA(self):
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

        expected_objective = 220044845.67373

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods_new_build_2zones_transmission(self):
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

        expected_objective = 50552825288.933334

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_example_test_2periods_new_build_rps(self):
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

        expected_objective = 972816049.42922

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=5)

    def test_single_stage_prod_cost(self):
        """
        Check objective function values of "single_stage_prod_cost" example
        :return:
        """
        actual_objectives = \
            run_scenario.main(["--scenario", "single_stage_prod_cost",
                               "--scenario_location", "examples",
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objectives = {
            1: 65494.41332,
            2: 65494.41332,
            3: 65494.41332
        }

        for horizon in [1, 2, 3]:
            self.assertAlmostEqual(
                expected_objectives[horizon],
                actual_objectives[str(horizon)],
                places=5
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
            1: {"da": 65494.41333,
                "ha": 65494.41333,
                "rt": 65494.41333},
            2: {"da": 65494.41333,
                "ha": 65494.41333,
                "rt": 65494.41333},
            3: {"da": 65494.41333,
                "ha": 65494.41333,
                "rt": 65494.41333}
        }

        for horizon in [1, 2, 3]:
            for stage in {"da", "ha", "rt"}:
                self.assertAlmostEqual(
                    expected_objectives[horizon][stage],
                    actual_objectives[str(horizon)][stage],
                    places=5
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
            1: {"da": 60554.52439,
                "ha": 60554.52439,
                "rt": 60554.52439},
            2: {"da": 60554.52439,
                "ha": 60554.52439,
                "rt": 60554.52439},
            3: {"da": 60554.52439,
                "ha": 60554.52439,
                "rt": 60554.52439}
        }

        for horizon in [1, 2, 3]:
            for stage in {"da", "ha", "rt"}:
                self.assertAlmostEqual(
                    expected_objectives[horizon][stage],
                    actual_objectives[str(horizon)][stage],
                    places=5
                )


if __name__ == "__main__":
    unittest.main()
