# Copyright 2026 Sylvan Energy Analytics LLC.
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

"""
Tests for the parallel E2E driver: argument handling and per-scenario
argument lists; the worker pool's handling of interruption and of a worker
that dies without reporting; and end-to-end runs against a scratch copy of
the examples database -- two scenarios solved in parallel and imported by
the single importer, and a run in which one scenario fails while the other
completes.
"""

import contextlib
import io
import os
import shutil
import sqlite3
import tempfile
import time
import unittest

from db import create_database
from db.common_functions import connect_to_database
from db.utilities import port_csvs_to_db, scenario
from gridpath import run_end_to_end_parallel

TESTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
REPO_DIRECTORY = os.path.join(TESTS_DIRECTORY, "..")
DB_SCHEMA = os.path.join(REPO_DIRECTORY, "db", "db_schema.sql")
DATA_DIRECTORY = os.path.join(REPO_DIRECTORY, "db", "data")
CSV_PATH = os.path.join(REPO_DIRECTORY, "db", "csvs_test_examples")
SCENARIOS_CSV = os.path.join(CSV_PATH, "scenarios.csv")
DB_TEMPLATE_ENV_VAR = "GRIDPATH_TEST_EXAMPLES_DB_TEMPLATE"

COMMON_ARGS = ["--database", "irrelevant.db", "--scenario_location", "irrelevant"]


def build_examples_database(db_path):
    """
    Build the examples database at db_path, from the pre-built template if
    the parallel test runner provides one, otherwise from the CSVs.
    """
    template_path = os.environ.get(DB_TEMPLATE_ENV_VAR)
    if template_path and os.path.exists(template_path):
        shutil.copyfile(template_path, db_path)
        return

    create_database.main(
        [
            "--database",
            db_path,
            "--db_schema",
            DB_SCHEMA,
            "--data_directory",
            DATA_DIRECTORY,
        ]
    )
    port_csvs_to_db.main(["--database", db_path, "--csv_location", CSV_PATH, "--quiet"])
    scenario.main(["--database", db_path, "--csv_path", SCENARIOS_CSV, "--quiet"])


def write_scenarios_csv(path, rows):
    with open(path, "w", newline="") as f:
        f.write("\n".join(",".join(row) for row in rows) + "\n")


class TestArguments(unittest.TestCase):
    def parse(self, args):
        return run_end_to_end_parallel.parse_arguments(args)

    def build(self, args):
        parsed_args, common_e2e_args = self.parse(args)
        return run_end_to_end_parallel.build_scenario_arg_lists(
            parsed_args=parsed_args, common_e2e_args=common_e2e_args
        )

    def assert_parser_rejects(self, args):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.parse(args)

    def test_n_parallel_scenarios_required_and_positive(self):
        self.assert_parser_rejects(["--scenarios", "a"] + COMMON_ARGS)
        self.assert_parser_rejects(
            ["--scenarios", "a", "--n_parallel_scenarios", "0"] + COMMON_ARGS
        )

    def test_scenarios_required(self):
        self.assert_parser_rejects(["--n_parallel_scenarios", "2"] + COMMON_ARGS)

    def test_scenario_arg_lists_from_names(self):
        arg_lists = self.build(
            ["--scenarios", "a", "b", "--n_parallel_scenarios", "2"]
            + COMMON_ARGS
            + ["--log", "--n_parallel_solve", "3"]
        )
        self.assertEqual(
            arg_lists,
            [
                (
                    "a",
                    COMMON_ARGS
                    + ["--log", "--n_parallel_solve", "3", "--scenario", "a"],
                ),
                (
                    "b",
                    COMMON_ARGS
                    + ["--log", "--n_parallel_solve", "3", "--scenario", "b"],
                ),
            ],
        )

    def test_scenario_arg_lists_from_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, "scenarios.csv")
            write_scenarios_csv(
                csv_path,
                [
                    ["scenario", "b", "c"],
                    ["scenario_location", "/loc/b", "/loc/c"],
                    ["mute_solver_output", "", ""],
                    [],
                ],
            )
            arg_lists = self.build(
                [
                    "--scenarios",
                    "a",
                    "--scenarios_csv",
                    csv_path,
                    "--n_parallel_scenarios",
                    "2",
                    "--database",
                    "irrelevant.db",
                ]
            )
        self.assertEqual(
            arg_lists,
            [
                ("a", ["--database", "irrelevant.db", "--scenario", "a"]),
                (
                    "b",
                    [
                        "--database",
                        "irrelevant.db",
                        "--scenario",
                        "b",
                        "--scenario_location",
                        "/loc/b",
                        "--mute_solver_output",
                    ],
                ),
                (
                    "c",
                    [
                        "--database",
                        "irrelevant.db",
                        "--scenario",
                        "c",
                        "--scenario_location",
                        "/loc/c",
                        "--mute_solver_output",
                    ],
                ),
            ],
        )

    def test_csv_may_not_set_database_or_scenario(self):
        for option in ["database", "scenario", "scenario_id"]:
            with self.subTest(option=option):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    csv_path = os.path.join(tmp_dir, "scenarios.csv")
                    write_scenarios_csv(
                        csv_path, [["scenario", "a"], [option, "something"]]
                    )
                    with self.assertRaises(ValueError):
                        self.build(
                            ["--scenarios_csv", csv_path, "--n_parallel_scenarios", "1"]
                            + COMMON_ARGS
                        )

    def test_common_args_may_not_select_a_scenario(self):
        for selection in [["--scenario", "a"], ["--scenario_id", "1"]]:
            with self.subTest(selection=selection):
                with self.assertRaises(ValueError):
                    self.build(
                        ["--scenarios", "a", "--n_parallel_scenarios", "1"]
                        + COMMON_ARGS
                        + selection
                    )

    def test_duplicate_scenarios_rejected(self):
        with self.assertRaises(ValueError):
            self.build(["--scenarios", "a", "a", "--n_parallel_scenarios", "1"])

    def test_unsupported_e2e_modes_rejected(self):
        for mode in [
            ["--per_draw_lifecycle"],
            ["--single_e2e_step_only", "get_inputs"],
        ]:
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    self.build(
                        ["--scenarios", "a", "--n_parallel_scenarios", "1"]
                        + COMMON_ARGS
                        + mode
                    )

    def test_bad_e2e_option_rejected_up_front(self):
        # Validated with gridpath_run_e2e's own (strict) parser, naming the
        # scenario
        with self.assertRaises(ValueError) as context:
            self.build(
                ["--scenarios", "a", "--n_parallel_scenarios", "1"]
                + COMMON_ARGS
                + ["--no_such_option"]
            )
        self.assertIn("scenario a", str(context.exception))
        self.assertIn("--no_such_option", str(context.exception))

    def test_e2e_flag_combination_rules_apply(self):
        # Cleanup needs the import statuses, as in gridpath_run_e2e
        with self.assertRaises(ValueError):
            self.build(
                ["--scenarios", "a", "--n_parallel_scenarios", "1"]
                + COMMON_ARGS
                + ["--cleanup_after_import", "--skip_import_results"]
            )


# Worker targets for the pool tests (module-level, so the spawned worker
# processes can import them)
def reporting_worker(scenario_name, e2e_args, result_queue):
    record = run_end_to_end_parallel.SolveStageRecord(
        scenario_name=scenario_name, process_id=os.getpid(), start_time=None
    )
    record.success = True
    result_queue.put(record)


def sleeping_worker(scenario_name, e2e_args, result_queue):
    time.sleep(60)


def dying_worker(scenario_name, e2e_args, result_queue):
    os._exit(7)


def worker_by_scenario(scenario_name, e2e_args, result_queue):
    # The scenario name's prefix picks the behavior: fast_1, slow_2, dies_1
    {"fast": reporting_worker, "slow": sleeping_worker, "dies": dying_worker}[
        scenario_name.split("_")[0]
    ](scenario_name, e2e_args, result_queue)


class TestSolveStagePool(unittest.TestCase):
    def run_pool(self, scenario_names, n_parallel, on_solved):
        stopped = []
        run_end_to_end_parallel.run_solve_stages(
            scenario_arg_lists=[(name, []) for name in scenario_names],
            n_parallel_scenarios=n_parallel,
            on_solved=on_solved,
            on_stopped=stopped.extend,
            worker_target=worker_by_scenario,
            poll_interval_seconds=0.2,
        )
        return stopped

    def test_results_are_handled_as_workers_finish(self):
        solved = []
        self.run_pool(
            ["fast_1", "fast_2", "fast_3"], 2, lambda record: solved.append(record)
        )
        self.assertEqual(
            sorted(r.scenario_name for r in solved), ["fast_1", "fast_2", "fast_3"]
        )
        self.assertTrue(all(r.success for r in solved))

    def test_dead_worker_gets_a_failure_record(self):
        solved = []
        self.run_pool(["dies_1", "fast_1"], 2, lambda record: solved.append(record))
        by_name = {r.scenario_name: r for r in solved}
        self.assertTrue(by_name["fast_1"].success)
        self.assertFalse(by_name["dies_1"].success)
        self.assertFalse(by_name["dies_1"].run_end_recorded)
        self.assertIn("exited with code 7", by_name["dies_1"].error)

    def test_interruption_terminates_running_workers(self):
        """
        An exception while handling a result (standing in for Ctrl-C or the
        SIGTERM handler's SystemExit) terminates the worker still running,
        reports its scenario as stopped, and never starts the pending one.
        """

        def interrupt(record):
            raise KeyboardInterrupt

        stopped = []
        start = time.time()
        with self.assertRaises(KeyboardInterrupt):
            run_end_to_end_parallel.run_solve_stages(
                scenario_arg_lists=[("fast_1", []), ("slow_1", []), ("slow_2", [])],
                n_parallel_scenarios=2,
                on_solved=interrupt,
                on_stopped=stopped.extend,
                worker_target=worker_by_scenario,
                poll_interval_seconds=0.2,
            )
        # Only the running sleeper was stopped; the pending one never started
        self.assertEqual(stopped, ["slow_1"])
        # The sleeper was terminated, not waited for (it sleeps 60 s)
        self.assertLess(time.time() - start, 30)


class TestParallelEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.class_tmp_dir = tempfile.TemporaryDirectory()
        cls.template_db_path = os.path.join(cls.class_tmp_dir.name, "examples.db")
        build_examples_database(cls.template_db_path)

    @classmethod
    def tearDownClass(cls):
        cls.class_tmp_dir.cleanup()

    def setUp(self):
        # A fresh scratch copy of the database and scenario location per test
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.db_path = os.path.join(self.tmp_dir.name, "test.db")
        shutil.copyfile(self.template_db_path, self.db_path)
        # Start from rollback-journal mode (the examples database is built
        # in WAL mode), so that the run's switch to WAL and back is observable
        conn = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                conn.execute("PRAGMA journal_mode=delete;").fetchone()[0], "delete"
            )
        finally:
            conn.close()
        self.scenario_location = os.path.join(self.tmp_dir.name, "scenarios")

    def common_args(self):
        return [
            "--database",
            self.db_path,
            "--scenario_location",
            self.scenario_location,
            "--quiet",
            "--mute_solver_output",
        ]

    def query(self, sql, params=()):
        conn = connect_to_database(db_path=self.db_path)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def get_run_status(self, scenario_name):
        return self.query(
            "SELECT run_status_id FROM scenarios WHERE scenario_name = ?;",
            (scenario_name,),
        )[0][0]

    def get_steps_timed(self, scenario_name):
        return sorted(
            row[0]
            for row in self.query(
                "SELECT e2e_step FROM status_e2e_step_timings "
                "JOIN scenarios USING (scenario_id) WHERE scenario_name = ?;",
                (scenario_name,),
            )
        )

    def get_objective(self, scenario_name):
        rows = self.query(
            "SELECT objective_function_value FROM results_scenario "
            "JOIN scenarios USING (scenario_id) WHERE scenario_name = ?;",
            (scenario_name,),
        )
        return rows[0][0] if rows else None

    def get_journal_mode(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("PRAGMA journal_mode;").fetchone()[0]
        finally:
            conn.close()

    def test_two_scenarios_in_parallel(self):
        """
        Both scenarios solve, both are imported by the single importer and
        marked complete with every step timed, and the database is returned
        to its prior journal mode.
        """
        scenario_names = ["test", "test_w_hydro"]
        run_end_to_end_parallel.main(
            ["--scenarios"]
            + scenario_names
            + ["--n_parallel_scenarios", "2", "--log"]
            + self.common_args()
        )

        for scenario_name in scenario_names:
            with self.subTest(scenario=scenario_name):
                self.assertEqual(self.get_run_status(scenario_name), 2)
                self.assertIsNotNone(self.get_objective(scenario_name))
                self.assertEqual(
                    self.get_steps_timed(scenario_name),
                    ["get_inputs", "import_results", "process_results", "run_scenario"],
                )
                # One E2E log per scenario, carrying both stages
                logs_directory = os.path.join(
                    self.scenario_location, scenario_name, "logs"
                )
                # (run_scenario writes its own opt_*.log alongside)
                log_files = [
                    f
                    for f in os.listdir(logs_directory)
                    if f.startswith("e2e_") and f.endswith(".log")
                ]
                self.assertEqual(len(log_files), 1, log_files)
                timing_summaries = [
                    f
                    for f in os.listdir(logs_directory)
                    if f.startswith("e2e_timing_summary")
                ]
                self.assertEqual(len(timing_summaries), 1)
                with open(os.path.join(logs_directory, timing_summaries[0])) as f:
                    summary = f.read()
                self.assertEqual(summary.count("E2E timing summary:"), 1)
                for step in ["get_inputs", "run_scenario", "import_results"]:
                    self.assertIn(step, summary)
                self.assertIn("total run time", summary)
        self.assertEqual(self.get_journal_mode(), "delete")
        # Leaving WAL mode checkpoints and deletes the -wal sidecar
        self.assertFalse(os.path.exists(f"{self.db_path}-wal"))

    def test_failed_scenario_does_not_stop_the_others(self):
        """
        One scenario's solve stage fails (its scenario location is under a
        regular file); it is marked run_error, the other scenario completes,
        and the driver exits with status 1.
        """
        not_a_directory = os.path.join(self.tmp_dir.name, "not_a_directory.txt")
        with open(not_a_directory, "w") as f:
            f.write("")
        csv_path = os.path.join(self.tmp_dir.name, "scenarios.csv")
        write_scenarios_csv(
            csv_path,
            [
                ["scenario", "test", "test_w_hydro"],
                [
                    "scenario_location",
                    self.scenario_location,
                    os.path.join(not_a_directory, "scenarios"),
                ],
            ],
        )

        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as context:
                run_end_to_end_parallel.main(
                    [
                        "--scenarios_csv",
                        csv_path,
                        "--n_parallel_scenarios",
                        "2",
                        "--database",
                        self.db_path,
                        "--quiet",
                        "--mute_solver_output",
                    ]
                )
        self.assertEqual(context.exception.code, 1)
        self.assertIn("test_w_hydro", stderr.getvalue())

        self.assertEqual(self.get_run_status("test"), 2)
        self.assertIsNotNone(self.get_objective("test"))
        self.assertEqual(self.get_run_status("test_w_hydro"), 3)
        self.assertIsNone(self.get_objective("test_w_hydro"))
        self.assertEqual(self.get_journal_mode(), "delete")


if __name__ == "__main__":
    unittest.main()
