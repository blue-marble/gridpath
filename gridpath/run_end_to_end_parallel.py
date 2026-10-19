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
Parallel gridpath_run_e2e: run several scenarios end to end against one
database, solving up to N scenarios at a time with a single results importer.

SQLite allows one writer at a time, and a scenario's results import holds
the write lock for minutes, so independent gridpath_run_e2e processes
sharing a database trip over each other at the import step. This driver
splits the pipeline instead: worker processes run the get_inputs and
run_scenario steps (database reads plus small run-status writes), and the
driver process is the only results importer -- it imports and processes each
scenario's results as that scenario finishes solving, while the remaining
scenarios keep solving. The database is switched to WAL journal mode for
the run so the workers' input queries are not blocked by an import in
progress (WAL mode is not supported on network file systems).

Usage::

    gridpath_run_e2e_parallel --database /PATH/TO/DATABASE
    --scenario_location /PATH/TO/SCENARIOS --scenarios base high_load
    --n_parallel_scenarios 2 [gridpath_run_e2e options]

Every argument other than ``--scenarios``, ``--scenarios_csv`` and
``--n_parallel_scenarios`` is a gridpath_run_e2e argument applied to every
scenario (e.g. ``--log``, ``--quiet``, ``--n_parallel_solve``,
``--cleanup_after_import``). Options that differ by scenario go in a CSV
passed with ``--scenarios_csv``, in the gridpath_run_parallel format (see
:func:`gridpath.run_scenario_parallel.read_scenarios_csv`); its scenarios
are run in addition to any passed with ``--scenarios``. The database is set
once for the whole run, so the CSV may not carry a ``database`` row.

Each scenario gets the same run-status bookkeeping as gridpath_run_e2e: its
run status, process ID (the worker's), start/end times and per-step timings
are recorded in the database, and ``--log`` writes the scenario's E2E log
file (all steps, including the import stage run by the driver). A scenario
whose solve or import fails is marked ``run_error`` and the run continues
with the others; the driver exits with status 1 if any scenario failed. On
Ctrl-C or SIGTERM, the worker processes still solving are terminated and
their scenarios marked ``run_stopped``; scenarios not yet started are left
as they were.

Not supported here: ``--per_draw_lifecycle`` (its per-scenario importer
thread would be a second database writer) and ``--single_e2e_step_only``.
``--skip_*`` step flags are honored (``--skip_import_results`` is rejected
with cleanup/archiving, as in gridpath_run_e2e).
"""

from argparse import ArgumentParser
import contextlib
import datetime
import io
import logging
from multiprocessing import get_context
import os
import queue
import signal
import sys
import threading

from db.common_functions import connect_to_database
from gridpath import (
    get_scenario_inputs,
    import_scenario_results,
    process_results,
    run_end_to_end,
    run_scenario,
)
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from gridpath.common_functions import determine_scenario_directory, get_version_parser
from gridpath.run_end_to_end import (
    check_if_in_queue,
    clear_step_timings_in_db,
    record_process_id_and_start_time,
    record_step_timing,
    remove_from_queue_if_in_queue,
    start_e2e_logging,
    stop_e2e_logging,
    update_db_for_run_end,
    update_run_status,
)
from gridpath.run_end_to_end_per_draw import (
    restore_journal_mode,
    set_wal_journal_mode,
)
from gridpath.run_scenario_parallel import read_scenarios_csv
from gridpath.scenario_directory_cleanup import cleanup_scenario_directory_for_run

# Run status IDs (see mod_run_status_types)
RUN_STATUS_RUNNING = 1
RUN_STATUS_COMPLETE = 2
RUN_STATUS_RUN_ERROR = 3
RUN_STATUS_RUN_STOPPED = 4

# gridpath_run_e2e arguments that this driver manages itself and therefore
# refuses as common or per-scenario arguments
SCENARIO_SELECTION_ARGUMENTS = ("--scenario", "--scenario_id")


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: (parsed driver arguments, list of the remaining arguments, which
        are gridpath_run_e2e arguments common to every scenario)
    """
    # No prefix matching: --scenario (a gridpath_run_e2e argument this driver
    # refuses) must not be read as an abbreviation of --scenarios
    parser = ArgumentParser(
        add_help=True,
        allow_abbrev=False,
        parents=[get_version_parser()],
        description="Run several scenarios end to end, solving up to "
        "--n_parallel_scenarios of them at a time and importing results "
        "into the database one scenario at a time.",
        epilog="All other arguments are passed to gridpath_run_e2e for every "
        "scenario; see 'gridpath_run_e2e --help' for them. Pass at least "
        "--database and --scenario_location.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        metavar="SCENARIO",
        help="The names of the scenarios to run.",
    )
    parser.add_argument(
        "--scenarios_csv",
        help="A CSV of scenarios to run with per-scenario gridpath_run_e2e "
        "options (scenario names across the top row after 'scenario'; one "
        "row per option below, an empty cell meaning a bare flag). These "
        "scenarios are run in addition to any passed with --scenarios.",
    )
    parser.add_argument(
        "--n_parallel_scenarios",
        type=int,
        required=True,
        help="Run the get_inputs and run_scenario steps of up to this many "
        "scenarios at once (results imports are always one at a time). "
        "Memory per solve is usually the limit.",
    )

    parsed_arguments, common_e2e_args = parser.parse_known_args(args=args)

    if parsed_arguments.n_parallel_scenarios < 1:
        parser.error("--n_parallel_scenarios must be at least 1.")
    if parsed_arguments.scenarios is None and parsed_arguments.scenarios_csv is None:
        parser.error(
            "Specify the scenarios to run with --scenarios and/or " "--scenarios_csv."
        )

    return parsed_arguments, common_e2e_args


def parse_e2e_arguments(scenario_name, e2e_args):
    """
    :param scenario_name: the scenario the arguments are for (for the error
        message)
    :param e2e_args: a gridpath_run_e2e argument list
    :return: run_end_to_end's parsed arguments
    :raises ValueError: if gridpath_run_e2e's parser rejects the arguments,
        or they select a mode this driver does not support

    Validate a scenario's gridpath_run_e2e arguments with run_end_to_end's
    own parser (which is strict about unknown options and flag combinations)
    before anything is started.
    """
    argparse_messages = io.StringIO()
    try:
        with contextlib.redirect_stderr(argparse_messages):
            parsed_e2e_args = run_end_to_end.parse_arguments(e2e_args)
    except SystemExit:
        raise ValueError(
            f"Invalid gridpath_run_e2e arguments for scenario {scenario_name}: "
            f"{argparse_messages.getvalue().strip()}"
        )

    if parsed_e2e_args.per_draw_lifecycle:
        raise ValueError(
            "--per_draw_lifecycle runs its own results importer for each "
            "scenario and cannot be combined with parallel scenarios; run "
            "per-draw scenarios one at a time with gridpath_run_e2e."
        )
    if parsed_e2e_args.single_e2e_step_only is not None:
        raise ValueError(
            "--single_e2e_step_only is not supported with parallel scenarios; "
            "use the --skip_* flags instead."
        )

    return parsed_e2e_args


def build_scenario_arg_lists(parsed_args, common_e2e_args):
    """
    :param parsed_args: this driver's parsed arguments
    :param common_e2e_args: the gridpath_run_e2e arguments common to every
        scenario
    :return: list of (scenario_name, e2e_args) tuples, one gridpath_run_e2e
        argument list per scenario: the common arguments, then --scenario,
        then the scenario's options from the CSV (if any)

    The scenarios from --scenarios come first, then those from
    --scenarios_csv. Every argument list is validated with
    gridpath_run_e2e's parser, so a bad option fails before any scenario
    starts.
    """
    for argument in common_e2e_args:
        if argument in SCENARIO_SELECTION_ARGUMENTS or argument.startswith(
            tuple(f"{a}=" for a in SCENARIO_SELECTION_ARGUMENTS)
        ):
            raise ValueError(
                f"Pass the scenarios to run with --scenarios or --scenarios_csv, "
                f"not {argument}."
            )

    scenarios = []
    if parsed_args.scenarios is not None:
        scenarios.extend((scenario_name, []) for scenario_name in parsed_args.scenarios)
    if parsed_args.scenarios_csv is not None:
        scenarios.extend(read_scenarios_csv(parsed_args.scenarios_csv))

    scenario_names = [scenario_name for scenario_name, _ in scenarios]
    duplicates = sorted(
        {name for name in scenario_names if scenario_names.count(name) > 1}
    )
    if duplicates:
        raise ValueError(
            f"Each scenario can be run once per invocation; duplicated: "
            f"{', '.join(duplicates)}."
        )

    scenario_arg_lists = []
    for scenario_name, scenario_args in scenarios:
        for argument in scenario_args:
            if argument == "--database":
                raise ValueError(
                    f"The scenarios CSV sets 'database' for scenario "
                    f"{scenario_name}; the database is set once for the whole "
                    f"run with --database."
                )
            if argument in SCENARIO_SELECTION_ARGUMENTS:
                raise ValueError(
                    f"The scenarios CSV sets '{argument[2:]}' for scenario "
                    f"{scenario_name}; scenario names come from the CSV's top "
                    f"row."
                )
        e2e_args = list(common_e2e_args) + ["--scenario", scenario_name] + scenario_args
        parse_e2e_arguments(scenario_name=scenario_name, e2e_args=e2e_args)
        scenario_arg_lists.append((scenario_name, e2e_args))

    return scenario_arg_lists


class SolveStageRecord(object):
    """
    What a worker reports back to the driver about a scenario's solve stage:
    the run bookkeeping the import stage continues (process ID, start time,
    queue position, timing summary file) and whether the stage succeeded.
    """

    def __init__(self, scenario_name, process_id, start_time):
        self.scenario_name = scenario_name
        self.process_id = process_id
        self.start_time = start_time
        self.scenario_id = None
        self.queue_order_id = None
        self.timing_summary_file_path = None
        self.success = False
        self.error = None
        # Whether the worker recorded the run's end (status, end time) in
        # the database; False for a record synthesized by the driver for a
        # worker that died without reporting
        self.run_end_recorded = False


def run_solve_stage(scenario_name, e2e_args):
    """
    :param scenario_name:
    :param e2e_args: the scenario's gridpath_run_e2e argument list
    :return: a SolveStageRecord

    The worker-process body: the get_inputs and run_scenario steps for one
    scenario, with gridpath_run_e2e's run-status bookkeeping and logging.
    Never raises: a failure marks the scenario run_error and is reported in
    the returned record, so one scenario's failure doesn't stop the others.
    """
    process_id = os.getpid()
    start_time = datetime.datetime.now()
    record = SolveStageRecord(
        scenario_name=scenario_name, process_id=process_id, start_time=start_time
    )

    parsed_e2e_args = run_end_to_end.parse_arguments(e2e_args)
    db_path = parsed_e2e_args.database
    quiet = parsed_e2e_args.quiet
    scenario_directory = determine_scenario_directory(
        scenario_location=parsed_e2e_args.scenario_location,
        scenario_name=scenario_name,
    )

    e2e_logging = None
    try:
        if parsed_e2e_args.log:
            e2e_logging = start_e2e_logging(
                scenario_directory=scenario_directory,
                start_time=start_time,
                process_id=process_id,
            )
            record.timing_summary_file_path = e2e_logging.timing_summary_file_path

        conn = connect_to_database(db_path=db_path)
        try:
            scenario_id, scenario_name = get_scenario_id_and_name(
                scenario_id_arg=None,
                scenario_name_arg=scenario_name,
                c=conn.cursor(),
                script="run_end_to_end_parallel",
            )
        finally:
            conn.close()
        record.scenario_id = scenario_id

        if not quiet:
            print(
                f"Running scenario {scenario_name}: get_inputs and run_scenario "
                f"(process ID {process_id}, started on {start_time})"
            )

        record.queue_order_id = check_if_in_queue(db_path, scenario_name)
        update_run_status(db_path, scenario_name, RUN_STATUS_RUNNING)
        record_process_id_and_start_time(db_path, scenario_name, process_id, start_time)
        clear_step_timings_in_db(db_path=db_path, scenario_id=scenario_id)

        if not parsed_e2e_args.skip_get_inputs:
            step_start_time = datetime.datetime.now()
            get_scenario_inputs.main(args=e2e_args)
            record_step_timing(
                db_path=db_path,
                scenario_id=scenario_id,
                process_id=process_id,
                step="get_inputs",
                step_start_time=step_start_time,
                timing_summary_file_path=record.timing_summary_file_path,
                quiet=quiet,
            )

        if not parsed_e2e_args.skip_run_scenario:
            step_start_time = datetime.datetime.now()
            run_scenario.main(args=e2e_args)
            record_step_timing(
                db_path=db_path,
                scenario_id=scenario_id,
                process_id=process_id,
                step="run_scenario",
                step_start_time=step_start_time,
                timing_summary_file_path=record.timing_summary_file_path,
                quiet=quiet,
            )

        record.success = True
    except Exception as e:
        logging.exception(e)
        record.error = f"{type(e).__name__}: {e}"
        if record.scenario_id is not None:
            end_time = update_db_for_run_end(
                db_path=db_path,
                scenario=scenario_name,
                queue_order_id=record.queue_order_id,
                process_id=process_id,
                run_status_id=RUN_STATUS_RUN_ERROR,
                start_time=start_time,
                timing_summary_file_path=record.timing_summary_file_path,
            )
            record.run_end_recorded = True
            print(
                f"Error encountered when getting inputs for or running scenario "
                f"{scenario_name}. End time: {end_time}. Total run time: "
                f"{end_time - start_time}."
            )
    finally:
        if e2e_logging is not None:
            stop_e2e_logging(e2e_logging)

    return record


def run_import_stage(record, e2e_args):
    """
    :param record: the scenario's SolveStageRecord (a successful one)
    :param e2e_args: the scenario's gridpath_run_e2e argument list
    :return: True if the stage succeeded, False otherwise

    The driver-process body for one solved scenario: import its results,
    process them, clean up/archive the scenario directory if requested, and
    mark the run complete (or run_error on failure). Steps are recorded
    under the solve stage's process ID so the run's timings and log file
    are in one place.
    """
    parsed_e2e_args = run_end_to_end.parse_arguments(e2e_args)
    db_path = parsed_e2e_args.database
    quiet = parsed_e2e_args.quiet
    scenario_name = record.scenario_name
    scenario_directory = determine_scenario_directory(
        scenario_location=parsed_e2e_args.scenario_location,
        scenario_name=scenario_name,
    )

    e2e_logging = None
    try:
        if parsed_e2e_args.log:
            # Append to the log and timing summary the worker started
            e2e_logging = start_e2e_logging(
                scenario_directory=scenario_directory,
                start_time=record.start_time,
                process_id=record.process_id,
                new_summary=False,
            )

        import_statuses = None
        if not parsed_e2e_args.skip_import_results:
            step_start_time = datetime.datetime.now()
            import_statuses = import_scenario_results.main(args=e2e_args)
            record_step_timing(
                db_path=db_path,
                scenario_id=record.scenario_id,
                process_id=record.process_id,
                step="import_results",
                step_start_time=step_start_time,
                timing_summary_file_path=record.timing_summary_file_path,
                quiet=quiet,
            )

        if not parsed_e2e_args.skip_process_results:
            step_start_time = datetime.datetime.now()
            process_results.main(args=e2e_args)
            record_step_timing(
                db_path=db_path,
                scenario_id=record.scenario_id,
                process_id=record.process_id,
                step="process_results",
                step_start_time=step_start_time,
                timing_summary_file_path=record.timing_summary_file_path,
                quiet=quiet,
            )

        if (
            parsed_e2e_args.cleanup_after_import
            or parsed_e2e_args.archive_after_import is not None
        ):
            step_start_time = datetime.datetime.now()
            cleanup_scenario_directory_for_run(
                db_path=db_path,
                scenario_id_arg=None,
                scenario_name_arg=scenario_name,
                scenario_location=parsed_e2e_args.scenario_location,
                import_statuses=import_statuses,
                archive_format=parsed_e2e_args.archive_after_import,
                quiet=quiet,
                temporal_structure_csv_overwrite=(
                    parsed_e2e_args.temporal_structure_csv_overwrite
                ),
                temporal_structure_csv_path=parsed_e2e_args.temporal_structure_csv_path,
                granularity=parsed_e2e_args.cleanup_granularity,
            )
            record_step_timing(
                db_path=db_path,
                scenario_id=record.scenario_id,
                process_id=record.process_id,
                step="cleanup_after_import",
                step_start_time=step_start_time,
                timing_summary_file_path=record.timing_summary_file_path,
                quiet=quiet,
            )

        end_time = update_db_for_run_end(
            db_path=db_path,
            scenario=scenario_name,
            queue_order_id=record.queue_order_id,
            process_id=record.process_id,
            run_status_id=RUN_STATUS_COMPLETE,
            start_time=record.start_time,
            timing_summary_file_path=record.timing_summary_file_path,
        )
        if not quiet:
            print(
                f"Scenario {scenario_name} done. Run finished on {end_time}. "
                f"Total run time: {end_time - record.start_time}."
            )
        return True
    except Exception as e:
        logging.exception(e)
        end_time = update_db_for_run_end(
            db_path=db_path,
            scenario=scenario_name,
            queue_order_id=record.queue_order_id,
            process_id=record.process_id,
            run_status_id=RUN_STATUS_RUN_ERROR,
            start_time=record.start_time,
            timing_summary_file_path=record.timing_summary_file_path,
        )
        print(
            f"Error encountered when importing or processing results for "
            f"scenario {scenario_name}. End time: {end_time}. Total run time: "
            f"{end_time - record.start_time}."
        )
        return False
    finally:
        if e2e_logging is not None:
            stop_e2e_logging(e2e_logging)


def _exit_on_sigterm(signum, frame):
    """
    Turn SIGTERM into a SystemExit so that cleanup runs: in the driver,
    terminating the workers and marking their scenarios stopped; in a
    worker, its finally blocks and multiprocessing's exit handler (which
    terminates any --n_parallel_solve pool it started).
    """
    raise SystemExit(
        f"SIGTERM received by run_end_to_end_parallel (PID {os.getpid()})."
    )


def solve_stage_worker(scenario_name, e2e_args, result_queue):
    """
    :param scenario_name:
    :param e2e_args: the scenario's gridpath_run_e2e argument list
    :param result_queue: the queue the SolveStageRecord is reported on

    The worker process's entry point: run the solve stage and report its
    record to the driver.
    """
    signal.signal(signal.SIGTERM, _exit_on_sigterm)
    result_queue.put(run_solve_stage(scenario_name=scenario_name, e2e_args=e2e_args))


def run_solve_stages(
    scenario_arg_lists,
    n_parallel_scenarios,
    on_solved,
    on_stopped,
    worker_target=solve_stage_worker,
    poll_interval_seconds=1,
):
    """
    :param scenario_arg_lists: list of (scenario_name, e2e_args) tuples
    :param n_parallel_scenarios: how many worker processes to run at once
    :param on_solved: called in this process with each scenario's
        SolveStageRecord as its worker finishes (the import stage)
    :param on_stopped: called with the names of the scenarios whose workers
        were terminated because this function was interrupted
    :param worker_target: the worker process target, taking
        (scenario_name, e2e_args, result_queue); the default runs the solve
        stage (a parameter for tests)
    :param poll_interval_seconds: how often to check for dead workers while
        waiting for a result

    Run the scenarios' solve stages in up to n_parallel_scenarios worker
    processes (spawned, non-daemonic, so a scenario's own
    --n_parallel_solve pool works inside them), starting the next scenario
    as soon as a worker frees up. A worker that dies without reporting a
    record (killed, crashed) gets a failure record synthesized for it.

    On an exception -- Ctrl-C, the SIGTERM handler's SystemExit, an error
    raised by on_solved -- the running workers are terminated and joined,
    on_stopped is called with their scenarios, and the exception is
    re-raised; scenarios not yet started are never started.
    """
    context = get_context("spawn")
    result_queue = context.Queue()
    pending = list(scenario_arg_lists)
    running = {}  # scenario name -> worker Process
    try:
        while pending or running:
            while pending and len(running) < n_parallel_scenarios:
                scenario_name, e2e_args = pending.pop(0)
                worker = context.Process(
                    target=worker_target,
                    args=(scenario_name, e2e_args, result_queue),
                    name=f"gridpath-e2e-{scenario_name}",
                )
                worker.start()
                running[scenario_name] = worker

            try:
                record = result_queue.get(timeout=poll_interval_seconds)
            except queue.Empty:
                # No result yet. A worker that has exited either reported
                # its record (flushed to the queue before it exited) or died
                # without one (killed, crashed): synthesize a failure record
                # for the latter
                dead = [
                    scenario_name
                    for scenario_name, worker in running.items()
                    if not worker.is_alive()
                ]
                if not dead:
                    continue
                try:
                    record = result_queue.get(timeout=poll_interval_seconds)
                except queue.Empty:
                    scenario_name = dead[0]
                    worker = running[scenario_name]
                    record = SolveStageRecord(
                        scenario_name=scenario_name,
                        process_id=worker.pid,
                        start_time=None,
                    )
                    record.error = (
                        f"worker process {worker.pid} exited with code "
                        f"{worker.exitcode} without reporting a result"
                    )

            worker = running.pop(record.scenario_name)
            worker.join()
            on_solved(record)
    except BaseException:
        for worker in running.values():
            worker.terminate()
        for worker in running.values():
            worker.join()
        if running:
            on_stopped(list(running))
        raise


def mark_scenarios_stopped(db_path, scenario_names, quiet):
    """
    :param db_path:
    :param scenario_names: the scenarios whose workers were terminated
    :param quiet:

    Mark the scenarios run_stopped (and drop them from the run queue if
    they were in it), as gridpath_run_e2e does when it is terminated.
    """
    for scenario_name in scenario_names:
        if not quiet:
            print(f"Stopped scenario {scenario_name}.")
        queue_order_id = check_if_in_queue(db_path, scenario_name)
        remove_from_queue_if_in_queue(db_path, scenario_name, queue_order_id)
        update_run_status(db_path, scenario_name, RUN_STATUS_RUN_STOPPED)


def main(args=None):
    """
    :param args: the argument list (sys.argv[1:] if None)

    Run the scenarios: solve stages in worker processes, import stages in
    this process as scenarios finish solving. Exits with status 1 if any
    scenario failed.
    """
    if args is None:
        args = sys.argv[1:]

    parsed_args, common_e2e_args = parse_arguments(args)
    scenario_arg_lists = build_scenario_arg_lists(
        parsed_args=parsed_args, common_e2e_args=common_e2e_args
    )
    e2e_args_by_scenario = dict(scenario_arg_lists)

    # Run-wide settings are the same in every scenario's argument list
    first_parsed_e2e_args = run_end_to_end.parse_arguments(scenario_arg_lists[0][1])
    db_path = first_parsed_e2e_args.database
    quiet = first_parsed_e2e_args.quiet
    n_parallel_scenarios = min(
        parsed_args.n_parallel_scenarios, len(scenario_arg_lists)
    )

    if not quiet:
        print(
            f"Running {len(scenario_arg_lists)} scenario(s) end to end, "
            f"{n_parallel_scenarios} at a time, started on "
            f"{datetime.datetime.now()} (database {db_path})"
        )

    completed_scenarios = []
    failed_scenarios = []

    def on_solved(record):
        scenario_name = record.scenario_name
        if not record.success:
            failed_scenarios.append((scenario_name, record.error))
            if not record.run_end_recorded:
                update_run_status(db_path, scenario_name, RUN_STATUS_RUN_ERROR)
            print(
                f"Scenario {scenario_name} failed before its results could be "
                f"imported: {record.error}",
                file=sys.stderr,
            )
            return

        if not quiet:
            print(f"Scenario {scenario_name} solved; importing results.")
        if run_import_stage(
            record=record, e2e_args=e2e_args_by_scenario[scenario_name]
        ):
            completed_scenarios.append(scenario_name)
        else:
            failed_scenarios.append((scenario_name, "results import/processing failed"))

    def on_stopped(scenario_names):
        mark_scenarios_stopped(
            db_path=db_path, scenario_names=scenario_names, quiet=quiet
        )

    # SIGTERM would otherwise kill this process without stopping the
    # workers (only in the main thread, where signal handlers can be set)
    prior_sigterm_handler = None
    if threading.current_thread() is threading.main_thread():
        prior_sigterm_handler = signal.signal(signal.SIGTERM, _exit_on_sigterm)

    prior_journal_mode = set_wal_journal_mode(db_path=db_path)
    try:
        run_solve_stages(
            scenario_arg_lists=scenario_arg_lists,
            n_parallel_scenarios=n_parallel_scenarios,
            on_solved=on_solved,
            on_stopped=on_stopped,
        )
    finally:
        # Best effort on an interrupted run: SQLite leaves the mode unchanged
        # (without raising) while other connections are open
        restore_journal_mode(db_path=db_path, journal_mode=prior_journal_mode)
        if prior_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, prior_sigterm_handler)

    if not quiet:
        print(
            f"Done. {len(completed_scenarios)} of {len(scenario_arg_lists)} "
            f"scenario(s) complete, finished on {datetime.datetime.now()}."
        )
    if failed_scenarios:
        print(
            "{} scenario(s) failed:\n{}".format(
                len(failed_scenarios),
                "\n".join(
                    f"  {scenario_name}: {error}"
                    for scenario_name, error in failed_scenarios
                ),
            ),
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
