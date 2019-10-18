# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import atexit
from flask import Flask
from flask_restful import Api
from flask_socketio import SocketIO, emit
import os
import signal
import sys
import time

# API
from ui.server.create_api import add_api_resources

# Database operations functions (Socket IO)
from ui.server.db_ops.add_scenario import add_or_update_scenario
from ui.server.db_ops.delete_scenario import clear as clear_scenario, \
  delete as delete_scenario
from ui.server.validate_scenario import validate_scenario

# Scenario process functions (Socket IO)
from ui.server.scenario_process import launch_scenario_process, \
  check_scenario_run_status, stop_scenario_run


# Define custom signal handlers
def sigterm_handler(signal, frame):
    """
    Exit when SIGTERM received (we're sending SIGTERM from Electron on app
    exit)
    :param signal:
    :param frame:
    :return:
    """
    print('SIGTERM received by server. Terminating server process.')
    sys.exit(0)


def sigint_handler(signal, frame):
    """
    Exit when SIGINT received
    :param signal:
    :param frame:
    :return:
    """
    print('SIGINT received by server. Terminating server process.')
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigint_handler)


# Global server variables
SCENARIOS_DIRECTORY = os.environ['SCENARIOS_DIRECTORY']
# DATABASE_PATH = '/Users/ana/dev/ui-run-scenario/db/io.db'
DATABASE_PATH = os.environ['GRIDPATH_DATABASE_PATH']
CBC_EXECUTABLE = os.environ['CBC_EXECUTABLE']
CPLEX_EXECUTABLE = os.environ['CPLEX_EXECUTABLE']
GUROBI_EXECUTABLE = os.environ['GUROBI_EXECUTABLE']
SOLVER_EXECUTABLES = {
  "cbc": {"name": "cbc", "executable": CBC_EXECUTABLE},
  "cplex": {"name": "cplex", "executable": CPLEX_EXECUTABLE},
  "gurobi": {"name": "gurobi", "executable": GUROBI_EXECUTABLE}
}


# TODO: not sure we'll need this
SCENARIO_STATUS = dict()


# ### Basic server set-up ### #
app = Flask(__name__)
api = Api(app)

# Needed to pip install eventlet
socketio = SocketIO(app, async_mode='eventlet')


@app.route('/')
def welcome():
    return 'GridPath UI Server is running.'


@socketio.on('connect')
def connection():
    print('Client connection established.')


# ################################### API ################################### #

add_api_resources(api=api, db_path=DATABASE_PATH)


# ########################## Socket Communication ########################### #

# ### Database operations ### #
@socketio.on('add_new_scenario')
def socket_add_or_edit_new_scenario(msg):
    add_or_update_scenario(db_path=DATABASE_PATH, msg=msg)


# ### RUNNING SCENARIOS ### #

@socketio.on('launch_scenario_process')
def socket_launch_scenario_process(client_message):
    """
    :param client_message:
    :return:
    Launch and manage a scenario run process.
    """
    print(client_message)
    scenario_id = client_message["scenario"]
    solver = SOLVER_EXECUTABLES[client_message["solver"]]
    # TODO: implement functionality to skip warnings if the user has
    #  confirmed they want to re-run scenario
    skip_warnings = client_message["skipWarnings"]

    warn_user_boolean = False if skip_warnings \
        else warn_user(scenario_id=scenario_id)

    if warn_user_boolean:
        pass
    else:
        # Launch the process, get back the process object, scenario_id,
        # and scenario_name
        p, scenario_id, scenario_name = launch_scenario_process(
          db_path=DATABASE_PATH,
          scenarios_directory=SCENARIOS_DIRECTORY,
          scenario_id=scenario_id,
          solver=solver
        )
        # Needed to ensure child processes are terminated when server exits
        atexit.register(p.terminate)

        # Save the scenario's process ID
        SCENARIO_STATUS[scenario_id] = dict()
        SCENARIO_STATUS[scenario_id]['scenario_name'] = scenario_name
        SCENARIO_STATUS[scenario_id]['process_id'] = p.pid

        # Wait a couple of seconds, then tell the client the process was
        # launched, so that the client can refresh the run status
        time.sleep(2)
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
        emit("warn_user_scenario_is_running",
             {"scenario_id": scenario_id, "process_id": process_id})
        return True
    elif run_status == "complete":
        emit("warn_user_scenario_is_complete",
             {"scenario_id": scenario_id})
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
    stop_scenario_run(db_path=DATABASE_PATH,
                      scenario_id=scenario_id)


@socketio.on("validate_scenario")
def socket_validate_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    validate_scenario(db_path=DATABASE_PATH,
                      client_message=client_message)
    emit("validation_complete")


@socketio.on("clear_scenario")
def socket_clear_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    clear_scenario(db_path=DATABASE_PATH,
                   scenario_id=client_message["scenario"])
    emit("scenario_cleared")


@socketio.on("delete_scenario")
def socket_clear_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    delete_scenario(db_path=DATABASE_PATH,
                    scenario_id=client_message["scenario"])
    emit("scenario_deleted")


def main():
    socketio.run(
        app,
        host='127.0.0.1',
        port='8080',
        debug=True,
        use_reloader=False  # Reload manually for code changes to take effect
    )


if __name__ == '__main__':
    main()
