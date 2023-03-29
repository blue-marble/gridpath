# Copyright 2016-2022 Blue Marble Analytics LLC.
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
        # If so, convert the manager proxy dictionary to to a simple dictionary
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
        self.run_and_check_objective("test_no_overgen_allowed", -5256303226874.182)

    def test_example_test_new_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_build_storage" example
        :return:
        """

        self.check_validation("test_new_build_storage")
        self.run_and_check_objective("test_new_build_storage", -4484591199.92)

    def test_example_test_new_binary_build_storage(self):
        """
        Check validation and objective function value of
        "test_new_binary_build_storage" example
        :return:
        """

        self.check_validation("test_new_binary_build_storage")
        self.run_and_check_objective(
            "test_new_binary_build_storage", -4484591878.4800005
        )

    def test_example_test_new_build_storage_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "test_new_build_storage_cumulative_min_max" example
        :return:
        """

        self.check_validation("test_new_build_storage_cumulative_min_max")
        self.run_and_check_objective(
            "test_new_build_storage_cumulative_min_max", -4561692383.87
        )

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
            "2horizons_w_hydro_and_nuclear_binary_availability", -179455911.23328674
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
        self.run_and_check_objective(
            "2horizons_w_hydro_w_balancing_types", -214913823.367428
        )

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
        objective = -20171691806.955845 if UBUNTU_16 else -20171691798.193214

        self.check_validation("2periods_new_build_2zones")
        self.run_and_check_objective("2periods_new_build_2zones", objective)

    def test_example_2periods_new_build_2zones_new_build_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_new_build_transmission" example
        :return:
        """

        self.check_validation("2periods_new_build_2zones_new_build_transmission")
        self.run_and_check_objective(
            "2periods_new_build_2zones_new_build_transmission", -7028494941419.333
        )

    def test_example_2periods_new_build_2zones_singleBA(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_singleBA"
        example
        :return:
        """

        objective = -20171691752.945038 if UBUNTU_16 else -20171691750.059643

        self.check_validation("2periods_new_build_2zones_singleBA")
        self.run_and_check_objective("2periods_new_build_2zones_singleBA", objective)

    def test_example_2periods_new_build_2zones_transmission(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission" example
        :return:
        """
        objective = -220771078212324.8 if UBUNTU_16 else -220771078212311.7
        self.check_validation("2periods_new_build_2zones_transmission")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission", objective
        )

    def test_example_2periods_new_build_2zones_transmission_w_losses(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses" example
        :return:
        """
        objective = -238291078037124.8 if UBUNTU_16 else -238291078037111.7

        self.check_validation("2periods_new_build_2zones_transmission_w_losses")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_w_losses", objective
        )

    def test_example_2periods_new_build_2zones_transmission_w_losses_opp_dir(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_w_losses_opp_dir" example

        Note: this should be the same as the objective function for
        2periods_new_build_2zones_transmission_w_losses
        :return:
        """
        objective = -238291078037124.8 if UBUNTU_16 else -238291078037111.7

        self.check_validation("2periods_new_build_2zones_transmission_w_losses_opp_dir")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_w_losses_opp_dir", objective
        )

    def test_example_2periods_new_build_rps(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps" example
        :return:
        """
        objective = -26966855745114.633 if UBUNTU_16 else -26966855745108.062

        self.check_validation("2periods_new_build_rps")
        self.run_and_check_objective("2periods_new_build_rps", objective)

    def test_example_2periods_new_build_rps_percent_target(self):
        """
        Check objective function value of
        "2periods_new_build_rps_percent_target" example
        This example should have the same objective function as
        test_example_2periods_new_build_rps, as its target is the same,
        but specified as percentage of load.
        :return:
        """
        objective = -26966855745114.633 if UBUNTU_16 else -26966855745108.062

        self.check_validation("2periods_new_build_rps_percent_target")
        self.run_and_check_objective("2periods_new_build_rps_percent_target", objective)

    def test_example_2periods_new_build_cumulative_min_max(self):
        """
        Check validation and objective function value of
        "2periods_new_build_cumulative_min_max" example
        :return:
        """

        self.check_validation("2periods_new_build_cumulative_min_max")
        self.run_and_check_objective(
            "2periods_new_build_cumulative_min_max", -27166044526940.195
        )

    def test_example_single_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost" example
        :return:
        """

        self.check_validation("single_stage_prod_cost")
        self.run_and_check_objective(
            "single_stage_prod_cost",
            {1: -1265436373826.0408, 2: -1265436373826.0408, 3: -1265436373826.0408},
        )

    def test_example_single_stage_prod_cost_linked_subproblems(self):
        """
        Check objective function values of
        "single_stage_prod_cost_linked_subproblems" example
        :return:
        """
        self.check_validation("single_stage_prod_cost_linked_subproblems")
        self.run_and_check_objective(
            "single_stage_prod_cost_linked_subproblems",
            {1: -1265436373826.0408, 2: -1265436373826.0408, 3: -1265436373826.0408},
        )

    def test_example_single_stage_prod_cost_linked_subproblems_w_hydro(self):
        """
        Check objective function values of
        "single_stage_prod_cost_linked_subproblems" example
        :return:
        """
        self.check_validation("single_stage_prod_cost_linked_subproblems_w_hydro")
        self.run_and_check_objective(
            "single_stage_prod_cost_linked_subproblems_w_hydro",
            {1: -71637941.12254025, 2: -71637941.12254025, 3: -71637941.12254025},
        )

    def test_example_multi_stage_prod_cost(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost" example
        :return:
        """

        self.check_validation("multi_stage_prod_cost")
        self.run_and_check_objective(
            "multi_stage_prod_cost",
            {
                1: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436373826.099,
                },
                2: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436373826.099,
                },
                3: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436373826.099,
                },
            },
        )

    def test_example_single_stage_prod_cost_cycle_select(self):
        """
        Check validation and objective function values of
        "single_stage_prod_cost_cycle_select" example. This example is the same as
        single_stage_prod_cost but the Coal and Gas_CCGT plants have mutually
        exclusive commitment in this example.
        """

        self.check_validation("single_stage_prod_cost_cycle_select")
        self.run_and_check_objective(
            "single_stage_prod_cost_cycle_select",
            {1: -7154084662888.654, 2: -7154084662888.654, 3: -7154084662888.654},
        )

    def test_example_multi_stage_prod_cost_parallel(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost" example running subproblems in parallel
        :return:
        """
        self.run_and_check_objective(
            "multi_stage_prod_cost",
            {
                1: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436373826.099,
                },
                2: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436373826.099,
                },
                3: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436373826.099,
                },
            },
            parallel=3,
        )

    def test_example_multi_stage_prod_cost_w_hydro(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_w_hydro"
        example
        :return:
        """

        self.check_validation("multi_stage_prod_cost_w_hydro")
        self.run_and_check_objective(
            "multi_stage_prod_cost_w_hydro",
            {
                1: {
                    1: -1411433910806.1167,
                    2: -1411433910806.1167,
                    3: -1411433910806.175,
                },
                2: {
                    1: -1411433910806.1167,
                    2: -1411433910806.1167,
                    3: -1411433910806.175,
                },
                3: {
                    1: -1411433910806.1167,
                    2: -1411433910806.1167,
                    3: -1411433910806.175,
                },
            },
        )

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
                    3: -1265436372366.0408,
                },
                2: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436372366.0408,
                },
                3: {
                    1: -1265436373826.0408,
                    2: -1265436373826.0408,
                    3: -1265436372366.0408,
                },
            },
        )

    def test_example_2periods_gen_lin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_lin_econ_retirement"
        example
        :return:
        """

        self.check_validation("2periods_gen_lin_econ_retirement")
        self.run_and_check_objective(
            "2periods_gen_lin_econ_retirement", -75926125638846.83
        )

    def test_example_2periods_gen_bin_econ_retirement(self):
        """
        Check validation and objective function value of
        "2periods_gen_bin_econ_retirement"
        example
        :return:
        """

        self.check_validation("2periods_gen_bin_econ_retirement")
        self.run_and_check_objective(
            "2periods_gen_bin_econ_retirement", -75926182429562.45
        )

    def test_example_variable_gen_reserves(self):
        """
        Check validation and objective function value of
        "variable_gen_reserves"
        example; this example requires a non-linear solver
        :return:
        """

        self.check_validation("test_variable_gen_reserves")
        self.run_and_check_objective("test_variable_gen_reserves", -1343499590014.7651)

    def test_example_2periods_new_build_rps_variable_reserves(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_variable_reserves")
        self.run_and_check_objective(
            "2periods_new_build_rps_variable_reserves", -4980266823.194146
        )

    def test_example_2periods_new_build_rps_variable_reserves_subhourly_adj(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_variable_reserves_subhourly_adj" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_variable_reserves_subhourly_adj")
        self.run_and_check_objective(
            "2periods_new_build_rps_variable_reserves_subhourly_adj", -4980266823.194146
        )

    def test_example_test_ramp_up_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_constraints" example
        :return:
        """

        self.check_validation("test_ramp_up_constraints")
        self.run_and_check_objective("test_ramp_up_constraints", -3796309121478.1226)

    def test_example_test_ramp_up_and_down_constraints(self):
        """
        Check validation and objective function value of
        "test_ramp_up_and_down_constraints"
        example;
        :return:
        """

        self.check_validation("test_ramp_up_and_down_constraints")
        self.run_and_check_objective(
            "test_ramp_up_and_down_constraints", -4730755816658.181
        )

    def test_example_2periods_new_build_rps_w_rps_ineligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_ineligible_storage" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_w_rps_ineligible_storage")
        self.run_and_check_objective(
            "2periods_new_build_rps_w_rps_ineligible_storage", -16980455713578.633
        )

    def test_example_2periods_new_build_rps_w_rps_eligible_storage(self):
        """
        Check validation and objective function value of
        "2periods_new_build_rps_w_rps_eligible_storage" example
        :return:
        """

        self.check_validation("2periods_new_build_rps_w_rps_eligible_storage")
        self.run_and_check_objective(
            "2periods_new_build_rps_w_rps_eligible_storage", -26966830249904.633
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
        self.run_and_check_objective("test_new_binary_solar", -3796300848658.342)

    def test_example_test_new_solar_carbon_cap(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap")
        self.run_and_check_objective("test_new_solar_carbon_cap", -58282515304521.79)

    def test_example_test_new_solar_carbon_cap_2zones_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_tx" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_tx")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_tx", -58248087935073.625
        )

    def test_example_test_new_solar_carbon_cap_2zones_dont_count_tx(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_dont_count_tx" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_dont_count_tx")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_dont_count_tx", -56530649982951.8
        )

    def test_example_test_new_solar_carbon_tax(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_tax" example
        :return:
        """

        self.check_validation("test_new_solar_carbon_tax")
        self.run_and_check_objective("test_new_solar_carbon_tax", -3796369926691.2686)

    def test_example_2periods_new_build_simple_prm(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """
        objective = -10153045886.999044 if UBUNTU_16 else -10153045900.191605
        self.check_validation("2periods_new_build_simple_prm")
        self.run_and_check_objective("2periods_new_build_simple_prm", objective)

    def test_example_2periods_new_build_simple_prm_w_energy_only(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """
        self.check_validation("2periods_new_build_simple_prm_w_energy_only")
        self.run_and_check_objective(
            "2periods_new_build_simple_prm_w_energy_only", -11133045895.810287
        )

    def test_example_2periods_new_build_simple_prm_w_energy_only_deliv_cap_limit(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm"
        example
        :return:
        """
        self.check_validation(
            "2periods_new_build_simple_prm_w_energy_only_deliv_cap_limit"
        )
        self.run_and_check_objective(
            "2periods_new_build_simple_prm_w_energy_only_deliv_cap_limit",
            -11133045900.191603,
        )

    def test_example_2periods_new_build_local_capacity(self):
        """
        Check validation and objective function value of
        "2periods_new_build_local_capacity"
        example
        :return:
        """

        self.check_validation("2periods_new_build_local_capacity")
        self.run_and_check_objective(
            "2periods_new_build_local_capacity", -10087189902.382917
        )

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
        self.run_and_check_objective("test_startup_shutdown_rates", -560795927282.9794)

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
        self.run_and_check_objective("test_variable_om_curves", -3796309193923.3223)

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
        self.run_and_check_objective("test_w_lf_down_percent_req", -6643312468674.122)

    def test_example_2periods_new_build_capgroups(self):
        """
        Check validation and objective function value of "2periods_new_build" example
        """

        self.check_validation("2periods_new_build_capgroups")
        self.run_and_check_objective("2periods_new_build_capgroups", -5266183794340.191)

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
        objective = -26966855745114.633 if UBUNTU_16 else -26966855745108.062

        self.check_validation("2periods_new_build_horizon_energy_target")
        self.run_and_check_objective(
            "2periods_new_build_horizon_energy_target", objective
        )

    def test_example_2periods_new_build_horizon_energy_target_halfyear(self):
        """
        Check validation and objective function value of
        "2periods_new_build_horizon_energy_target_halfyear" example
        :return:
        """
        objective = -101086984772727.86 if UBUNTU_16 else -101086984772721.28

        self.check_validation("2periods_new_build_horizon_energy_target_halfyear")
        self.run_and_check_objective(
            "2periods_new_build_horizon_energy_target_halfyear", objective
        )

    def test_example_test_new_build_gen_var_stor_hyb(self):
        """
        Check validation and objective function value of
        "2periods_new_build_horizon_energy_target_halfyear" example
        :return:
        """

        self.check_validation("test_new_build_gen_var_stor_hyb")
        self.run_and_check_objective(
            "test_new_build_gen_var_stor_hyb", -5797066114.34292
        )

    def test_example_test_carbon_tax_allowance(self):
        """
        Check validation and objective function value of
        "test_carbon_tax_allowance" example
        :return:
        """

        self.check_validation("test_carbon_tax_allowance")
        self.run_and_check_objective("test_carbon_tax_allowance", -3796303120157.2686)

    def test_example_test_min_max_build_trans(self):
        """
        Check validation and objective function value of
        "test_min_max_build_trans" example
        :return:
        """
        objective = -7028538202569.947 if UBUNTU_16 else -7028538202574.325

        self.check_validation("test_min_max_build_trans")
        self.run_and_check_objective("test_min_max_build_trans", objective)

    def test_example_2periods_new_build_2zones_transmission_Tx1halfavail(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_Tx1halfavail" example
        :return:
        """
        objective = -308370294932310.25 if UBUNTU_16 else -308370294932297.06

        self.check_validation("2periods_new_build_2zones_transmission_Tx1halfavail")
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_Tx1halfavail", objective
        )

    def test_example_2periods_new_build_2zones_transmission_Tx1halfavailmonthly(self):
        """
        Check validation and objective function value of
        "2periods_new_build_2zones_transmission_Tx1halfavail" example
        :return:
        """

        objective = -308370294932310.25 if UBUNTU_16 else -308370294932297.06

        self.check_validation(
            "2periods_new_build_2zones_transmission_Tx1halfavailmonthly"
        )
        self.run_and_check_objective(
            "2periods_new_build_2zones_transmission_Tx1halfavailmonthly", objective
        )

    def test_example_test_cheap_fuel_blend(self):
        """
        Check validation and objective function value of "test_cheap_fuel_blend" example
        :return:
        """

        objective = -3796255594374.1226

        self.check_validation("test_cheap_fuel_blend")
        self.run_and_check_objective("test_cheap_fuel_blend", objective)

    def test_example_test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend" example
        :return:
        """

        self.check_validation(
            "test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend"
        )
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_tx_low_carbon_fuel_blend",
            -3504399050661.217,
        )

    def test_example_test_cheap_fuel_blend_w_limit(self):
        """
        Check validation and objective function value of
        "test_cheap_fuel_blend_w_limit" example
        :return:
        """

        objective = -3796282357926.1226

        self.check_validation("test_cheap_fuel_blend_w_limit")
        self.run_and_check_objective("test_cheap_fuel_blend_w_limit", objective)

    def test_example_test_new_solar_fuel_burn_limit(self):
        """
        Check validation and objective function value of
        "test_new_solar_fuel_burn_limit" example. Inputs set up so that this should
        be the same as the "test_new_solar_carbon_cap" example.
        :return:
        """

        self.check_validation("test_new_solar_fuel_burn_limit")
        self.run_and_check_objective(
            "test_new_solar_fuel_burn_limit", -58282515304521.79
        )

    def test_example_test_new_solar_fuel_burn_limit_relative(self):
        """
        Check validation and objective function value of
        "test_new_solar_fuel_burn_limit_relative" example. Inputs set up so that this
        should be the same as the "test_new_solar_fuel_burn_limit" example.
        :return:
        """

        self.check_validation("test_new_solar_fuel_burn_limit_relative")
        self.run_and_check_objective(
            "test_new_solar_fuel_burn_limit_relative", -58282515304521.79
        )

    def test_test_w_solver_options(self):
        """
        Check validation and objective function value of "test_w_solver_options" example
        :return:
        """

        self.check_validation("test_w_solver_options")
        self.run_and_check_objective("test_w_solver_options", -3796309121478.12)

    def test_example_test_carbon_tax_allowance_with_different_fuel_groups(self):
        """
        Check validation and objective function value of
        "test_carbon_tax_allowance_with_different_fuel_groups" example
        :return:
        """

        self.check_validation("test_carbon_tax_allowance_with_different_fuel_groups")
        self.run_and_check_objective(
            "test_carbon_tax_allowance_with_different_fuel_groups", -3796325179179.2686
        )

    def test_performance_standard(self):
        """
        Check validation and objective function value of "test_performance_standard" example
        :return:
        """

        self.check_validation("test_performance_standard")
        self.run_and_check_objective("test_performance_standard", -3592014754469.9077)

    def test_tx_flow(self):
        """
        Check validation and objective function value of
        "test_tx_flow" example
        :return:
        """

        self.check_validation("test_tx_flow")
        self.run_and_check_objective("test_tx_flow", -59124336744013.484)

    def test_example_test_new_solar_reserve_prj_contribution(self):
        """
        Check validation and objective function value of
        "test_reserve_prj_contribution" example.
        This example is based on "test_new_solar" with the only difference, the LF UP
        requirement ID
        :return:
        """

        self.check_validation("test_new_solar_reserve_prj_contribution")
        self.run_and_check_objective(
            "test_new_solar_reserve_prj_contribution", -3796311064738.0493
        )

    def test_test_new_solar_carbon_cap_2zones_tx_hydrogen_prod(self):
        """
        Check validation and objective function value of
        "test_reserve_prj_contribution" example.
        This example is based on "test_new_solar" with the only difference, the LF UP
        requirement ID
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_tx_hydrogen_prod")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_tx_hydrogen_prod", -186977669.6
        )

    def test_test_new_solar_carbon_cap_2zones_tx_hydrogen_prod_new(self):
        """
        Check validation and objective function value of
        "test_reserve_prj_contribution" example.
        This example is based on "test_new_solar" with the only difference, the LF UP
        requirement ID
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_2zones_tx_hydrogen_prod_new")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_2zones_tx_hydrogen_prod_new", -186998077.6
        )

    def test_example_test_new_solar_carbon_cap_dac(self):
        """
        Check validation and objective function value of
        "test_new_solar_carbon_cap_dac" example.

        Note that the same version of Cbc (v2.10.5) produces a slightly different
        objective function for this problem on Windows than on Mac.
        :return:
        """

        self.check_validation("test_new_solar_carbon_cap_dac")
        self.run_and_check_objective(
            "test_new_solar_carbon_cap_dac",
            -3504434601570.9893,
        )

    def test_example_test_cap_factor_limits(self):
        """
        Check validation and objective function value of "test" example
        :return:
        """

        self.check_validation("test_cap_factor_limits")
        self.run_and_check_objective("test_cap_factor_limits", -5373102109974.298)

    def test_example_multi_stage_prod_cost_w_markets(self):
        """
        Check validation and objective function values of
        "multi_stage_prod_cost_w_markets" example
        :return:
        """

        self.check_validation("multi_stage_prod_cost_w_markets")
        self.run_and_check_objective(
            "multi_stage_prod_cost_w_markets",
            {
                1: {
                    1: -1168100020726.1135,
                    2: -1168100283039.4688,
                    3: -1168100283039.5056,
                },
                2: {
                    1: -1168100035326.1135,
                    2: -1168100283039.4688,
                    3: -1168100283039.5056,
                },
                3: {
                    1: -1168100020726.1135,
                    2: -1168100283039.4688,
                    3: -1168100283039.5056,
                },
            },
        )

    def test_example_test_supplemental_firing(self):
        """
        Check validation and objective function value of "test_supplemental_firing" example
        :return:
        """

        self.check_validation("test_supplemental_firing")
        self.run_and_check_objective("test_supplemental_firing", -4380327039279.8545)

    def test_example_test_tx_capacity_groups(self):
        """
        Check validation and objective function value of
        "test_tx_capacity_groups" example
        :return:
        """

        self.check_validation("test_tx_capacity_groups")
        self.run_and_check_objective("test_tx_capacity_groups", -12284573611936.518)

    def test_example_2periods_new_build_fin_lifetime(self):
        """
        Check validation and objective function value of
        "2periods_new_build_fin_lifetime" example. Same as "2periods_new_build" but
        with shorter financial lifetimes and some fixed costs. Cost is lower because
        the same payment is made fewer times.
        """

        self.check_validation("2periods_new_build_fin_lifetime")
        self.run_and_check_objective(
            "2periods_new_build_fin_lifetime", -10022366566.861605
        )

    def test_example_2periods_new_build_cumulative_and_vintage_min_max(self):
        """
        Check validation and objective function value of
        "2periods_new_build_cumulative_and_vintage_min_max" example. It is the same
        as 2periods_new_build_cumulative_and_min_max but with a max in 2020 for the
        CCGT to force early build and a min on the CT in 2030 to force more build.

        :return:
        """

        self.check_validation("2periods_new_build_cumulative_and_vintage_min_max")
        self.run_and_check_objective(
            "2periods_new_build_cumulative_and_vintage_min_max", -110384972580606.39
        )

    def test_example_test_w_storage_w_soc_penalty(self):
        """
        Check validation and objective function value of "test_w_storage_w_soc_penalty"
        example
        :return:
        """

        self.check_validation("test_w_storage_w_soc_penalty")
        self.run_and_check_objective(
            "test_w_storage_w_soc_penalty", -245736137.55082923
        )

    def test_example_test_new_solar_itc(self):
        """
        Check validation and objective function value of
        "test_new_solar_itc" example
        :return:
        """

        self.check_validation("test_new_solar_itc")
        self.run_and_check_objective("test_new_solar_itc", -3796301348804.993)

    def test_example_test_new_build_storage_itc(self):
        """
        Check validation and objective function value of
        "test_new_build_storage" example
        :return:
        """

        self.check_validation("test_new_build_storage_itc")
        self.run_and_check_objective("test_new_build_storage_itc", -4484590199.92)

    def test_example_2periods_new_build_simple_prm_2loadzones(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm_2loadzones"
        example
        :return:
        """
        objective = -613211671721885.6
        self.check_validation("2periods_new_build_simple_prm_2loadzones")
        self.run_and_check_objective(
            "2periods_new_build_simple_prm_2loadzones", objective
        )

    def test_example_2periods_new_build_simple_prm_2loadzones_newtx_w_transfers(self):
        """
        Check validation and objective function value of
        "2periods_new_build_simple_prm_w_transfers"
        example
        :return:
        """
        objective = -17323444870.099785
        self.check_validation(
            "2periods_new_build_simple_prm_2loadzones_newtx_w_transfers"
        )
        self.run_and_check_objective(
            "2periods_new_build_simple_prm_2loadzones_newtx_w_transfers", objective
        )

    def test_example_test_period_tx_targets(self):
        """
        Check validation and objective function value of "test_w_storage_w_soc_penalty"
        example
        :return:
        """

        self.check_validation("test_period_tx_targets")
        self.run_and_check_objective("test_period_tx_targets", -58248345119704.586)

    @classmethod
    def tearDownClass(cls):
        os.remove(DB_PATH)
        for temp_file_ext in ["-shm", "-wal"]:
            temp_file = "{}{}".format(DB_PATH, temp_file_ext)
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()
