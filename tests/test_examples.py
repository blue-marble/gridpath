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

import ast
import csv
import logging
import multiprocessing
import os
import pandas as pd
import platform
import sqlite3
import unittest

from gridpath import run_end_to_end, run_scenario, validate_inputs
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
TEST_SCENARIOS_CSV = "../tests/test_data/test_scenario_objective_function_values.csv"

# Travis CI VM machines run on Ubuntu 16.04.7 LTS, which has an older
# version of Cbc only (2.8.12) and gives slightly different results for some
# tests
UBUNTU_16 = (
    True
    if (platform.system() == "Linux" and platform.release() == "4.15.0-1098-gcp")
    else False
)

# Windows check
WINDOWS = True if os.name == "nt" else False


class TestExamples(unittest.TestCase):
    """ """

    df = pd.read_csv(TEST_SCENARIOS_CSV, delimiter=",")
    df.set_index("test_scenario", inplace=True)

    def assertDictAlmostEqual(self, d1, d2, msg=None, places=7):
        # check if both inputs are dicts
        self.assertIsInstance(d1, dict, "First argument is not a dictionary")
        self.assertIsInstance(d2, dict, "Second argument is not a dictionary")

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
        validate_inputs.main(["--database", DB_PATH, "--scenario", test, "--quiet"])

        # Check that no validation issues are recorded in the db for the test
        expected_validations = []

        conn = connect_to_database(
            db_path=DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES
        )
        c = conn.cursor()
        validations = c.execute(
            """
            SELECT scenario_name FROM status_validation
            INNER JOIN
            (SELECT scenario_id, scenario_name FROM scenarios)
            USING (scenario_id)
            WHERE scenario_name = '{}'
            """.format(
                test
            )
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
            [
                "--database",
                DB_PATH,
                "--scenario",
                test,
                "--scenario_location",
                EXAMPLES_DIRECTORY,
                # "--log",
                # "--write_solver_files_to_logs_dir",
                # "--keepfiles",
                # "--symbolic",
                "--n_parallel_get_inputs",
                str(parallel),
                "--n_parallel_solve",
                str(parallel),
                "--quiet",
                "--mute_solver_output",
                "--testing",
            ]
        )

        # Check if we have a multiprocessing manager
        # If so, convert the manager proxy dictionary to a simple dictionary
        # to avoid errors
        # Done via copies to avoid broken pipe error
        if hasattr(multiprocessing, "managers"):
            if isinstance(actual_objective, multiprocessing.managers.DictProxy):
                # Make a dictionary from a copy of the objective
                actual_objective_copy = dict(actual_objective.copy())
                for subproblem in actual_objective.keys():
                    # If we have stages, make a dictionary form a copy of the
                    # stage dictionary for each subproblem
                    if isinstance(
                        actual_objective[subproblem], multiprocessing.managers.DictProxy
                    ):
                        stage_dict_copy = dict(actual_objective_copy[subproblem].copy())
                        # Reset the stage dictionary to the new simple
                        # dictionary object
                        actual_objective_copy[subproblem] = stage_dict_copy
                # Reset the objective to the new dictionary object
                actual_objective = actual_objective_copy

        # Uncomment this to save new objective function values
        df = pd.read_csv(TEST_SCENARIOS_CSV, delimiter=",")
        df.set_index("test_scenario", inplace=True)
        # Set dtype to 'object' so that we can have floats and dictionaries
        # in the column
        df["actual_objective"] = df["actual_objective"].astype("object")
        df.at[test, "actual_objective"] = actual_objective
        df.to_csv(TEST_SCENARIOS_CSV, index=True)

        # Multi-subproblem and/or multi-stage scenarios return dict
        if isinstance(expected_objective, dict):
            self.assertDictAlmostEqual(expected_objective, actual_objective, places=1)
        # Otherwise, objective is a single value
        else:
            self.assertAlmostEqual(expected_objective, actual_objective, places=1)

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
            port_csvs_to_db.main(
                ["--database", DB_PATH, "--csv_location", CSV_PATH, "--quiet"]
            )
        except Exception as e:
            print(
                "Error encountered during population of testing database "
                "{}.db. Deleting database ...".format(DB_NAME)
            )
            logging.exception(e)
            os.remove(DB_PATH)

        try:
            scenario.main(
                ["--database", DB_PATH, "--csv_path", SCENARIOS_CSV, "--quiet"]
            )
        except Exception as e:
            print(
                "Error encountered during population of testing database "
                "{}.db. Deleting database ...".format(DB_NAME)
            )
            logging.exception(e)
            os.remove(DB_PATH)

    def validate_and_test_example_generic(self, scenario_name, literal=False):
        # For multi-subproblem and multi-stage problems, we need to evaluate
        # the objective function as a literal (as it is in dictionary format
        # stored as string in the CSV)
        # For the rest of the problems, convert the objective function value
        # from string to floating point data type
        if literal:
            objective = ast.literal_eval(
                self.df.loc[scenario_name]["expected_objective"]
            )
        else:
            objective = float(self.df.loc[scenario_name]["expected_objective"])
        self.check_validation(scenario_name)
        self.run_and_check_objective(scenario_name, objective)

    def test_example_test(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """
        scenario_name = "test"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_no_overgen_allowed(self):
        """
        Check validation and objective function value of
        "test_no_overgen_allowed" example
        :return:
        """

        scenario_name = "test_no_overgen_allowed"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_build_storage" example
        :return:
        """

        scenario_name = "test_new_build_storage"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_binary_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_binary_build_storage" example
        :return:
        """
        scenario_name = "test_new_binary_build_storage"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_build_storage_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "test_new_build_storage_cumulative_min_max" example
        :return:
        """
        scenario_name = "test_new_build_storage_cumulative_min_max"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_no_reserves(self):
        """
        Check validation and objective function value of
        "test_no_reserves" example
        :return:
        """
        scenario_name = "test_no_reserves"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_hydro(self):
        """
        Check validation and objective function value of "test_w_hydro" example
        :return:
        """
        scenario_name = "test_w_hydro"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_storage(self):
        """
        Check validation and objective function value of "test_w_storage" example
        :return:
        """
        scenario_name = "test_w_storage"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2horizons(self):
        """
        Check validation and objective function value of "2horizons" example
        :return:
        """
        scenario_name = "2horizons"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2horizons_w_hydro(self):
        """
        Check validation and objective function value of
        "2horizons_w_hydro" example
        :return:
        """
        scenario_name = "2horizons_w_hydro"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

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
        scenario_name = "2horizons_w_hydro_and_nuclear_binary_availability"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

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
        scenario_name = "2horizons_w_hydro_w_balancing_types"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods(self):
        """
        Check validation and objective function value of "2periods" example
        :return:
        """
        scenario_name = "2periods"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build(self):
        """
        Check validation and objective function value of "2periods_new_build" example
        """
        scenario_name = "2periods_new_build"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_new_build_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_new_build_transmission" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_new_build_transmission"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_singleBA(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_singleBA"
        example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_singleBA"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_transmission"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_transmission_w_losses(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_transmission_w_losses"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_transmission_w_losses_opp_dir(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses_opp_dir" example

        Note: this should be the same as the objective function for
        2periods_new_build_2zones_transmission_w_losses
        :return:
        """
        scenario_name = "2periods_new_build_2zones_transmission_w_losses_opp_dir"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_rps(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps" example
        :return:
        """
        scenario_name = "2periods_new_build_rps"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_rps_percent_target(self):
        """
        Check objective function value of
        "2periods_new_build_rps_percent_target" example
        This example should have the same objective function as
        test_example_2periods_new_build_rps, as its target is the same,
        but specified as percentage of load.
        :return:
        """
        scenario_name = "2periods_new_build_rps_percent_target"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "2periods_new_build_cumulative_min_max" example
        :return:
        """
        scenario_name = "2periods_new_build_cumulative_min_max"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_single_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost" example
        :return:
        """
        scenario_name = "single_stage_prod_cost"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_single_stage_prod_cost_linked_subproblems(self):
        """
        Check objective function values of
        "single_stage_prod_cost_linked_subproblems" example
        :return:
        """
        scenario_name = "single_stage_prod_cost_linked_subproblems"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_single_stage_prod_cost_linked_subproblems_w_hydro(self):
        """
        Check objective function values of
        "single_stage_prod_cost_linked_subproblems" example
        :return:
        """
        scenario_name = "single_stage_prod_cost_linked_subproblems_w_hydro"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_multi_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost" example
        :return:
        """
        scenario_name = "multi_stage_prod_cost"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_single_stage_prod_cost_cycle_select(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost_cycle_select" example. This example is the same as
        single_stage_prod_cost but the Coal and Gas_CCGT plants have mutually
        exclusive commitment in this example.
        """
        scenario_name = "single_stage_prod_cost_cycle_select"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_multi_stage_prod_cost_parallel(self):
        """
        Check "multi_stage_prod_cost" example running subproblems in parallel
        (getting inputs and optimization)
        :return:
        """
        run_end_to_end.main(
            [
                "--database",
                DB_PATH,
                "--scenario",
                "multi_stage_prod_cost",
                "--scenario_location",
                EXAMPLES_DIRECTORY,
                # "--log",
                # "--write_solver_files_to_logs_dir",
                # "--keepfiles",
                # "--symbolic",
                "--n_parallel_get_inputs",
                "3",
                "--n_parallel_solve",
                "3",
                "--quiet",
                "--mute_solver_output",
                "--testing",
            ]
        )

    def test_example_multi_stage_prod_cost_w_hydro(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_w_hydro"
        example
        :return:
        """
        scenario_name = "multi_stage_prod_cost_w_hydro"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_multi_stage_prod_cost_linked_subproblems(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_linked_subproblems" example
        :return:
        """
        scenario_name = "multi_stage_prod_cost_linked_subproblems"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_2periods_gen_lin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_lin_econ_retirement"
        example
        :return:
        """
        scenario_name = "2periods_gen_lin_econ_retirement"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_gen_bin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_bin_econ_retirement"
        example
        :return:
        """
        scenario_name = "2periods_gen_bin_econ_retirement"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_variable_gen_reserves(self):
        """
        Check validation and objective function value of
        "variable_gen_reserves"
        example; this example requires a non-linear solver
        :return:
        """
        scenario_name = "test_variable_gen_reserves"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_rps_variable_reserves(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves" example
        :return:
        """
        scenario_name = "2periods_new_build_rps_variable_reserves"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_rps_variable_reserves_subhourly_adj(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves_subhourly_adj" example
        :return:
        """
        scenario_name = "2periods_new_build_rps_variable_reserves_subhourly_adj"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_ramp_up_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_constraints" example
        :return:
        """
        scenario_name = "test_ramp_up_constraints"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_ramp_up_and_down_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_and_down_constraints"
        example;
        :return:
        """
        scenario_name = "test_ramp_up_and_down_constraints"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_rps_w_rps_ineligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_ineligible_storage" example
        :return:
        """
        scenario_name = "2periods_new_build_rps_w_rps_ineligible_storage"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_rps_w_rps_eligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_eligible_storage" example
        :return:
        """
        scenario_name = "2periods_new_build_rps_w_rps_eligible_storage"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar(self):
        """
        Check validation and objective function value of
        "test_new_solar" example
        :return:
        """
        scenario_name = "test_new_solar"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_binary_solar(self):
        """
        Check validation and objective function value of
        "test_new_binary_solar" example
        :return:
        """
        scenario_name = "test_new_binary_solar"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_cap(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_cap_2zones_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_tx" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap_2zones_tx"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_cap_2zones_dont_count_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_dont_count_tx" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap_2zones_dont_count_tx"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_tax(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_tax" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_tax"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """
        scenario_name = "2periods_new_build_simple_prm"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm_w_energy_only(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """
        scenario_name = "2periods_new_build_simple_prm_w_energy_only"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm_w_energy_only_deliv_cap_limit(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """
        scenario_name = "2periods_new_build_simple_prm_w_energy_only_deliv_cap_limit"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_local_capacity(self):
        """
        Check validation and objective function value of
        "2periods_new_build_local_capacity"
        example
        :return:
        """
        scenario_name = "2periods_new_build_local_capacity"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_tx_dcopf(self):
        """
        Check validation and objective function value of
        "test_tx_dcopf" example
        :return:
        """
        scenario_name = "test_tx_dcopf"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_tx_simple(self):
        """
        Check validation and objective function value of
        "test_tx_simple" example
        :return:
        """
        scenario_name = "test_tx_simple"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_startup_shutdown_rates(self):
        """
        Check validation and objective function value of
        "test_startup_shutdown_rates"
        example
        :return:
        """
        scenario_name = "test_startup_shutdown_rates"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_no_fuels(self):
        """
        Check validation and objective function value of "test_no_fuels"
        example
        :return:
        """
        scenario_name = "test_no_fuels"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_variable_om_curves(self):
        """
        Check validation and objective function value of
        "test_variable_om_curves"
        example
        :return:
        """
        scenario_name = "test_variable_om_curves"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_aux_cons(self):
        """
        Check validation and objective function value of
        "test_aux_cons" example

        Note: the objective function value is lower than that for the "test"
        example because the auxiliary consumption results in less
        overgeneration and therefore lower overgeneration penalty.
        """
        scenario_name = "test_aux_cons"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_lf_down_percent_req(self):
        """
        Check validation and objective function value of
        "test_w_lf_down_percent_req" example
        :return:
        """
        scenario_name = "test_w_lf_down_percent_req"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_capgroups(self):
        """
        Check validation and objective function value of "2periods_new_build" example
        """
        scenario_name = "2periods_new_build_capgroups"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_markets(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """
        scenario_name = "test_markets"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_horizon_energy_target(self):
        """
        Check validation and objective function value of
        "test_example_2periods_new_build_horizon_energy_target" example
        :return:
        """
        scenario_name = "2periods_new_build_horizon_energy_target"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_horizon_energy_target_halfyear(self):
        """
        Check validation and objective function value of
        "2periods_new_build_horizon_energy_target_halfyear" example
        :return:
        """
        scenario_name = "2periods_new_build_horizon_energy_target_halfyear"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_build_gen_var_stor_hyb(self):
        """
        Check validation and objective function value of
        "2periods_new_build_horizon_energy_target_halfyear" example
        :return:
        """
        scenario_name = "test_new_build_gen_var_stor_hyb"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_carbon_tax_allowance(self):
        """
        Check validation and objective function value of
        "test_carbon_tax_allowance" example
        :return:
        """
        scenario_name = "test_carbon_tax_allowance"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_min_max_build_trans(self):
        """
        Check validation and objective function value of
        "test_min_max_build_trans" example
        :return:
        """
        scenario_name = "test_min_max_build_trans"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_transmission_Tx1halfavail(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_Tx1halfavail" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_transmission_Tx1halfavail"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_transmission_Tx1halfavailmonthly(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_Tx1halfavail" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_transmission_Tx1halfavailmonthly"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_cheap_fuel_blend(self):
        """
        Check validation and objective function value of "test_cheap_fuel_blend" example
        :return:
        """
        scenario_name = "test_cheap_fuel_blend"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_cheap_fuel_blend_w_limit(self):
        """
        Check validation and objective function value of
        "test_cheap_fuel_blend_w_limit" example
        :return:
        """
        scenario_name = "test_cheap_fuel_blend_w_limit"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_fuel_burn_limit(self):
        """
        Check validation and objective function value of
        "test_new_solar_fuel_burn_limit" example. Inputs set up so that this should
        be the same as the "test_new_solar_carbon_cap" example.
        :return:
        """
        scenario_name = "test_new_solar_fuel_burn_limit"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_fuel_burn_limit_relative(self):
        """
        Check validation and objective function value of
        "test_new_solar_fuel_burn_limit_relative" example. Inputs set up so that this
        should be the same as the "test_new_solar_fuel_burn_limit" example.
        :return:
        """
        scenario_name = "test_new_solar_fuel_burn_limit_relative"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_test_w_solver_options(self):
        """
        Check validation and objective function value of "test_w_solver_options" example
        :return:
        """
        scenario_name = "test_w_solver_options"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_carbon_tax_allowance_with_different_fuel_groups(self):
        """
        Check validation and objective function value of
        "test_carbon_tax_allowance_with_different_fuel_groups" example
        :return:
        """
        scenario_name = "test_carbon_tax_allowance_with_different_fuel_groups"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_performance_standard(self):
        """
        Check validation and objective function value of "test_performance_standard" example
        :return:
        """
        scenario_name = "test_performance_standard"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_tx_flow(self):
        """
        Check validation and objective function value of
        "test_tx_flow" example
        :return:
        """
        scenario_name = "test_tx_flow"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_reserve_prj_contribution(self):
        """
        Check validation and objective function value of
        "test_reserve_prj_contribution" example.
        This example is based on "test_new_solar" with the only difference, the LF UP
        requirement ID
        :return:
        """
        scenario_name = "test_new_solar_reserve_prj_contribution"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_test_new_solar_carbon_cap_2zones_tx_hydrogen_prod(self):
        """
        Check validation and objective function value of
        "test_reserve_prj_contribution" example.
        This example is based on "test_new_solar" with the only difference, the LF UP
        requirement ID
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap_2zones_tx_hydrogen_prod"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_test_new_solar_carbon_cap_2zones_tx_hydrogen_prod_new(self):
        """
        Check validation and objective function value of
        "test_reserve_prj_contribution" example.
        This example is based on "test_new_solar" with the only difference, the LF UP
        requirement ID
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap_2zones_tx_hydrogen_prod_new"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_cap_dac(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_dac" example.

        Note that the same version of Cbc (v2.10.5) produces a slightly different
        objective function for this problem on Windows than on Mac.
        :return:
        """
        scenario_name = "test_new_solar_carbon_cap_dac"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_cap_factor_limits(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """
        scenario_name = "test_cap_factor_limits"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_multi_stage_prod_cost_w_markets(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_w_markets" example
        :return:
        """
        scenario_name = "multi_stage_prod_cost_w_markets"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
        )

    def test_example_test_supplemental_firing(self):
        """
        Check validation and objective function value of "test_supplemental_firing" example
        :return:
        """
        scenario_name = "test_supplemental_firing"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_tx_capacity_groups(self):
        """
        Check validation and objective function value of
        "test_tx_capacity_groups" example
        :return:
        """
        scenario_name = "test_tx_capacity_groups"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_fin_lifetime(self):
        """
        Check validation and objective function value of
        "2periods_new_build_fin_lifetime" example. Same as "2periods_new_build" but
        with shorter financial lifetimes and some fixed costs. Cost is lower because
        the same payment is made fewer times.
        """
        scenario_name = "2periods_new_build_fin_lifetime"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_cumulative_and_vintage_min_max(self):
        """
        Check validation and objective function value of
        "2periods_new_build_cumulative_and_vintage_min_max" example. It is the same
        as 2periods_new_build_cumulative_and_min_max but with a max in 2020 for the
        CCGT to force early build and a min on the CT in 2030 to force more build.

        :return:
        """
        scenario_name = "2periods_new_build_cumulative_and_vintage_min_max"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_storage_w_soc_penalty(self):
        """
        Check validation and objective function value of "test_w_storage_w_soc_penalty"
        example
        :return:
        """
        scenario_name = "test_w_storage_w_soc_penalty"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_storage_w_soc_last_tmp_penalty(self):
        """
        Check validation and objective function value of "test_w_storage_w_soc_penalty"
        example
        :return:
        """
        scenario_name = "test_w_storage_w_soc_last_tmp_penalty"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_itc(self):
        """
        Check validation and objective function value of
        "test_new_solar_itc" example
        :return:
        """
        scenario_name = "test_new_solar_itc"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_build_storage_itc(self):
        """
        Check validation and objective function value of
        "test_new_build_storage" example
        :return:
        """
        scenario_name = "test_new_build_storage_itc"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm_2loadzones(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm_2loadzones"
        example
        :return:
        """
        scenario_name = "2periods_new_build_simple_prm_2loadzones"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm_2loadzones_newtx_w_transfers(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm_w_transfers"
        example
        :return:
        """
        scenario_name = "2periods_new_build_simple_prm_2loadzones_newtx_w_transfers"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm_2loadzones_newtx_w_transfers_w_costs(
        self,
    ):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm_2loadzones_newtx_w_transfers_w_costs"
        example
        :return:
        """
        scenario_name = (
            "2periods_new_build_simple_prm_2loadzones_newtx_w_transfers_w_costs"
        )
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_period_tx_targets(self):
        """
        Check validation and objective function value of "test_example_test_period_tx_targets"
        example
        :return:
        """
        scenario_name = "test_period_tx_targets"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_flex_load(self):
        """
        Check validation and objective function value of "test_w_storage" example
        :return:
        """
        scenario_name = "test_w_flex_load"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_w_relative_capacity_instead_of_potential(self):
        """
        Check validation and objective function value of
        "test_new_solar" example
        :return:
        """
        scenario_name = "test_new_solar_w_relative_capacity_instead_of_potential"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_2zones_transmission_w_hurdle_rates(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_hurdle_rates" example
        :return:
        """
        scenario_name = "2periods_new_build_2zones_transmission_w_hurdle_rates"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_2periods_new_build_simple_prm_2loadzones_newtx_w_transfers_w_subsidies(
        self,
    ):
        """
        Check validation and objective function value of
        "test_new_solar" example
        :return:
        """
        scenario_name = (
            "2periods_new_build_simple_prm_2loadzones_newtx_w_transfers_w_subsidies"
        )
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_build_storage_itc_single_superperiod(self):
        """
        Check validation and objective function value of
        "test_new_build_storage_itc_single_superperiodself" example
        :return:
        """
        scenario_name = "test_new_build_storage_itc_single_superperiod"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_incomplete_only(self):
        """
        Check that the "incomplete only" functionality works with no errors.
        :return:
        """
        actual_objective = run_scenario.main(
            [
                "--scenario",
                "test",
                "--scenario_location",
                EXAMPLES_DIRECTORY,
                "--quiet",
                "--mute_solver_output",
                "--incomplete_only",
            ]
        )

    def test_example_test_w_storage_starting_soc(self):
        """
        Check validation and objective function value of
        "test_w_storage_starting_soc" example
        :return:
        """
        scenario_name = "test_w_storage_starting_soc"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_w_nonfuel_emissions(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """
        scenario_name = "test_w_nonfuel_emissions"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_credits(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_credits" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_credits"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_performance_standard_carbon_credits(self):
        """
        Check validation and objective function value of "test_performance_standard" example
        :return:
        """
        scenario_name = "test_performance_standard_carbon_credits"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_tax_w_carbon_credits(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_tax_w_carbon_credits" example
        :return:
        """
        scenario_name = "test_new_solar_carbon_tax_w_carbon_credits"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_example_test_new_solar_carbon_credits_w_sell(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_credits_w_sell" example
        The carbon credit price must be set higher than the cost of USE in this
        example to incentivize the project to not run and generate credits.
        :return:
        """
        scenario_name = "test_new_solar_carbon_credits_w_sell"
        self.validate_and_test_example_generic(scenario_name=scenario_name)

    def test_test_performance_standard_carbon_credits_w_cap_no_credits_mapping(self):
        """
        Check validation and objective function value of "test_performance_standard" example
        :return:
        """

        self.check_validation(
            "test_performance_standard_carbon_credits_w_cap_no_credits_mapping"
        )
        self.run_and_check_objective(
            "test_performance_standard_carbon_credits_w_cap_no_credits_mapping",
            -3592014778836.2856,
        )

    def test_example_single_stage_prod_cost_w_spinup_lookahead(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost_w_spinup_lookahead" example
        :return:
        """
        scenario_name = "single_stage_prod_cost_w_spinup_lookahead"
        self.validate_and_test_example_generic(
            scenario_name=scenario_name, literal=True
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
