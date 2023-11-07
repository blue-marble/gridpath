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

import atexit
from flask import Flask
from flask_restful import Api
from flask_socketio import SocketIO, emit
import os
import signal
import subprocess
import sys

# API
from ui.server.create_api import add_api_resources
from ui.server.common_functions import get_executable_path

# Database operations functions (Socket IO)
from ui.server.db_ops.add_scenario import add_or_update_scenario
from ui.server.db_ops.delete_scenario import (
    clear as clear_scenario,
    delete as delete_scenario,
)
from ui.server.validate_scenario import validate_scenario
from ui.server.save_data import save_table_data_to_csv, save_plot_data_to_csv
from ui.server.run_queue_manager import (
    add_scenario_to_queue,
    remove_scenario_from_queue,
)

# Scenario process functions (Socket IO)
from ui.server.scenario_process import (
    launch_scenario_process,
    check_scenario_run_status,
    stop_scenario_run,
)


# Define custom signal handlers
def sigterm_handler(signal, frame):
    """
    Exit when SIGTERM received (we're sending SIGTERM from Electron on app
    exit)
    :param signal:
    :param frame:
    :return:
    """
    print("SIGTERM received by server. Terminating server process.")
    sys.exit(0)


def sigint_handler(signal, frame):
    """
    Exit when SIGINT received
    :param signal:
    :param frame:
    :return:
    """
    print("SIGINT received by server. Terminating server process.")
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigint_handler)


# Global server variables
SCENARIOS_DIRECTORY = os.environ["SCENARIOS_DIRECTORY"]
# DATABASE_PATH = '/Users/ana/dev/ui-run-scenario/db/io.db'
DATABASE_PATH = os.environ["GRIDPATH_DATABASE_PATH"]
SOLVER1_NAME = os.environ["SOLVER1_NAME"]
SOLVER1_EXECUTABLE = os.environ["SOLVER1_EXECUTABLE"]
SOLVER2_NAME = os.environ["SOLVER2_NAME"]
SOLVER2_EXECUTABLE = os.environ["SOLVER2_EXECUTABLE"]
SOLVER3_NAME = os.environ["SOLVER3_NAME"]
SOLVER3_EXECUTABLE = os.environ["SOLVER3_EXECUTABLE"]
SOLVERS = {
    SOLVER1_NAME: SOLVER1_EXECUTABLE,
    SOLVER2_NAME: SOLVER2_EXECUTABLE,
    SOLVER3_NAME: SOLVER3_EXECUTABLE,
}
RUN_QUEUE_MANAGER_PID = None


# TODO: not sure we'll need this
SCENARIO_STATUS = dict()


# ### Basic server set-up ### #
app = Flask(__name__)
api = Api(app)

# Needed to pip install eventlet
socketio = SocketIO(app, async_mode="eventlet")


@app.route("/")
def welcome():
    return "GridPath UI Server is running."


@socketio.on("connect")
def connection():
    print("Client connection established.")


# ################################### API ################################### #

add_api_resources(api=api, db_path=DATABASE_PATH)


# ########################## Socket Communication ########################### #


# ### DATABASE OPERATIONS ### #
@socketio.on("add_new_scenario")
def socket_add_or_edit_new_scenario(msg):
    add_or_update_scenario(db_path=DATABASE_PATH, msg=msg)


# ### RUNNING SCENARIOS ### #


@socketio.on("launch_scenario_process")
def socket_launch_scenario_process(client_message):
    """
    :param client_message:
    :return:
    Launch and manage a scenario run process.
    """
    print(client_message)

    scenario_id = client_message["scenario"]

    # TODO: get this from the database instead of passing from the UI to
    #  consolidate
    solver = client_message["solver"]

    # TODO: add error if solver is not in the keys of the SOLVERS
    solver_executable = SOLVERS[solver]
    # TODO: implement functionality to skip warnings if the user has
    #  confirmed they want to re-run scenario
    skip_warnings = client_message["skipWarnings"]

    warn_user_boolean = False if skip_warnings else warn_user(scenario_id=scenario_id)

    if not warn_user_boolean:
        # Launch the process, get back the process object, scenario_id,
        # and scenario_name
        p, scenario_id, scenario_name = launch_scenario_process(
            db_path=DATABASE_PATH,
            scenarios_directory=SCENARIOS_DIRECTORY,
            scenario_id=scenario_id,
            solver=solver,
            solver_executable=solver_executable,
        )
        # Needed to ensure child processes are terminated when server exits
        atexit.register(p.terminate)

        # Save the scenario's process ID
        SCENARIO_STATUS[scenario_id] = dict()
        SCENARIO_STATUS[scenario_id]["scenario_name"] = scenario_name
        SCENARIO_STATUS[scenario_id]["process_id"] = p.pid

        # Tell the client the process launched
        emit("scenario_process_launched")


def warn_user(scenario_id):
    """
    :param scenario_id:
    :return:
    """
    run_status, process_id = check_scenario_run_status(
        db_path=DATABASE_PATH, scenario_id=scenario_id
    )

    # Warn user if scenario is running or is complete
    if run_status == "running":
        emit(
            "warn_user_scenario_is_running",
            {"scenario_id": scenario_id, "process_id": process_id},
        )
        return True
    elif run_status == "complete":
        emit("warn_user_scenario_is_complete", {"scenario_id": scenario_id})
        return True
    else:
        return False


@socketio.on("stop_scenario_run")
def socket_stop_scenario_run(client_message):
    """

    :param client_message:
    :return:
    """
    print(client_message)
    scenario_id = client_message["scenario"]
    print("Stopping scenario run for scenario ID {}".format(scenario_id))
    stop_scenario_run(db_path=DATABASE_PATH, scenario_id=scenario_id)

    # Tell the client the run was stopped
    emit("scenario_stopped")


@socketio.on("validate_scenario")
def socket_validate_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    validate_scenario(db_path=DATABASE_PATH, client_message=client_message)
    emit("validation_complete")


@socketio.on("clear_scenario")
def socket_clear_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    clear_scenario(db_path=DATABASE_PATH, scenario_id=client_message["scenario"])
    emit("scenario_cleared")


@socketio.on("delete_scenario")
def socket_clear_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    delete_scenario(db_path=DATABASE_PATH, scenario_id=client_message["scenario"])
    emit("scenario_deleted")


# Queue Manager
@socketio.on("add_scenario_to_queue")
def socket_add_scenario_to_queue(client_message):
    """

    :return:
    """
    add_scenario_to_queue(db_path=DATABASE_PATH, scenario_id=client_message["scenario"])

    # Start the run queue manager if we don't have a process currently
    if RUN_QUEUE_MANAGER_PID is None:
        start_run_queue_manager()


@socketio.on("remove_scenario_from_queue")
def socket_remove_scenario_from_queue(client_message):
    """

    :return:
    """
    remove_scenario_from_queue(
        db_path=DATABASE_PATH, scenario_id=client_message["scenario"]
    )


@socketio.on("reset_queue_manager_pid")
def socket_queue_manager_exit_alert():
    global RUN_QUEUE_MANAGER_PID
    RUN_QUEUE_MANAGER_PID = None


def start_run_queue_manager():
    # Start queue manager
    print("Starting queue manager")
    run_queue_manager_executable = get_executable_path(
        script_name="gridpath_run_queue_manager"
    )

    p = subprocess.Popen(
        [run_queue_manager_executable, "--database", DATABASE_PATH],
        shell=False,
    )
    print("Queue manager PID: ,", p.pid)
    global RUN_QUEUE_MANAGER_PID
    RUN_QUEUE_MANAGER_PID = p.pid

    # Needed to ensure child processes are terminated when server exits
    # TODO: still needed now that the queue manager will exit when it does
    #  not get a response from the server?
    atexit.register(p.terminate)


# ### SAVING DATA ### #


@socketio.on("save_table_data")
def socket_save_table_data(client_message):
    """

    :param client_message:
    :return:
    """
    save_table_data_to_csv(
        db_path=DATABASE_PATH,
        table=client_message["tableName"],
        scenario_id=client_message["scenarioID"],
        other_scenarios=client_message["otherScenarios"],
        download_path=client_message["downloadPath"],
        table_type=client_message["tableType"],
        ui_table_name_in_db=client_message["uiTableNameInDB"],
        ui_row_name_in_db=client_message["uiRowNameInDB"],
    )


@socketio.on("save_plot_data")
def socket_save_plot_data(client_message):
    """
    :param client_message: dictionary with various params needed for
      save_plot_data_to_csv function
    :return:

    Function that responds to socket call from client and calls
    save_plot_data_to_csv function.
    """
    save_plot_data_to_csv(
        db_path=DATABASE_PATH,
        download_path=client_message["downloadPath"],
        scenario_id_list=client_message["scenarioIDList"],
        plot_type=client_message["plotType"],
        load_zone=client_message["loadZone"],
        carbon_cap_zone=client_message["carbonCapZone"],
        energy_target_zone=client_message["energyTargetZone"],
        period=client_message["period"],
        horizon=client_message["horizon"],
        start_timepoint=client_message["startTimepoint"],
        end_timepoint=client_message["endTimepoint"],
        subproblem=client_message["subproblem"],
        stage=client_message["stage"],
        project=client_message["project"],
    )


def main():
    # Run server
    socketio.run(
        app,
        host="127.0.0.1",
        port="8080",
        debug=True,
        use_reloader=False,  # Reload manually for code changes to take effect
    )


if __name__ == "__main__":
    main()
