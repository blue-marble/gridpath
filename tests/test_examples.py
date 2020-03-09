#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from builtins import str
import logging
import os
import unittest

from gridpath import run_end_to_end
from db import create_database, port_csvs_to_gridpath


# Change directory to 'gridpath' directory, as that's what run_scenario.py
# expects
# TODO: handle this more robustly? (e.g. db scripts expect you to be in
#  db folder and changing directions all the time is not ideal.
os.chdir(os.path.join(os.path.dirname(__file__), "..", "gridpath"))
EXAMPLES_DIRECTORY = os.path.join(os.getcwd(), "..", "examples")


class TestExamples(unittest.TestCase):
    """

    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the testing database
        :return:
        """

        test_db_path = os.path.join(os.getcwd(),
                                    "..", "db", "test_examples.db")

        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        create_database.main(["--db_location", "../db",
                              "--db_name", "test_examples"])

        try:
            port_csvs_to_gridpath.main(["--db_location", "../db/",
                                        "--db_name", "test_examples",
                                        "--csv_location",
                                        "../db/csvs_test_examples",
                                        "--quiet"])
        except Exception as e:
            print("Error encountered during population of testing database "
                  "test_examples.db. Deleting database ...")
            logging.exception(e)
            os.remove(test_db_path)

        # TODO: create in memory instead and pass around connection?

        # self.conn = sqlite3.connect(":memory:")
        # self.conn.execute("PRAGMA journal_mode=WAL")
        # create_database.create_database_schema(
        #     db=self.conn,
        #     parsed_arguments=["--db_schema", "db_schema.sql"]
        # )
        # create_database.load_data(db=self.conn, omit_data=False)
        # port_csvs_to_gridpath.load_csv_data(
        #     conn=self.conn,
        #     csv_path="../db/csvs_test_examples"
        # )

    def test_example_test(self):
        """
        Check objective function value of "test" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 866737242.3466034

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_no_overgen_allowed(self):
        """
        Check objective function value of "test_no_overgen_allowed" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_no_overgen_allowed",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 1200069229.87995

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_build_storage(self):
        """
        Check objective function value of "test_new_build_storage" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_new_build_storage",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 102420.06359999996

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_binary_build_storage(self):
        """
        Check objective function value of "test_new_binary_build_storage"
        example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_new_binary_build_storage",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 102487.92

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_build_storage_cumulative_min_max(self):
        """
        Check objective function value of
        "test_new_build_storage_cumulative_min_max" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario",
                                 "test_new_build_storage_cumulative_min_max",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 104184.53965

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_no_reserves(self):
        """
        Check objective function value of "test_no_reserves" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_no_reserves", "--quiet",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_w_hydro", "--quiet",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_w_storage", "--quiet",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "2horizons", "--quiet",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--mute_solver_output", "--testing"])

        expected_objective = 1733474484.6932068

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2horizons_w_hydro(self):
        """
        Check objective function value of "2horizons_w_hydro" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "2horizons_w_hydro", "--quiet",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--mute_solver_output", "--testing"])

        expected_objective = 100062.55

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2horizons_w_hydro_and_nuclear_binary_availability(self):
        """
        Check objective function value of
        "2horizons_w_hydro_and_nuclear_binary_availability" example
        :return:

        NOTE: the objective function for this example is lower than that for
        the '2horizons_w_hydro' example because of the unrealistically high
        relative heat rate of the 'Nuclear' project relative to the gas
        projects; allowing binary availability for a must-run project
        actually allows lower-cost power when the nuclear plant is
        unavailable. We should probably re-think this example as part of a
        future more general revamp of the examples.
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
                 "2horizons_w_hydro_and_nuclear_binary_availability",
                 "--quiet", "--scenario_location", EXAMPLES_DIRECTORY,
                 "--mute_solver_output", "--testing"]
            )

        expected_objective = 81943.32

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2horizons_w_hydro_w_balancing_types(self):
        """
        Check objective function value of
        "2horizons_w_hydro_w_balancing_types" example. The objective
        function of this example should be lower than that of the
        '2horizons_w_hydro' example, as the average hydro budget is the
        same across all timepoints, but the hydro balancing horizon is now
        longer.
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario",
                                 "2horizons_w_hydro_w_balancing_types",
                                 "--quiet",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--mute_solver_output", "--testing"])

        expected_objective = 98134.16

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods(self):
        """
        Check objective function value of "2periods" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "2periods", "--quiet",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "2periods_new_build",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 111439176.928

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_2periods_new_build_2zones(self):
        """
        Check objective function value of "2periods_new_build_2zones" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "2periods_new_build_2zones",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_new_build_2zones_singleBA",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_new_build_2zones_transmission",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 50553647766.524

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_2zones_transmission_w_losses(self):
        """
        Check objective function value of
        "2periods_new_build_2zones_transmission_w_losses" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
                 "2periods_new_build_2zones_transmission_w_losses",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 54553647726.524

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_2zones_transmission_w_losses_opp_dir(
            self):
        """
        Check objective function value of
        "2periods_new_build_2zones_transmission_w_losses_opp_dir" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
                 "2periods_new_build_2zones_transmission_w_losses_opp_dir",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        # Note: this should be the same as the objective function for
        # 2periods_new_build_2zones_transmission_w_losses
        expected_objective = 54553647726.524

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_2periods_new_build_rps(self):
        """
        Check objective function value of "2periods_new_build_rps" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_new_build_rps",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario",
                                 "2periods_new_build_cumulative_min_max",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objective = 6296548240.926001

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_single_stage_prod_cost(self):
        """
        Check objective function values of "single_stage_prod_cost" example
        :return:
        """
        actual_objectives = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "single_stage_prod_cost",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "multi_stage_prod_cost",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objectives = {
            1: {1: 866737242.3466433,
                2: 866737242.3466433,
                3: 866737242.3466433},
            2: {1: 866737242.3466433,
                2: 866737242.3466433,
                3: 866737242.3466433},
            3: {1: 866737242.3466433,
                2: 866737242.3466433,
                3: 866737242.3466433}
        }

        for horizon in [1, 2, 3]:
            for stage in {1, 2, 3}:
                self.assertAlmostEqual(
                    expected_objectives[horizon][stage],
                    actual_objectives[str(horizon)][str(stage)],
                    places=1
                )

    def test_example_multi_stage_prod_cost_w_hydro(self):
        """
        Check objective function values of "multi_stage_prod_cost_w_hydro"
        example
        :return:
        """
        actual_objectives = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "multi_stage_prod_cost_w_hydro",
                                 "--scenario_location", EXAMPLES_DIRECTORY,
                                 "--quiet", "--mute_solver_output",
                                 "--testing"])

        expected_objectives = {
            1: {1: 966735555.35,
                2: 966735555.35,
                3: 966735555.35},
            2: {1: 966735555.35,
                2: 966735555.35,
                3: 966735555.35},
            3: {1: 966735555.35,
                2: 966735555.35,
                3: 966735555.35}
        }

        for horizon in [1, 2, 3]:
            for stage in {1, 2, 3}:
                self.assertAlmostEqual(
                    expected_objectives[horizon][stage],
                    actual_objectives[str(horizon)][str(stage)],
                    places=1
                )

    def test_example_2periods_gen_lin_econ_retirement(self):
        """
        Check objective function value of "2periods_gen_lin_econ_retirement"
        example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_gen_lin_econ_retirement",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_gen_bin_econ_retirement",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_variable_gen_reserves",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_new_build_rps_variable_reserves",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_ramp_up_constraints",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_ramp_up_and_down_constraints",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "2periods_new_build_rps_w_rps_eligible_storage",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_new_solar",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 866735867.6799834

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_binary_solar(self):
        """
        Check objective function value of "test_new_binary_solar" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_new_binary_solar",
                 "--scenario_location", EXAMPLES_DIRECTORY,
                 "--quiet", "--mute_solver_output", "--testing"]
            )

        expected_objective = 866736353.35

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=1)

    def test_example_test_new_solar_carbon_cap(self):
        """
        Check objective function value of "test_new_solar_carbon_cap" example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_new_solar_carbon_cap",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario", "test_new_solar_carbon_cap_2zones_tx",
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
            run_end_to_end.main(
                ["--database", "../db/test_examples.db",
                 "--scenario",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "2periods_new_build_simple_prm",
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
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario",
                                 "2periods_new_build_local_capacity",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 114863176.928

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_test_tx_dcopf(self):
        """
        Check objective function value of "test_tx_dcopf"
        example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_tx_dcopf",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 3100193282.07

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_test_tx_simple(self):
        """
        Check objective function value of "test_tx_simple"
        example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_tx_simple",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 3100192148.07

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    def test_example_test_startup_shutdown_rates(self):
        """
        Check objective function value of "test_startup_shutdown_rates"
        example
        :return:
        """
        actual_objective = \
            run_end_to_end.main(["--database", "../db/test_examples.db",
                                 "--scenario", "test_startup_shutdown_rates",
                               "--scenario_location", EXAMPLES_DIRECTORY,
                               "--quiet", "--mute_solver_output", "--testing"])

        expected_objective = 1280325998.36

        self.assertAlmostEqual(expected_objective, actual_objective,
                               places=0)

    @classmethod
    def tearDownClass(cls):
        os.remove("../db/test_examples.db")


if __name__ == "__main__":
    unittest.main()
