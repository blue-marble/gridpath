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


def get_scenario_detail(scenario_id, columns_string):
    """

    :param scenario_id:
    :param columns_string:
    :return:
    """
    io, c = connect_to_database()

    scenario_detail_query = c.execute(
        """SELECT {}
        FROM scenarios_view
        WHERE scenario_id = {};""".format(columns_string, scenario_id)
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


class ScenarioDetailAll(Resource):
    """
    Detailed information for a scenario.
    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(scenario_id, '*')

        return scenario_detail_api


class ScenarioDetailFeatures(Resource):
    """
    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'feature_fuels, feature_transmission, '
            'feature_transmission_hurdle_rates,'
            'feature_simultaneous_flow_limits, feature_load_following_up, '
            'feature_load_following_down, feature_regulation_up, '
            'feature_regulation_down, feature_spinning_reserves, '
            'feature_frequency_response, '
            'feature_rps, feature_carbon_cap, feature_track_carbon_imports, '
            'feature_prm, feature_elcc_surface, feature_local_capacity'
        )

        return scenario_detail_api


class ScenarioDetailTemporal(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'temporal'
        )

        return scenario_detail_api


# TODO: exclude transmission_load_zones if Tx feature not enabled
class ScenarioDetailGeographyLoadZones(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'geography_load_zones, project_load_zones, transmission_load_zones'
        )

        return scenario_detail_api


class ScenarioDetailLoad(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'load_profile'
        )

        return scenario_detail_api


class ScenarioDetailProjectCapacity(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'project_portfolio, project_existing_capacity, '
            'project_existing_fixed_cost, project_new_cost, '
            'project_new_potential, project_availability'
        )

        return scenario_detail_api


class ScenarioDetailProjectOpChars(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'project_operating_chars'
        )

        return scenario_detail_api


class ScenarioDetailFuels(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'feature_fuels, project_fuels, fuel_prices'
        )

        return scenario_detail_api


# TODO: show transmission selections only when Tx feature is selected,
#  show info that feature is not selected otherwise
class ScenarioDetailTransmissionCapacity(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'transmission_portfolio, transmission_existing_capacity '
        )

        return scenario_detail_api


class ScenarioDetailTransmissionOpChars(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'transmission_operational_chars'
        )

        return scenario_detail_api


# TODO: show subscenario selections only when Tx hurdle rate feature is
#  selected, show info that feature is not selected otherwise
class ScenarioDetailTransmissionHurdleRates(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'transmission_hurdle_rates'
        )

        return scenario_detail_api


# TODO: show subscenario selections only when Tx simultaneous flow feature
#  is selected, show info that feature is not selected otherwise
class ScenarioDetailTransmissionSimFlow(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'transmission_simultaneous_flow_limits, '
            'transmission_simultaneous_flow_limit_line_groups'
        )

        return scenario_detail_api


# Reserves
# TODO: show selections only of reserves feature selected
class ScenarioDetailLoadFollowingUp(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'load_following_reserves_up_profile, project_lf_up_bas'
        )

        return scenario_detail_api


class ScenarioDetailLoadFollowingDown(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'load_following_reserves_down_profile, project_lf_down_bas'
        )

        return scenario_detail_api


class ScenarioDetailRegulationUp(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'regulation_up_profile, project_reg_up_bas'
        )

        return scenario_detail_api


class ScenarioDetailRegulationDown(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'regulation_down_profile, project_reg_down_bas'
        )

        return scenario_detail_api


class ScenarioDetailSpinningReserves(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'spinning_reserves_profile, project_spin_bas'
        )

        return scenario_detail_api


class ScenarioDetailFrequencyResponse(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'frequency_response_profile, project_freq_resp_bas'
        )

        return scenario_detail_api


# Policy and reliability
class ScenarioDetailRPS(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'rps_target, project_rps_areas'
        )

        return scenario_detail_api


class ScenarioDetailCarbonCap(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'carbon_cap, project_carbon_cap_areas'
        )

        return scenario_detail_api


# TODO: show elcc_surface only if feature selected
class ScenarioDetailPRM(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'prm_requirement, elcc_surface, project_prm_areas, '
            'project_elcc_chars, project_prm_energy_only'
        )

        return scenario_detail_api


class ScenarioDetailLocalCapacity(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        scenario_detail_api = get_scenario_detail(
            scenario_id,
            'local_capacity_requirement, project_local_capacity_areas, '
            'project_local_capacity_chars'
        )

        return scenario_detail_api


class ServerStatus(Resource):
    """
    Server status; response will be 'running'; if HTTP error is caught,
    server status will be set to 'down'
    """
    @staticmethod
    def get():
        return 'running'


# ### Routes ### #
# Scenario list
api.add_resource(Scenarios, '/scenarios/')

# Scenario detail (by scenario_id)
# All
api.add_resource(ScenarioDetailAll, '/scenarios/<scenario_id>')
# Features
api.add_resource(ScenarioDetailFeatures, '/scenarios/<scenario_id>/features')
# Temporal
api.add_resource(ScenarioDetailTemporal, '/scenarios/<scenario_id>/temporal')
# Geography load zones
api.add_resource(
    ScenarioDetailGeographyLoadZones,
    '/scenarios/<scenario_id>/geography-load-zones'
)
# System load
api.add_resource(
    ScenarioDetailLoad,
    '/scenarios/<scenario_id>/load'
)
# Project capacity
api.add_resource(
    ScenarioDetailProjectCapacity,
    '/scenarios/<scenario_id>/project-capacity'
)
# Project operating characteristics
api.add_resource(
    ScenarioDetailProjectOpChars,
    '/scenarios/<scenario_id>/project-opchars'
)
# Fuels
api.add_resource(
    ScenarioDetailFuels,
    '/scenarios/<scenario_id>/fuels'
)
# Transmission capacity
api.add_resource(
    ScenarioDetailTransmissionCapacity,
    '/scenarios/<scenario_id>/transmission-capacity'
)
# Transmission operating characteristics
api.add_resource(
    ScenarioDetailTransmissionOpChars,
    '/scenarios/<scenario_id>/transmission-opchars'
)
# Transmission hurdle rates
api.add_resource(
    ScenarioDetailTransmissionHurdleRates,
    '/scenarios/<scenario_id>/transmission-hurdle-rates'
)
# Transmission simultaneous flow limits
api.add_resource(
    ScenarioDetailTransmissionSimFlow,
    '/scenarios/<scenario_id>/transmission-sim-flow'
)
# Reserves
api.add_resource(
    ScenarioDetailLoadFollowingUp,
    '/scenarios/<scenario_id>/lf-up'
)
api.add_resource(
    ScenarioDetailLoadFollowingDown,
    '/scenarios/<scenario_id>/lf-down'
)
api.add_resource(
    ScenarioDetailRegulationUp,
    '/scenarios/<scenario_id>/reg-up'
)
api.add_resource(
    ScenarioDetailRegulationDown,
    '/scenarios/<scenario_id>/reg-down'
)
api.add_resource(
    ScenarioDetailSpinningReserves,
    '/scenarios/<scenario_id>/spin'
)
api.add_resource(
    ScenarioDetailFrequencyResponse,
    '/scenarios/<scenario_id>/freq-resp'
)
# Policy and reliability
api.add_resource(
    ScenarioDetailRPS,
    '/scenarios/<scenario_id>/rps'
)
api.add_resource(
    ScenarioDetailCarbonCap,
    '/scenarios/<scenario_id>/carbon-cap'
)
api.add_resource(
    ScenarioDetailPRM,
    '/scenarios/<scenario_id>/prm'
)
api.add_resource(
    ScenarioDetailLocalCapacity,
    '/scenarios/<scenario_id>/local-capacity'
)


# Server status
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
    # '/Users/ana/dev/gridpath-ui-dev/db/io.db'
    io = sqlite3.connect(DATABASE_PATH)
    c = io.cursor()
    return io, c


if __name__ == '__main__':
    socketio.run(
        app,
        port='8080',
        debug=True,
        use_reloader=False  # Reload manually for code changes to take effect
    )
