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


def launch_scenario_process(
    db_path, scenarios_directory, scenario_status, scenario_id, solver
):
    """
    :param db_path:
    :param scenarios_directory:
    :param scenario_status:
    :param scenario_id: integer, the scenario_id from the database
    :param solver: dictionary with keys "name" and "executable" for the solver
    :return:

    Launch a process to run the scenario.
    """
    # Get the scenario name for this scenario ID
    # TODO: pass both from the client and do a check here that they exist
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    scenario_name = c.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    # First, check if the scenario is already running
    run_status, process_id = check_scenario_run_status(
        db_path=db_path,
        scenario_id=scenario_id
    )
    if run_status == 'running':
        # TODO: what should happen if the scenario is already running? At a
        #  minimum, it should be a warning and perhaps a way to stop the
        #  process and re-start the scenario run.
        print("Scenario already running.")
        emit(
            "scenario_already_running",
            "scenario already running"
        )
    # If the scenario is not found among the running processes, launch a
    # process
    else:
        print("Starting process for scenario_id " + str(scenario_id))
        # Get the run_gridpath_e2e entry point script from the
        # sys.executable (remove 'python' and add 'gridpath_run_e2e')
        if os.name == "nt":
            chars_to_remove = 10
            shell_bool = True
        else:
            chars_to_remove = 6
            shell_bool = False
        run_gridpath_e2e_executable = \
            sys.executable[:-chars_to_remove] + "gridpath_run_e2e"
        p = subprocess.Popen(
            [run_gridpath_e2e_executable,
             "--log",
             "--database", db_path,
             "--scenario", scenario_name,
             "--scenario_location", scenarios_directory,
             "--solver", solver["name"],
             "--solver_executable", solver["executable"]],
            shell=shell_bool)

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
    print("Really stopping scenario run for scenario ID {}".format(
      scenario_id))
    run_status, process_id = check_scenario_run_status(db_path=db_path,
                                                       scenario_id=scenario_id)
    if run_status != "running":
        # TODO: Tell user scenario is not running
        pass
    else:
        print("Here we are")
        p = psutil.Process(process_id)
        print("Process ID seen by stop_scenario_run is {}".format(process_id))
        print("Attempting to terminate")
        p.terminate()
