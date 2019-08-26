# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Launch a scenario end-to-end run in its own process.
"""

import os
import psutil
from flask_socketio import emit
import subprocess
import sys

from ui.server.common_functions import connect_to_database


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
        # p = multiprocessing.Process(
        #     target=run_scenario,
        #     name=scenario_id,
        #     args=(scenario_name,),
        # )
        # p.start()
        # TODO: this temporarily doesn"t work, unless the scenarios directory
        #  we"re passing is in the default location
        os.chdir(os.path.join(scenarios_directory, "..", "gridpath"))
        p = subprocess.Popen(
            [sys.executable, "-u",
             os.path.join(scenarios_directory,  "..", "gridpath",
                          "run_end_to_end.py"),
             "--log",
             "--scenario", scenario_name,
             "--solver", solver["name"],
             "--solver_executable", solver["executable"]])

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
