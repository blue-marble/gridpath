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

import logging
import multiprocessing
import os
import platform
import sqlite3
import unittest

from gridpath import run_end_to_end, validate_inputs
from db import create_database
from db.common_functions import connect_to_database
from db.utilities import port_csvs_to_db, scenario


# Change directory to 'gridpath' directory, as that's what run_scenario.py
# expects; the rest of the global variables are relative paths from there
os.chdir(os.path.join(os.path.dirname(__file__), "..", "gridpath"))
EXAMPLES_DIRECTORY = os.path.join("..", "examples")
DB_NAME = "unittest_examples"
DB_PATH = os.path.join("../db", "{}.db".format(DB_NAME))
CSV_PATH = "../db//csvs_test_examples"
SCENARIOS_CSV = os.path.join(CSV_PATH, "scenarios.csv")


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

    def run_and_check_objective(self, test, expected_objective, parallel=1):
        """

        :param test: str, name of the test example
        :param expected_objective: float or dict, expected objective
        :param parallel: int, set to a number > 1 to test
            parallelization functionality
        :return:
        """

        actual_objective = run_end_to_end.main(
            ["--database", DB_PATH,
             "--scenario", test,
             "--scenario_location", EXAMPLES_DIRECTORY,
             # "--log",
             # "--write_solver_files_to_logs_dir",
             # "--keepfiles",
             # "--symbolic",
             "--n_parallel_get_inputs", str(parallel),
             "--n_parallel_solve", str(parallel),
             "--quiet",
             "--mute_solver_output",
             "--testing"]
        )

        # Check if we have a multiprocessing manager
        # If so, convert the manager proxy dictionary to to a simple dictionary
        # to avoid errors
        # Done via copies to avoid broken pipe error
        if hasattr(multiprocessing, "managers"):
            if isinstance(actual_objective,
                          multiprocessing.managers.DictProxy):
                # Make a dictionary from a copy of the objective
                actual_objective_copy = dict(actual_objective.copy())
                for subproblem in actual_objective.keys():
                    # If we have stages, make a dictionary form a copy of the
                    # stage dictionary for each subproblem
                    if isinstance(actual_objective[subproblem],
                                  multiprocessing.managers.DictProxy):
                        stage_dict_copy = dict(
                            actual_objective_copy[subproblem].copy()
                        )
                        # Reset the stage dictionary to the new simple
                        # dictionary object
                        actual_objective_copy[subproblem] = stage_dict_copy
                # Reset the objective to the new dictionary object
                actual_objective = actual_objective_copy

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

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

        create_database.main(["--database", DB_PATH])

        try:
            port_csvs_to_db.main([
                "--database", DB_PATH,
                "--csv_location", CSV_PATH,
                "--quiet"
            ])
        except Exception as e:
            print("Error encountered during population of testing database "
                  "{}.db. Deleting database ...".format(DB_NAME))
            logging.exception(e)
            os.remove(DB_PATH)

        try:
            scenario.main([
                "--database", DB_PATH,
                "--csv_path", SCENARIOS_CSV,
                "--quiet"
            ])
        except Exception as e:
            print("Error encountered during population of testing database "
                  "{}.db. Deleting database ...".format(DB_NAME))
            logging.exception(e)
            os.remove(DB_PATH)

    def test_example_test(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """

        self.check_validation("test")
        self.run_and_check_objective("test", -3796309121478.12)

    def test_example_test_no_overgen_allowed(self):
        """
        Check validation and objective function value of
        "test_no_overgen_allowed" example
        :return:
        """

        self.check_validation("test_no_overgen_allowed")
        self.run_and_check_objective("test_no_overgen_allowed",
                                     -5256303226874.182)

    def test_example_test_new_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_build_storage" example
        :return:
        """

        self.check_validation("test_new_build_storage")
        self.run_and_check_objective("test_new_build_storage",
                                     -4484591199.92)

    def test_example_test_new_binary_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_binary_build_storage" example
        :return:
        """

        self.check_validation("test_new_binary_build_storage")
        self.run_and_check_objective("test_new_binary_build_storage",
                                     -4484591878.4800005)

    def test_example_test_new_build_storage_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "test_new_build_storage_cumulative_min_max" example
        :return:
        """

        self.check_validation("test_new_build_storage_cumulative_min_max")
        self.run_and_check_objective("test_new_build_storage_cumulative_min_max",
                                     -4561692383.87)

    def test_example_test_no_reserves(self):
        """
        Check validation and objective function value of
        "test_no_reserves" example
        :return:
        """

        self.check_validation("test_no_reserves")
        self.run_and_check_objective("test_no_reserves", -233812049.889)

    def test_example_test_w_hydro(self):
        """
        Check validation and objective function value of "test_w_hydro" example
        :return:
        """

        self.check_validation("test_w_hydro")
        self.run_and_check_objective("test_w_hydro", -214913823.36742803)

    def test_example_test_w_storage(self):
        """
        Check validation and objective function value of "test_w_storage" example
        :return:
        """

        self.check_validation("test_w_storage")
        self.run_and_check_objective("test_w_storage", -237985313.88900003)

    def test_example_2horizons(self):
        """
        Check validation and objective function value of "2horizons" example
        :return:
        """

        self.check_validation("2horizons")
        self.run_and_check_objective("2horizons", -3796309121478.1226)

    def test_example_2horizons_w_hydro(self):
        """
        Check validation and objective function value of
        "2horizons_w_hydro" example
        :return:
        """

        self.check_validation("2horizons_w_hydro")
        self.run_and_check_objective("2horizons_w_hydro", -219136981.90835398)

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
            -179455911.23328674
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
                                     -214913823.367428)

    def test_example_2periods(self):
        """
        Check validation and objective function value of "2periods" example
        :return:
        """

        self.check_validation("2periods")
        self.run_and_check_objective("2periods", -75926182429562.45)

    def test_example_2periods_new_build(self):
        """
        Check validation and objective function value of "2periods_new_build" example
        """

        self.check_validation("2periods_new_build")
        self.run_and_check_objective("2periods_new_build", -10085845900.191605)

    def test_example_2periods_new_build_2zones(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones")
        self.run_and_check_objective("2periods_new_build_2zones",
                                     -20171691806.955837)

    def test_example_2periods_new_build_2zones_new_build_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_new_build_transmission" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_new_build_transmission")
        self.run_and_check_objective(
            "2periods_new_build_2zones_new_build_transmission",
            -7028494941419.333
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
                                     -20171691752.98445)

    def test_example_2periods_new_build_2zones_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission" example
        :return:
        """
        print("platform: ", platform.system())
        print("release: ", platform.release())

        self.check_validation("2periods_new_build_2zones_transmission")
        self.run_and_check_objective("2periods_new_build_2zones_transmission",
                                     -220771078212318.25)

    def test_example_2periods_new_build_2zones_transmission_w_losses(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_transmission_w_losses")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_w_losses",
            -238291078037118.25
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
            -238291078037118.25
        )

    def test_example_2periods_new_build_rps(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps" example
        :return:
        """

        self.check_validation("2periods_new_build_rps")
        self.run_and_check_objective("2periods_new_build_rps",
                                     -26966855745114.633)

    def test_example_2periods_new_build_rps_percent_target(self):
        """
        Check objective function value of
        "2periods_new_build_rps_percent_target" example
        This example should have the same objective function as
        test_example_2periods_new_build_rps, as its target is the same,
        but specified as percentage of load.
        :return:
        """

        self.check_validation("2periods_new_build_rps_percent_target")
        self.run_and_check_objective("2periods_new_build_rps_percent_target",
                                     -26966855745114.633)

    def test_example_2periods_new_build_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "2periods_new_build_cumulative_min_max" example
        :return:
        """

        self.check_validation("2periods_new_build_cumulative_min_max")
        self.run_and_check_objective("2periods_new_build_cumulative_min_max",
                                     -27166044526940.195)

    def test_example_single_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost" example
        :return:
        """

        self.check_validation("single_stage_prod_cost")
        self.run_and_check_objective("single_stage_prod_cost",
                                     {1: -1265436373826.0408,
                                      2: -1265436373826.0408,
                                      3: -1265436373826.0408})

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
                1: -1265436373826.0408,
                2: -1265436373826.0408,
                3: -1265436373826.0408
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
                                     {1: {1: -1265436373826.0408,
                                          2: -1265436373826.0408,
                                          3: -1265436373826.099},
                                      2: {1: -1265436373826.0408,
                                          2: -1265436373826.0408,
                                          3: -1265436373826.099},
                                      3: {1: -1265436373826.0408,
                                          2: -1265436373826.0408,
                                          3: -1265436373826.099}})

    def test_example_multi_stage_prod_cost_parallel(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost" example
        :return:
        """
        # TODO: figure why run_e2e processed gets terminated on linux when
        #  using parallel processing; skip test on linux for the time being
        if platform == "Linux":
            print("Skipping test_example_multi_stage_prod_cost_parallel on ",
                  platform)
        else:
            self.run_and_check_objective("multi_stage_prod_cost",
                                         {1: {1: -1265436373826.0408,
                                              2: -1265436373826.0408,
                                              3: -1265436373826.099},
                                          2: {1: -1265436373826.0408,
                                              2: -1265436373826.0408,
                                              3: -1265436373826.099},
                                          3: {1: -1265436373826.0408,
                                              2: -1265436373826.0408,
                                              3: -1265436373826.099}},
                                         parallel=3)

    def test_example_multi_stage_prod_cost_w_hydro(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_w_hydro"
        example
        :return:
        """

        self.check_validation("multi_stage_prod_cost_w_hydro")
        self.run_and_check_objective("multi_stage_prod_cost_w_hydro",
                                     {1: {1: -1411433910806.1167,
                                          2: -1411433910806.1167,
                                          3: -1411433910806.175},
                                      2: {1: -1411433910806.1167,
                                          2: -1411433910806.1167,
                                          3: -1411433910806.175},
                                      3: {1: -1411433910806.1167,
                                          2: -1411433910806.1167,
                                          3: -1411433910806.175}})

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
                1: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436372366.0408
                },
                2: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436372366.0408
                },
                3: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436372366.0408
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
                                     -75926125638846.83)

    def test_example_2periods_gen_bin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_bin_econ_retirement"
        example
        :return:
        """

        self.check_validation("2periods_gen_bin_econ_retirement")
        self.run_and_check_objective("2periods_gen_bin_econ_retirement",
                                     -75926182429562.45)

    def test_example_variable_gen_reserves(self):
        """
        Check validation and objective function value of
        "variable_gen_reserves"
        example; this example requires a non-linear solver
        :return:
        """

        self.check_validation("test_variable_gen_reserves")
        self.run_and_check_objective("test_variable_gen_reserves",
                                     -1343499590014.7651)

    def test_example_2periods_new_build_rps_variable_reserves(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_variable_reserves")
        self.run_and_check_objective("2periods_new_build_rps_variable_reserves",
                                     -4980266823.194146)

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
            -4980266823.194146
        )

    def test_example_test_ramp_up_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_constraints" example
        :return:
        """

        self.check_validation("test_ramp_up_constraints")
        self.run_and_check_objective("test_ramp_up_constraints",
                                     -3796309121478.1226)

    def test_example_test_ramp_up_and_down_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_and_down_constraints"
        example;
        :return:
        """

        self.check_validation("test_ramp_up_and_down_constraints")
        self.run_and_check_objective("test_ramp_up_and_down_constraints",
                                     -4730755816658.181)

    def test_example_2periods_new_build_rps_w_rps_ineligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_ineligible_storage" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_w_rps_ineligible_storage")
        self.run_and_check_objective(
            "2periods_new_build_rps_w_rps_ineligible_storage",
            -16980455713578.633
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
            -26966830249904.633
        )

    def test_example_test_new_solar(self):
        """
        Check validation and objective function value of
        "test_new_solar" example
        :return:
        """

        self.check_validation("test_new_solar")
        self.run_and_check_objective("test_new_solar", -3796301348838.3267)

    def test_example_test_new_binary_solar(self):
        """
        Check validation and objective function value of
        "test_new_binary_solar" example
        :return:
        """

        self.check_validation("test_new_binary_solar")
        self.run_and_check_objective("test_new_binary_solar",
                                     -3796300848658.342)

    def test_example_test_new_solar_carbon_cap(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap")
        self.run_and_check_objective("test_new_solar_carbon_cap",
                                     -58282515304521.79)

    def test_example_test_new_solar_carbon_cap_2zones_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_tx" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_tx")
        self.run_and_check_objective("test_new_solar_carbon_cap_2zones_tx",
                                     -58248087935073.625)

    def test_example_test_new_solar_carbon_cap_2zones_dont_count_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_dont_count_tx" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_dont_count_tx")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_dont_count_tx",
            -56530649982951.8
        )

    def test_example_test_new_solar_carbon_tax(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_tax" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_tax")
        self.run_and_check_objective("test_new_solar_carbon_tax",
                                     -3796369926691.2686)

    def test_example_2periods_new_build_simple_prm(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """

        self.check_validation("2periods_new_build_simple_prm")
        self.run_and_check_objective("2periods_new_build_simple_prm",
                                     -10153045900.191605)

    def test_example_2periods_new_build_local_capacity(self):
        """
        Check validation and objective function value of
        "2periods_new_build_local_capacity"
        example
        :return:
        """

        self.check_validation("2periods_new_build_local_capacity")
        self.run_and_check_objective("2periods_new_build_local_capacity",
                                     -10087189902.382917)

    def test_example_test_tx_dcopf(self):
        """
        Check validation and objective function value of
        "test_tx_dcopf" example
        :return:
        """

        self.check_validation("test_tx_dcopf")
        self.run_and_check_objective("test_tx_dcopf", -58248351050674.516)

    def test_example_test_tx_simple(self):
        """
        Check validation and objective function value of
        "test_tx_simple" example
        :return:
        """

        self.check_validation("test_tx_simple")
        self.run_and_check_objective("test_tx_simple", -58248338996673.625)

    def test_example_test_startup_shutdown_rates(self):
        """
        Check validation and objective function value of
        "test_startup_shutdown_rates"
        example
        :return:
        """

        self.check_validation("test_startup_shutdown_rates")
        self.run_and_check_objective("test_startup_shutdown_rates",
                                     -560795927282.9794)

    def test_no_fuels(self):
        """
        Check validation and objective function value of "test_no_fuels"
        example
        :return:
        """

        self.check_validation("test_no_fuels")
        self.run_and_check_objective("test_no_fuels", -3796000221920.0)

    def test_variable_om_curves(self):
        """
        Check validation and objective function value of
        "test_variable_om_curves"
        example
        :return:
        """

        self.check_validation("test_variable_om_curves")
        self.run_and_check_objective("test_variable_om_curves",
                                     -3796309193923.3223)

    def test_aux_cons(self):
        """
        Check validation and objective function value of
        "test_aux_cons" example

        Note: the objective function value is lower than that for the "test"
        example because the auxiliary consumption results in less
        overgeneration and therefore lower overgeneration penalty.
        """

        self.check_validation("test_aux_cons")
        self.run_and_check_objective("test_aux_cons", -3664910801437.807)

    def test_example_test_w_lf_down_percent_req(self):
        """
        Check validation and objective function value of
        "test_w_lf_down_percent_req" example
        :return:
        """

        self.check_validation("test_w_lf_down_percent_req")
        self.run_and_check_objective("test_w_lf_down_percent_req",
                                     -6643312468674.122)

    def test_example_2periods_new_build_capgroups(self):
        """
        Check validation and objective function value of "2periods_new_build" example
        """

        self.check_validation("2periods_new_build_capgroups")
        self.run_and_check_objective("2periods_new_build_capgroups",
                                     -5266183794340.191)

    def test_example_test_markets(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """

        self.check_validation("test_markets")
        self.run_and_check_objective("test_markets", -3504300478278.3403)

    def test_example_2periods_new_build_horizon_energy_target(self):
        """
        Check validation and objective function value of
        "test_example_2periods_new_build_horizon_energy_target" example
        :return:
        """

        self.check_validation("2periods_new_build_horizon_energy_target")
        self.run_and_check_objective("2periods_new_build_horizon_energy_target",
                                     -26966855745114.633)

    def test_example_2periods_new_build_horizon_energy_target_halfyear(self):
        """
        Check validation and objective function value of
        "2periods_new_build_horizon_energy_target_halfyear" example
        :return:
        """

        self.check_validation("2periods_new_build_horizon_energy_target_halfyear")
        self.run_and_check_objective("2periods_new_build_horizon_energy_target_halfyear",
                                     -101086984772727.86)

    def test_example_test_new_build_gen_var_stor_hyb(self):
        """
        Check validation and objective function value of
        "2periods_new_build_horizon_energy_target_halfyear" example
        :return:
        """

        self.check_validation("test_new_build_gen_var_stor_hyb")
        self.run_and_check_objective("test_new_build_gen_var_stor_hyb",
                                     -5797066114.34292)

    def test_carbon_tax_allowance(self):
        """
        Check validation and objective function value of
        "test_carbon_tax_allowance" example
        :return:
        """

        self.check_validation("test_carbon_tax_allowance")
        self.run_and_check_objective("test_carbon_tax_allowance",
                                     -3796356403371.2686)

    def test_min_max_build_trans(self):
        """
        Check validation and objective function value of
        "test_min_max_build_trans" example
        :return:
        """

        self.check_validation("test_min_max_build_trans")
        self.run_and_check_objective("test_min_max_build_trans",
                                     -7028538202569.945)

    def test_example_2periods_new_build_2zones_transmission_Tx1halfavail(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_Tx1halfavail" example
        :return:
        """

        self.check_validation(
            "2periods_new_build_2zones_transmission_Tx1halfavail"
        )
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_Tx1halfavail",
            -308370294932303.7
        )

    def test_example_2periods_new_build_2zones_transmission_Tx1halfavailmonthly(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_Tx1halfavail" example
        :return:
        """

        self.check_validation(
            "2periods_new_build_2zones_transmission_Tx1halfavailmonthly"
        )
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_Tx1halfavailmonthly",
            -308370294932303.7
        )

    @classmethod
    def tearDownClass(cls):
        os.remove(DB_PATH)
        for temp_file_ext in ["-shm", "-wal"]:
            temp_file = "{}{}".format(DB_PATH, temp_file_ext)
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()
