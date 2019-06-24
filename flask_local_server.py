from flask import Flask
from flask_socketio import SocketIO, send, emit
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

app = Flask(__name__)
api = Api(app)

# Global variables
SCENARIO_STATUS = dict()
GRIDPATH_DIRECTORY = str()
DATABASE_PATH = str()

# Needed to pip install eventlet
socketio = SocketIO(app, async_mode='eventlet')


@app.route('/')
def welcome():
    print('GridPath UI')
    return 'GridPath UI'


@socketio.on('connect')
def connection():
    print('Electron connection established')


def _run_scenario(message):
    p = multiprocessing.current_process()
    scenario_name = str(message['scenario'])
    print("Running " + scenario_name)
    print("Process name and ID: ", p.name, p.pid)

    # TODO: we'll need to get this from the user
    os.chdir('/Users/ana/dev/gridpath-ui-dev/')

    import run_scenario
    run_scenario.main(
        args=['--scenario', scenario_name, '--scenario_location',
              'scenarios', '--solver', 'cplex', '--update_db_run_status']
    )
    return("Scenario completed")


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


@socketio.on('get_scenario_list')
def get_scenario_list():
    """

    :return:
    """
    print("Received request for scenario list")
    # TODO: we'll need to get db path from the user
    os.chdir('/Users/ana/dev/gridpath-ui-dev/')
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    scenarios_query = c.execute(
        """SELECT scenario_name FROM scenarios;"""
    )

    scenarios = [s[0] for s in scenarios_query]
    print(scenarios)
    print("Sending scenario list to client")

    emit('send_scenario_list', scenarios)


@socketio.on('get_scenario_detail')
def get_scenario_details(scenario):
    """

    :return:
    """
    print("Received request for scenario detail")
    # TODO: we'll need to get db path from the user
    os.chdir('/Users/ana/dev/gridpath-ui-dev/')
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    scenario_detail_query = c.execute(
        """SELECT
            subscenarios_project_portfolios.name as portfolio, 
            subscenarios_project_operational_chars.name as operating_chars, 
            subscenarios_system_load.name as load_profile, 
            subscenarios_project_fuel_prices.name as fuel_prices
            FROM scenarios 
            JOIN subscenarios_project_portfolios 
            USING (project_portfolio_scenario_id)
            JOIN subscenarios_project_operational_chars 
            USING (project_operational_chars_scenario_id)
            JOIN subscenarios_system_load 
            USING (load_scenario_id)
            JOIN subscenarios_project_fuel_prices 
            USING (fuel_price_scenario_id)
            WHERE scenario_name = '{}';""".format(scenario)
    )



    column_names = [s[0] for s in scenario_detail_query.description]
    column_values = list(list(scenario_detail_query)[0])
    scenario_detail_dict = dict(zip(column_names, column_values))
    scenario_detail_dict['scenario_name'] = scenario

    scenario_status_query = c.execute(
        """SELECT status
            FROM mod_run_status
            WHERE scenario_name = '{}';""".format(scenario)
    ).fetchone()
    scenario_detail_dict['run_status'] = scenario_status_query[0]

    print(scenario_detail_dict)

    print("Sending scenario detail to client")

    emit('send_scenario_detail', scenario_detail_dict)


class Scenarios(Resource):
    @staticmethod
    def get():
        global DATABASE_PATH
        io = sqlite3.connect(DATABASE_PATH)
        c = io.cursor()

        scenarios_query = c.execute(
            """SELECT scenario_id, scenario_name
            FROM scenarios
            ORDER by scenario_id ASC;"""
        )

        scenarios_api = []
        for s in scenarios_query:
            scenarios_api.append({'id': s[0], 'name': s[1]})

        return scenarios_api


# Add the scenarios data to the scenarios route
api.add_resource(Scenarios, '/scenarios')  # Route_1


@socketio.on('set_database_path')
def set_database_path(db_path):
    print('Database path set to ', str(db_path))
    global DATABASE_PATH
    DATABASE_PATH = db_path

    # Get the scenarios
    # TODO: when to call this?
    Scenarios.get()


if __name__ == '__main__':
    print("Running server manually")
    socketio.run(
        app,
        port='8080',
        debug=True,
        use_reloader=False  # Reload manually for code changes to take effect
    )
