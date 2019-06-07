from flask import Flask
from flask_socketio import SocketIO, send, emit
import multiprocessing
import os
import psutil
import pyutilib.subprocess.GlobalData

# Turn off signal handlers (in order to be able to spawn solvers from a
# Pyomo running in a thread)
# See: https://groups.google.com/forum/#!searchin/pyomo-forum
# /flask$20main$20thread%7Csort:date/pyomo-forum/TRwSIjQMtHI
# /e41wDAkPCgAJ and https://github.com/PyUtilib/pyutilib/issues/31
#
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

app = Flask(__name__)

# Global variables
SCENARIO_STATUS = dict()

#
# # @app.route('/hello/')
# # @app.route('/hello/<name>')
# # def hello(name=None):
# #     return render_template('hello.html', name=name)
# #
# #
# # if __name__ == "__main__":
# #     app.run(host='0.0.0.0', port=8000)
#
#
# @app.route('/')
# def run_scenario():
#
#     os.chdir('/Users/ana/dev/gridpath-ui-dev/')
#     import run_scenario
#     run_scenario.main(
#         args=['--scenario', 'test', '--scenario_location',
#               'examples', '--solver', 'cplex']
#     )
#     return("Scenario completed")
#
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port='8000', debug=True)



# Needed to pip install eventlet
socketio = SocketIO(app, async_mode='eventlet')


@app.route('/')
def welcome():
    print('GridPath UI')


@socketio.on('connect')
def connection():
    print('Electron connection established')


def _run_scenario(message):
    p = multiprocessing.current_process()
    scenario_name = str(message['scenario'])
    print("Running " + scenario_name)
    print("Process name and ID: ", p.name, p.pid)
    os.chdir('/Users/ana/dev/gridpath-ui-dev/')
    import run_scenario
    run_scenario.main(
        args=['--scenario', scenario_name, '--scenario_location',
              'scenarios', '--solver', 'cplex']
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


if __name__ == '__main__':
    print("Running server manually")
    socketio.run(
        app,
        port='8080',
        debug=True,
        use_reloader=False  # Reload manually for code changes to take effect
    )
