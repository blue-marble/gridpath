#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import logging
import os
import sqlite3
import unittest

from gridpath import run_end_to_end, validate_inputs
from db import create_database, port_csvs_to_gridpath
from db.common_functions import connect_to_database


# Change directory to 'gridpath' directory, as that's what run_scenario.py
# expects
# TODO: handle this more robustly? (e.g. db scripts expect you to be in
#  db folder and changing directions all the time is not ideal.
os.chdir(os.path.join(os.path.dirname(__file__), "..", "gridpath"))
EXAMPLES_DIRECTORY = os.path.join("..", "examples")
DB_PATH = os.path.join("..", "db", "test_examples.db")


class TestExamples(unittest.TestCase):
    """

    """

    def assertDictAlmostEqual(self, d1, d2, msg=None, places=7):

        # check if both inputs are dicts
        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')

        # check if both inputs have the same keys
        self.assertEqual(d1.keys(), d2.keys())

        # check each key
        for key, value in d1.items():
            if isinstance(value, dict):
                self.assertDictAlmostEqual(d1[key], d2[key], places=places, msg=msg)
            else:
                self.assertAlmostEqual(d1[key], d2[key], places=places, msg=msg)

    def check_validation(self, test):
        """
        Check that validate inputs runs without errors, and that there
        are no validation issues recorded in the status_validation table
        :return:
        """

        # Check that test validation runs without errors
        validate_inputs.main(
            ["--database", DB_PATH,
             "--scenario", test,
             "--quiet"]
        )

        # Check that no validation issues are recorded in the db for the test
        expected_validations = []

        conn = connect_to_database(db_path=DB_PATH,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        validations = c.execute(
            """
            SELECT scenario_name FROM status_validation
            INNER JOIN
            (SELECT scenario_id, scenario_name FROM scenarios)
            USING (scenario_id)
            WHERE scenario_name = '{}'
            """.format(test)
        )
        actual_validations = validations.fetchall()

        self.assertListEqual(expected_validations, actual_validations)

    def run_and_check_objective(self, test, expected_objective):
        """

        :param test: str, name of the test example
        :param expected_objective: float or dict, expected objective
        :return:
        """

        actual_objective = run_end_to_end.main(
            ["--database", DB_PATH,
             "--scenario", test,
             "--scenario_location", EXAMPLES_DIRECTORY,
             "--quiet",
             "--mute_solver_output",
             "--testing"]
        )

        # Multi-subproblem and/or multi-stage scenarios return dict
        if isinstance(expected_objective, dict):
            self.assertDictAlmostEqual(
                expected_objective, actual_objective, places=1
            )
        # Otherwise, objective is a single value
        else:
            self.assertAlmostEqual(
                expected_objective, actual_objective, places=1
            )

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
        Check validation and objective function value of "test" example
        :return:
        """

        self.check_validation("test")
        self.run_and_check_objective("test", 866737242.3466034)

    def test_example_test_no_overgen_allowed(self):
        """
        Check validation and objective function value of
        "test_no_overgen_allowed" example
        :return:
        """

        self.check_validation("test_no_overgen_allowed")
        self.run_and_check_objective("test_no_overgen_allowed",
                                     1200069229.87995)

    def test_example_test_new_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_build_storage" example
        :return:
        """

        self.check_validation("test_new_build_storage")
        self.run_and_check_objective("test_new_build_storage",
                                     102420.06359999996)

    def test_example_test_new_binary_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_binary_build_storage" example
        :return:
        """

        self.check_validation("test_new_binary_build_storage")
        self.run_and_check_objective("test_new_binary_build_storage",
                                     102487.92)

    def test_example_test_new_build_storage_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "test_new_build_storage_cumulative_min_max" example
        :return:
        """

        self.check_validation("test_new_build_storage_cumulative_min_max")
        self.run_and_check_objective("test_new_build_storage_cumulative_min_max",
                                     104184.53965)

    def test_example_test_no_reserves(self):
        """
        Check validation and objective function value of
        "test_no_reserves" example
        :return:
        """

        self.check_validation("test_no_reserves")
        self.run_and_check_objective("test_no_reserves", 53381.74655000001)

    def test_example_test_w_hydro(self):
        """
        Check validation and objective function value of "test_w_hydro" example
        :return:
        """

        self.check_validation("test_w_hydro")
        self.run_and_check_objective("test_w_hydro", 49067.079900000004)

    def test_example_test_w_storage(self):
        """
        Check validation and objective function value of "test_w_storage" example
        :return:
        """

        self.check_validation("test_w_storage")
        self.run_and_check_objective("test_w_storage", 54334.546550000014)

    def test_example_2horizons(self):
        """
        Check validation and objective function value of "2horizons" example
        :return:
        """

        self.check_validation("2horizons")
        self.run_and_check_objective("2horizons", 1733474484.6932068)

    def test_example_2horizons_w_hydro(self):
        """
        Check validation and objective function value of
        "2horizons_w_hydro" example
        :return:
        """

        self.check_validation("2horizons_w_hydro")
        self.run_and_check_objective("2horizons_w_hydro", 100062.55)

    def test_example_2horizons_w_hydro_and_nuclear_binary_availability(self):
        """
        Check validation and objective function value of
        "2horizons_w_hydro_and_nuclear_binary_availability" example

        NOTE: the objective function for this example is lower than that for
        the '2horizons_w_hydro' example because of the unrealistically high
        relative heat rate of the 'Nuclear' project relative to the gas
        projects; allowing binary availability for a must-run project
        actually allows lower-cost power when the nuclear plant is
        unavailable. We should probably re-think this example as part of a
        future more general revamp of the examples.

        :return:
        """

        self.check_validation("2horizons_w_hydro_and_nuclear_binary_availability")
        self.run_and_check_objective(
            "2horizons_w_hydro_and_nuclear_binary_availability",
            81943.32
        )

    def test_example_2horizons_w_hydro_w_balancing_types(self):
        """
        Check validation and objective function value of
        "2horizons_w_hydro_w_balancing_types" example. The objective
        function of this example should be lower than that of the
        '2horizons_w_hydro' example, as the average hydro budget is the
        same across all timepoints, but the hydro balancing horizon is now
        longer.
        :return:
        """

        self.check_validation("2horizons_w_hydro_w_balancing_types")
        self.run_and_check_objective("2horizons_w_hydro_w_balancing_types",
                                     98134.16)

    def test_example_2periods(self):
        """
        Check validation and objective function value of "2periods" example
        :return:
        """

        self.check_validation("2periods")
        self.run_and_check_objective("2periods", 17334744846.932064)

    def test_example_2periods_new_build(self):
        """
        Check validation and objective function value of "2periods_new_build" example
        """

        self.check_validation("2periods_new_build")
        self.run_and_check_objective("2periods_new_build", 111439176.928)

    def test_example_2periods_new_build_2zones(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones")
        self.run_and_check_objective("2periods_new_build_2zones",
                                     222878353.856)

    def test_example_2periods_new_build_2zones_new_build_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_new_build_transmission" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_new_build_transmission")
        self.run_and_check_objective(
            "2periods_new_build_2zones_new_build_transmission",
            1821806657.8548598
        )

    def test_example_2periods_new_build_2zones_singleBA(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_singleBA"
        example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_singleBA")
        self.run_and_check_objective("2periods_new_build_2zones_singleBA",
                                     222878353.857)

    def test_example_2periods_new_build_2zones_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_transmission")
        self.run_and_check_objective("2periods_new_build_2zones_transmission",
                                     50553647766.524)

    def test_example_2periods_new_build_2zones_transmission_w_losses(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_transmission_w_losses")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_w_losses",
            54553647726.524
        )

    def test_example_2periods_new_build_2zones_transmission_w_losses_opp_dir(
            self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses_opp_dir" example

        Note: this should be the same as the objective function for
        2periods_new_build_2zones_transmission_w_losses
        :return:
        """

        self.check_validation("2periods_new_build_2zones_transmission_w_losses_opp_dir")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_w_losses_opp_dir",
            54553647726.524
        )

    def test_example_2periods_new_build_rps(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps" example
        :return:
        """

        self.check_validation("2periods_new_build_rps")
        self.run_and_check_objective("2periods_new_build_rps",
                                     972692908.1319999)

    def test_example_2periods_new_build_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "2periods_new_build_cumulative_min_max" example
        :return:
        """

        self.check_validation("2periods_new_build_cumulative_min_max")
        self.run_and_check_objective("2periods_new_build_cumulative_min_max",
                                     6296548240.926001)

    def test_example_single_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost" example
        :return:
        """

        self.check_validation("single_stage_prod_cost")
        self.run_and_check_objective("single_stage_prod_cost",
                                     {"1": 866737242.3466034,
                                      "2": 866737242.3466034,
                                      "3": 866737242.3466034})

    def test_example_single_stage_prod_cost_linked_subproblems(self):
        """
        Check objective function values of
        "single_stage_prod_cost_linked_subproblems" example
        :return:
        """
        self.check_validation("single_stage_prod_cost_linked_subproblems")
        self.run_and_check_objective(
            "single_stage_prod_cost_linked_subproblems",
            {
                "1": 866737242.3466034,
                "2": 866737242.3466034,
                "3": 866737242.3466034
            }
        )

    def test_example_multi_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost" example
        :return:
        """

        self.check_validation("multi_stage_prod_cost")
        self.run_and_check_objective("multi_stage_prod_cost",
                                     {"1": {"1": 866737242.3466433,
                                            "2": 866737242.3466433,
                                            "3": 866737242.3466433},
                                      "2": {"1": 866737242.3466433,
                                            "2": 866737242.3466433,
                                            "3": 866737242.3466433},
                                      "3": {"1": 866737242.3466433,
                                            "2": 866737242.3466433,
                                            "3": 866737242.3466433}})

    def test_example_multi_stage_prod_cost_w_hydro(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_w_hydro"
        example
        :return:
        """

        self.check_validation("multi_stage_prod_cost_w_hydro")
        self.run_and_check_objective("multi_stage_prod_cost_w_hydro",
                                     {"1": {"1": 966735555.35,
                                            "2": 966735555.35,
                                            "3": 966735555.35},
                                      "2": {"1": 966735555.35,
                                            "2": 966735555.35,
                                            "3": 966735555.35},
                                      "3": {"1": 966735555.35,
                                            "2": 966735555.35,
                                            "3": 966735555.35}})

    def test_example_multi_stage_prod_cost_linked_subproblems(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_linked_subproblems" example
        :return:
        """
        self.check_validation("multi_stage_prod_cost_linked_subproblems")
        self.run_and_check_objective(
            "multi_stage_prod_cost_linked_subproblems",
            {
                "1": {
                    "1": 866737242.3466034,
                    "2": 866737242.3466034,
                    "3": 866737241.3466034
                },
                "2": {
                    "1": 866737242.3466034,
                    "2": 866737242.3466034,
                    "3": 866737241.3466034
                },
                "3": {
                    "1": 866737242.3466034,
                    "2": 866737242.3466034,
                    "3": 866737241.3466034
                }
            }
        )

    def test_example_2periods_gen_lin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_lin_econ_retirement"
        example
        :return:
        """

        self.check_validation("2periods_gen_lin_econ_retirement")
        self.run_and_check_objective("2periods_gen_lin_econ_retirement",
                                     17334744846.932064)

    def test_example_2periods_gen_bin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_bin_econ_retirement"
        example
        :return:
        """

        self.check_validation("2periods_gen_bin_econ_retirement")
        self.run_and_check_objective("2periods_gen_bin_econ_retirement",
                                     17334744846.932064)

    def test_example_variable_gen_reserves(self):
        """
        Check validation and objective function value of
        "variable_gen_reserves"
        example; this example requires a non-linear solver
        :return:
        """

        self.check_validation("test_variable_gen_reserves")
        self.run_and_check_objective("test_variable_gen_reserves",
                                     306735066.21341676)

    def test_example_2periods_new_build_rps_variable_reserves(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_variable_reserves")
        self.run_and_check_objective("2periods_new_build_rps_variable_reserves",
                                     844029554.4855622)

    def test_example_2periods_new_build_rps_variable_reserves_subhourly_adj(
            self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves_subhourly_adj" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_variable_reserves_subhourly_adj")
        self.run_and_check_objective(
            "2periods_new_build_rps_variable_reserves_subhourly_adj",
            845462123.9605286
        )

    def test_example_test_ramp_up_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_constraints" example
        :return:
        """

        self.check_validation("test_ramp_up_constraints")
        self.run_and_check_objective("test_ramp_up_constraints",
                                     866737242.3466034)

    def test_example_test_ramp_up_and_down_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_and_down_constraints"
        example;
        :return:
        """

        self.check_validation("test_ramp_up_and_down_constraints")
        self.run_and_check_objective("test_ramp_up_and_down_constraints",
                                     1080081236.67995)

    def test_example_2periods_new_build_rps_w_rps_ineligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_ineligible_storage" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_w_rps_ineligible_storage")
        self.run_and_check_objective(
            "2periods_new_build_rps_w_rps_ineligible_storage",
            937245877.5932124
        )

    def test_example_2periods_new_build_rps_w_rps_eligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_eligible_storage" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_w_rps_eligible_storage")
        self.run_and_check_objective(
            "2periods_new_build_rps_w_rps_eligible_storage",
            941888308.1279974
        )

    def test_example_test_new_solar(self):
        """
        Check validation and objective function value of
        "test_new_solar" example
        :return:
        """

        self.check_validation("test_new_solar")
        self.run_and_check_objective("test_new_solar", 866735867.6799834)

    def test_example_test_new_binary_solar(self):
        """
        Check validation and objective function value of
        "test_new_binary_solar" example
        :return:
        """

        self.check_validation("test_new_binary_solar")
        self.run_and_check_objective("test_new_binary_solar", 866736353.35)

    def test_example_test_new_solar_carbon_cap(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap")
        self.run_and_check_objective("test_new_solar_carbon_cap",
                                     3286733066.412322)

    def test_example_test_new_solar_carbon_cap_2zones_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_tx" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_tx")
        self.run_and_check_objective("test_new_solar_carbon_cap_2zones_tx",
                                     3180162433.1252494)

    def test_example_test_new_solar_carbon_cap_2zones_dont_count_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_dont_count_tx" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_dont_count_tx")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_dont_count_tx",
            3164472610.8364196
        )

    def test_example_2periods_new_build_simple_prm(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """

        self.check_validation("2periods_new_build_simple_prm")
        self.run_and_check_objective("2periods_new_build_simple_prm",
                                     198677529.596)

    def test_example_2periods_new_build_local_capacity(self):
        """
        Check validation and objective function value of
        "2periods_new_build_local_capacity"
        example
        :return:
        """

        self.check_validation("2periods_new_build_local_capacity")
        self.run_and_check_objective("2periods_new_build_local_capacity",
                                     114863176.928)

    def test_example_test_tx_dcopf(self):
        """
        Check validation and objective function value of
        "test_tx_dcopf" example
        :return:
        """

        self.check_validation("test_tx_dcopf")
        self.run_and_check_objective("test_tx_dcopf", 3100193282.07)

    def test_example_test_tx_simple(self):
        """
        Check validation and objective function value of
        "test_tx_simple" example
        :return:
        """

        self.check_validation("test_tx_simple")
        self.run_and_check_objective("test_tx_simple", 3100192148.07)

    def test_example_test_startup_shutdown_rates(self):
        """
        Check validation and objective function value of
        "test_startup_shutdown_rates"
        example
        :return:
        """

        self.check_validation("test_startup_shutdown_rates")
        self.run_and_check_objective("test_startup_shutdown_rates",
                                     768213599.01778)

    def test_no_fuels(self):
        """
        Check validation and objective function value of "test_no_fuels"
        example
        :return:
        """

        self.check_validation("test_no_fuels")
        self.run_and_check_objective("test_no_fuels", 866666717.3333334)

    def test_variable_om_curves(self):
        """
        Check validation and objective function value of
        "test_variable_om_curves"
        example
        :return:
        """

        self.check_validation("test_variable_om_curves")
        self.run_and_check_objective("test_variable_om_curves",
                                     866737258.8866034)

    def test_aux_cons(self):
        """
        Check validation and objective function value of
        "test_aux_cons" example

        Note: the objective function value is lower than that for the "test"
        example because the auxiliary consumption results in less
        overgeneration and therefore lower overgeneration penalty.
        """

        self.check_validation("test_aux_cons")
        self.run_and_check_objective("test_aux_cons", 836737625.8990427)

    @classmethod
    def tearDownClass(cls):
        os.remove("../db/test_examples.db")


if __name__ == "__main__":
    unittest.main()
