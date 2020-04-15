#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from builtins import str
import logging
import os
import unittest

from gridpath import run_end_to_end, validate_inputs
from db import create_database, port_csvs_to_gridpath


# Change directory to 'gridpath' directory, as that's what run_scenario.py
# expects
# TODO: handle this more robustly? (e.g. db scripts expect you to be in
#  db folder and changing directions all the time is not ideal.
os.chdir(os.path.join(os.path.dirname(__file__), "..", "gridpath"))
EXAMPLES_DIRECTORY = os.path.join(os.getcwd(), "..", "examples")

# Test examples and their objective function
TEST_EXAMPLES = {
    "test": 866737242.3466034,
    "test_no_overgen_allowed": 1200069229.87995,
    "test_new_build_storage": 102420.06359999996,
    "test_new_binary_build_storage": 102487.92,
    "test_new_build_storage_cumulative_min_max": 104184.53965,
    "test_no_reserves": 53381.74655000001,
    "test_w_hydro": 49067.079900000004,
    "test_w_storage": 54334.546550000014,
    "2horizons": 1733474484.6932068,
    "2horizons_w_hydro": 100062.55,
    "2horizons_w_hydro_and_nuclear_binary_availability": 81943.32,
    "2horizons_w_hydro_w_balancing_types": 98134.16,
    "2periods": 17334744846.932064,
    "2periods_new_build": 111439176.928,
    "2periods_new_build_2zones": 222878353.856,
    "2periods_new_build_2zones_new_build_transmission": 1821806657.8548598,
    "2periods_new_build_2zones_singleBA": 222878353.857,
    "2periods_new_build_2zones_transmission": 50553647766.524,
    "2periods_new_build_2zones_transmission_w_losses": 54553647726.524,
    "2periods_new_build_2zones_transmission_w_losses_opp_dir": 54553647726.524,
    "2periods_new_build_rps": 972692908.1319999,
    "2periods_new_build_cumulative_min_max": 6296548240.926001,
    "2periods_gen_lin_econ_retirement": 17334744846.932064,
    "2periods_gen_bin_econ_retirement": 17334744846.932064,
    "test_variable_gen_reserves": 306735066.21341676,
    "2periods_new_build_rps_variable_reserves": 844029554.4855622,
    "2periods_new_build_rps_variable_reserves_subhourly_adj":
        845462123.9605286,
    "2periods_new_build_simple_prm": 198677529.596,
    "2periods_new_build_local_capacity": 114863176.928,
    "2periods_new_build_rps_w_rps_ineligible_storage": 937245877.5932124,
    "2periods_new_build_rps_w_rps_eligible_storage": 941888308.1279974,
    "test_new_solar": 866735867.6799834,
    "test_new_binary_solar": 866736353.35,
    "test_new_solar_carbon_cap": 3286733066.412322,
    "test_new_solar_carbon_cap_2zones_tx": 3180162433.1252494,
    "test_new_solar_carbon_cap_2zones_dont_count_tx": 3164472610.8364196,
    "test_tx_dcopf": 3100193282.07,
    "test_tx_simple": 3100192148.07,
    "test_ramp_up_constraints": 866737242.3466034,
    "test_ramp_up_and_down_constraints": 1080081236.67995,
    "test_startup_shutdown_rates": 768213599.01778,
    "test_no_fuels": 866666717.3333334,
    "test_variable_om_curves": 866737258.8866034,
    "test_aux_cons": 836737625.8990427,
    "single_stage_prod_cost": {"1": 866737242.3466034,
                               "2": 866737242.3466034,
                               "3": 866737242.3466034},
    "multi_stage_prod_cost": {"1": {"1": 866737242.3466433,
                                    "2": 866737242.3466433,
                                    "3": 866737242.3466433},
                              "2": {"1": 866737242.3466433,
                                    "2": 866737242.3466433,
                                    "3": 866737242.3466433},
                              "3": {"1": 866737242.3466433,
                                    "2": 866737242.3466433,
                                    "3": 866737242.3466433}},
    "multi_stage_prod_cost_w_hydro": {"1": {"1": 966735555.35,
                                            "2": 966735555.35,
                                            "3": 966735555.35},
                                      "2": {"1": 966735555.35,
                                            "2": 966735555.35,
                                            "3": 966735555.35},
                                      "3": {"1": 966735555.35,
                                            "2": 966735555.35,
                                            "3": 966735555.35}}
}


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

    def test_objective_function(self):
        """
        Check objective function for all test examples

        NOTE: the objective function for the
        2horizons_w_hydro_and_nuclear_binary_availability example is lower
        than that for the '2horizons_w_hydro' example because of the
        unrealistically high relative heat rate of the 'Nuclear' project
        relative to the gas projects; allowing binary availability for a
        must-run project actually allows lower-cost power when the nuclear
        plant is unavailable. We should probably re-think this example as
        part of a future more general revamp of the examples.
        :return:
        """
        for test in TEST_EXAMPLES.keys():
            with self.subTest(i=test):
                expected_objective = TEST_EXAMPLES[test]
                actual_objective = run_end_to_end.main(
                    ["--database", "../db/test_examples.db",
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
    def tearDownClass(cls):
        os.remove("../db/test_examples.db")


if __name__ == "__main__":
    unittest.main()
