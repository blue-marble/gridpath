from flask import Flask
from flask_socketio import SocketIO, emit
import multiprocessing
import os
import pyutilib.subprocess.GlobalData
import sqlite3

from flask_restful import Resource, Api

# Turn off signal handlers (in order to be able to spawn solvers from a
# Pyomo running in a thread)
# See: https://groups.google.com/forum/#!searchin/pyomo-forum
# /flask$20main$20thread%7Csort:date/pyomo-forum/TRwSIjQMtHI
# /e41wDAkPCgAJ and https://github.com/PyUtilib/pyutilib/issues/31
#
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False


# Global variables
GRIDPATH_DIRECTORY = str()
DATABASE_PATH = str()
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


# ### User settings ### #

@socketio.on('set_gridpath_directory')
def set_database_path(gp_directory):
    print('GridPath directory set to ', str(gp_directory))
    global GRIDPATH_DIRECTORY
    GRIDPATH_DIRECTORY = gp_directory


@socketio.on('set_database_path')
def set_database_path(db_path):
    print('Database path set to ', str(db_path))
    global DATABASE_PATH
    DATABASE_PATH = db_path

    # Get the scenarios
    # TODO: when to call this?
    Scenarios.get()


# ### API ### #
class Scenarios(Resource):
    """
    The list of scenarios.
    """
    @staticmethod
    def get():
        io, c = connect_to_database()

        scenarios_query = c.execute(
            """SELECT *
            FROM scenarios_view
            ORDER by scenario_id ASC;"""
        )

        scenarios_api = []
        for s in scenarios_query:
            scenarios_api.append({'id': s[0], 'name': s[1]})

        return scenarios_api


class ScenarioDetail(Resource):
    """
    Detailed information for a scenario.
    """
    @staticmethod
    def get(scenario_id):
        io, c = connect_to_database()

        scenario_detail_query = c.execute(
            """SELECT *
            FROM scenarios_view
            WHERE scenario_id = {};""".format(scenario_id)
        )

        column_names = [s[0] for s in scenario_detail_query.description]
        column_values = list(list(scenario_detail_query)[0])
        scenario_detail_dict = dict(zip(column_names, column_values))

        scenario_detail_api = []
        for key in scenario_detail_dict.keys():
            scenario_detail_api.append(
                {'name': key, 'value': scenario_detail_dict[key]}
            )

        return scenario_detail_api


class ServerStatus(Resource):
    """
    Server status; response will be 'running'; if HTTP error is caught,
    server status will be sent to 'down'
    """
    @staticmethod
    def get():
        return 'running'


# Routes
# Scenario list
api.add_resource(Scenarios, '/scenarios/')
# Scenario detail (by scenario_id)
api.add_resource(ScenarioDetail, '/scenarios/<scenario_id>')
# Scenario detail (by scenario_id)
api.add_resource(ServerStatus, '/server-status')


# ### Socket Communication ### #
@socketio.on('add_new_scenario')
def add_new_scenario(msg):
    print('Got message from Angular')
    print(msg)

    io, c = connect_to_database()

    c.execute(
        """INSERT INTO scenarios (scenario_name) VALUES ('{}')""".format(
            msg['scenarioName']))
    io.commit()


# ### RUNNING SCENARIOS ### #
# TODO: incomplete functionality
# TODO: needs update
def _run_scenario(message):
    p = multiprocessing.current_process()
    scenario_name = str(message['scenario'])
    print("Running " + scenario_name)
    print("Process name and ID: ", p.name, p.pid)

    os.chdir(GRIDPATH_DIRECTORY)

    import run_scenario
    run_scenario.main(
        args=['--scenario', scenario_name, '--scenario_location',
              'scenarios', '--solver', SOLVER, '--update_db_run_status']
    )


# TODO: probably will do this directly from Angular
@socketio.on('launch_scenario_process')
def launch_scenario_process(message):
    scenario_name = str(message['scenario'])
    # TODO: there needs to be a check that this scenario isn't already running
    process_status = check_scenario_process_status(message=message)
    if process_status:
        print("Scenario already running")
        emit(
            'scenario_already_running',
            'scenario already running'
        )
    else:
        print("Starting process for scenario " + scenario_name)
        p = multiprocessing.Process(
            target=_run_scenario,
            name=scenario_name,
            args=(message,),
        )
        p.start()

        print("Sending PID to client ", p.pid)
        # # TODO: should we be joining
        # p.join()

        global SCENARIO_STATUS
        SCENARIO_STATUS[scenario_name] = dict()
        SCENARIO_STATUS[scenario_name]['process_id'] = p.pid


# TODO: figure out how to deal with scenarios that are already running
@socketio.on('check_scenario_process_status')
def check_scenario_process_status(message):
    """
    Check if there is any running process that contains the given name processName.
    """
    scenario_name = str(message['scenario'])
    global SCENARIO_STATUS
    if scenario_name in SCENARIO_STATUS.keys():
        if SCENARIO_STATUS[scenario_name]['process_id'] is not None:
            # TODO: will assume running for now, but will need to actually
            #  check process status later
            return True
        else:
            return False
    else:
        return False


# ### Common functions ### #
def connect_to_database():
    io = sqlite3.connect(DATABASE_PATH)
    c = io.cursor()
    return io, c


if __name__ == '__main__':
    print("Running server manually")
    socketio.run(
        app,
        port='8080',
        debug=True,
        use_reloader=False  # Reload manually for code changes to take effect
    )
