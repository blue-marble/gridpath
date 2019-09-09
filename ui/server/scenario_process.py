# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Launch a scenario end-to-end run in its own process.
"""

import os
import psutil
from flask_socketio import emit
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
    io, c = connect_to_database(db_path=db_path)
    scenario_name = c.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    # First, check if the scenario is already running
    process_status = check_scenario_process_status(
        db_path=db_path,
        scenario_status=scenario_status,
        scenario_id=scenario_id
    )
    if process_status:
        # TODO: what should happen if the scenario is already running? At a
        #  minimum, it should be a warning and perhaps a way to stop the
        #  process and re-start the scenario run.
        print("Scenario already running.")
        emit(
            "scenario_already_running",
            "scenario already running"
        )
    # If the scenario is not found among the running processes, launch a
    # multiprocessing process
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
            [run_gridpath_e2e_executable, "-u",
             "--log",
             "--database", db_path,
             "--scenario", scenario_name,
             "--scenario_location", scenarios_directory,
             "--solver", solver["name"],
             "--solver_executable", solver["executable"]],
            shell=shell_bool)

        return p, scenario_id, scenario_name


def check_scenario_process_status(db_path, scenario_status, scenario_id):
    """
    Check if there is any running process that contains the given scenario
    """
    io, c = connect_to_database(db_path=db_path)
    scenario_name = c.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    if (scenario_id, scenario_name) in scenario_status.keys():
        pid = scenario_status[(scenario_id, scenario_name)]["process_id"]
        # Process ID saved in global and process is still running
        if pid in [p.pid for p in psutil.process_iter()] \
                and psutil.Process(pid).status() == "running":
            return True
        else:
            # Process ID saved in global but process is not running
            return False
    else:
        return False
