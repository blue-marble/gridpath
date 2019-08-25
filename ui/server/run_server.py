# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import atexit
from flask import Flask
from flask_socketio import SocketIO, emit
import os
import signal
import sys

from flask_restful import Api

# API
from ui.server.create_api import add_api_resources

# Database operations functions (Socket IO)
from ui.server.db_ops.add_scenario import add_or_update_scenario
from ui.server.validate_scenario import validate_scenario

# Scenario process functions (Socket IO)
from ui.server.scenario_process import launch_scenario_process, \
  check_scenario_process_status


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
GRIDPATH_DIRECTORY = os.environ['GRIDPATH_DIRECTORY']
# DATABASE_PATH = '/Users/ana/dev/ui-run-scenario/db/io.db'
DATABASE_PATH = os.environ['GRIDPATH_DATABASE_PATH']
SOLVER = str()

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
# TODO: incomplete functionality

@socketio.on('launch_scenario_process')
def socket_launch_scenario_process(client_message):
    """
    :param client_message:
    :return:
    Launch and manage a scenario run process.
    """
    # Launch the process, get back the process object, scenario_id,
    # and scenario_name
    p, scenario_id, scenario_name = launch_scenario_process(
      db_path=DATABASE_PATH,
      gridpath_directory=GRIDPATH_DIRECTORY,
      scenario_status=SCENARIO_STATUS,
      client_message=client_message
    )
    # Needed to ensure child processes are terminated when server exits
    atexit.register(p.terminate)

    # Save the scenario's process ID
    # TODO: we should save to Electron instead, as closing the UI will
    #  delete the global data for the server
    SCENARIO_STATUS[(scenario_id, scenario_name)] = dict()
    SCENARIO_STATUS[(scenario_id, scenario_name)]['process_id'] = p.pid


# TODO: implement functionality to check on the process from the UI (
#  @socketio is not linked to anything yet)
@socketio.on('check_scenario_process_status')
def socket_check_scenario_process_status(client_message):
    """
    :param client_message:
    :return:
    """
    check_scenario_process_status(db_path=DATABASE_PATH,
                                  scenario_status=SCENARIO_STATUS,
                                  client_message=client_message)


@socketio.on("validate_scenario")
def socket_validate_scenario(client_message):
    """

    :param client_message:
    :return:
    """
    validate_scenario(db_path=DATABASE_PATH,
                      client_message=client_message)
    emit("validation_complete")


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
