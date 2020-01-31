# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Launch a scenario end-to-end run in its own process.
"""

import os
from flask_socketio import emit
import psutil
import subprocess
import sys

from db.common_functions import connect_to_database
from gridpath.run_end_to_end import update_run_status
from ui.server.db_ops.delete_scenario import clear as clear_scenario


def launch_scenario_process(
    db_path, scenarios_directory, scenario_id, solver, solver_executable
    ):
    """
    :param db_path:
    :param scenarios_directory:
    :param scenario_id: integer, the scenario_id from the database
    :param solver: string, the solver name
    :param solver: string, the solver executable
    :return:

    Launch a process to run the scenario.
    """
    # Get the scenario name for this scenario ID
    # TODO: pass both from the client and do a check here that they exist
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    scenario_name = get_scenario_name_from_scenario_id(cursor=c,
                                                       scenario_id=scenario_id)


    # First, check if the scenario is already running
    run_status, process_id = check_scenario_run_status(
        db_path=db_path,
        scenario_id=scenario_id
    )
    if run_status == 'running':
        # This shouldn't ever happen, as the Run Scenario button should
        # disappear when status changes to 'running'
        print("Scenario already running.")
        emit(
            "scenario_already_running"
        )
    # If the scenario is not found among the running processes, launch a
    # process
    else:
        print("Starting process for scenario_id " + str(scenario_id))
        # Get the run_gridpath_e2e entry point script from the
        # sys.executable (remove 'python' and add 'gridpath_run_e2e')
        chars_to_remove = 11 if os.name == "nt" else 7

        base_dir = os.path.basename(sys.executable[:-chars_to_remove])

        run_gridpath_e2e_executable = \
            os.path.join(
              sys.executable[:-chars_to_remove],
              "" if base_dir.lower() in ["scripts", "bin"] else "scripts",
              "gridpath_run_e2e"
            )

        p = subprocess.Popen(
            [run_gridpath_e2e_executable,
             "--log",
             "--database", db_path,
             "--scenario", scenario_name,
             "--scenario_location", scenarios_directory,
             "--solver", solver,
             "--solver_executable", solver_executable],
            shell=False
        )

        return p, scenario_id, scenario_name


def check_scenario_run_status(db_path, scenario_id):
    """
    Check if there is any running process that contains the given scenario
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()
    run_status, process_id = c.execute("""
        SELECT run_status_name, run_process_id
        FROM scenarios
        JOIN mod_run_status_types
        USING (run_status_id)
        WHERE scenario_id = {}
        """.format(scenario_id)
    ).fetchone()

    return run_status, process_id


def stop_scenario_run(db_path, scenario_id):
    """

    :param db_path:
    :param scenario_id:
    :return:
    """
    run_status, process_id = check_scenario_run_status(db_path=db_path,
                                                       scenario_id=scenario_id)
    if run_status != "running":
        # TODO: Tell user scenario is not running
        pass
    # If we can't find the process ID (None or psutil error),
    # the process likely did not exit cleanly, so we'll clear scenario
    # results and update the run status to 'run_error'
    elif process_id is None:
        clean_up_scenario_with_no_process_id(
          db_path=db_path, scenario_id=scenario_id
        )
    else:
        print("Attempting to terminate process ID {}".format(process_id))
        # TODO: is there an additional check to do, to make sure we don't
        #  terminate the wrong process (e.g. because of a prior crash,
        #  scenario appearing as running, but a different process actually
        #  having this id)
        try:
            p = psutil.Process(process_id)
            p.terminate()
        except psutil.NoSuchProcess:
            clean_up_scenario_with_no_process_id(
                db_path=db_path, scenario_id=scenario_id
            )

        # Update the scenario status to 'run_stopped'
        # This is only needed on Windows; on Mac, the signal is caught by
        # run_end_to_end, which updates the scenario status
        if os.name == "nt":
            connect_to_db_and_update_run_status(
              db_path=db_path,
              scenario_id=scenario_id,
              status_id=4
            )


def get_scenario_name_from_scenario_id(cursor, scenario_id):
    """
    :param cursor:
    :param scenario_id:
    :return:
    """
    scenario_name = cursor.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    return scenario_name


def connect_to_db_and_update_run_status(db_path, scenario_id, status_id):
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()
    scenario_name = get_scenario_name_from_scenario_id(
      cursor=c, scenario_id=scenario_id)
    update_run_status(db_path=db_path, scenario=scenario_name,
                      status_id=status_id)


def clean_up_scenario_with_no_process_id(db_path, scenario_id):
    """

    :param db_path:
    :param scenario_id:
    :return:
    """
    print("No such process")
    # Warn the user about what we're about to do
    emit(
      "process_id_not_found"
    )
    # Clear scenario from database
    clear_scenario(db_path=db_path, scenario_id=scenario_id)
    # Update status to 'run_error'
    connect_to_db_and_update_run_status(
      db_path=db_path,
      scenario_id=scenario_id,
      status_id=3
    )
