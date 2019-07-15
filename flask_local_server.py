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

# Gridpath modules
from db.utilities.create_scenario import create_scenario

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


# ################################### API ################################### #

# ### API: Scenarios List ### #
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


# ### API: Scenario Detail ### #
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


class ScenarioDetailGeographyLoadZones(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_transmission'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'geography_load_zones, project_load_zones, '
                'transmission_load_zones'
            )
        else:
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'geography_load_zones, project_load_zones, '
                '"WARNING: transmission feature disabled" AS '
                'transmission_load_zones'
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
        if check_feature(scenario_id, 'of_fuels'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'project_fuels, fuel_prices'
            )
        else:
            scenario_detail_api = [
                {"name": "project_fuels",
                 "value": "WARNING: fuels feature disabled"},
                {"name": "fuel_prices",
                 "value": "WARNING: fuels feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionCapacity(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_transmission'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'transmission_portfolio, transmission_existing_capacity '
            )
        else:
            scenario_detail_api = [
                {"name": "transmission_portfolio",
                 "value": "WARNING: transmission feature disabled"},
                {"name": "transmission_existing_capacity",
                 "value": "WARNING: transmission feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionOpChars(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_transmission'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'transmission_operational_chars'
            )
        else:
            scenario_detail_api = [
                {"name": "transmission_operational_chars",
                 "value": "WARNING: transmission feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionHurdleRates(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_transmission') \
                and check_feature(scenario_id, 'of_transmission_hurdle_rates'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'transmission_hurdle_rates'
            )
        elif not check_feature(scenario_id, 'of_transmission') \
                and not check_feature(scenario_id,
                                      'of_transmission_hurdle_rates'):
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: both transmission and transmission "
                          "hurdle rates features disabled"}
            ]
        elif not check_feature(scenario_id, 'of_transmission') \
                and check_feature(scenario_id, 'of_transmission_hurdle_rates'):
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: transmission feature disabled"}
            ]
        else:
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: transmission hurdle rates feature "
                          "disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionSimFlow(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_transmission') \
                and check_feature(scenario_id, 'of_simultaneous_flow_limits'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'transmission_simultaneous_flow_limits, '
                'transmission_simultaneous_flow_limit_line_groups'
            )
        elif not check_feature(scenario_id, 'of_transmission') \
                and not check_feature(scenario_id,
                                      'of_simultaneous_flow_limits'):
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: both transmission and simultaneous flow "
                          "limits features disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: both transmission and simultaneous flow "
                          "limits features disabled"}
            ]
        elif not check_feature(scenario_id, 'of_transmission') \
                and check_feature(scenario_id, 'of_simultaneous_flow_limits'):
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: transmission feature disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: transmission feature disabled"}
            ]
        else:
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: simultaneous flow limits feature "
                          "disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: simultaneous flow limits feature disabled"}
            ]

        return scenario_detail_api


# Reserves
class ScenarioDetailLoadFollowingUp(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_lf_reserves_up'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'load_following_reserves_up_profile, project_lf_up_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "load_following_reserves_up_profile",
                 "value": "WARNING: load-following reserves up feature "
                          "disabled"},
                {"name": "project_lf_up_bas",
                 "value": "WARNING: load-following reserves up feature "
                          "disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailLoadFollowingDown(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_lf_reserves_down'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'load_following_reserves_down_profile, project_lf_down_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "load_following_reserves_down_profile",
                 "value": "WARNING: load-following reserves down feature "
                          "disabled"},
                {"name": "project_lf_down_bas",
                 "value": "WARNING: load-following reserves down feature "
                          "disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailRegulationUp(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_regulation_up'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'regulation_up_profile, project_reg_up_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "regulation_up_profile",
                 "value": "WARNING: regulation up feature disabled"},
                {"name": "project_reg_up_bas",
                 "value": "WARNING: regulation up feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailRegulationDown(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_regulation_down'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'regulation_down_profile, project_reg_down_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "regulation_down_profile",
                 "value": "WARNING: regulation down feature disabled"},
                {"name": "project_reg_down_bas",
                 "value": "WARNING: regulation down feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailSpinningReserves(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_spinning_reserves'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'spinning_reserves_profile, project_spin_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "spinning_reserves_profile",
                 "value": "WARNING: spinning reserves feature disabled"},
                {"name": "project_spin_bas",
                 "value": "WARNING: spinning reserves feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailFrequencyResponse(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_frequency_response'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'frequency_response_profile, project_freq_resp_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "frequency_response_profile",
                 "value": "WARNING: frequency response feature disabled"},
                {"name": "project_freq_resp_bas",
                 "value": "WARNING: frequency response feature disabled"}
            ]

        return scenario_detail_api


# Policy and reliability
class ScenarioDetailRPS(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_rps'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'rps_target, project_rps_areas'
            )
        else:
            scenario_detail_api = [
                {"name": "rps_target",
                 "value": "WARNING: RPS feature disabled"},
                {"name": "project_rps_areas",
                 "value": "WARNING: RPS feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailCarbonCap(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_carbon_cap') \
                and check_feature(scenario_id, 'of_track_carbon_imports'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'carbon_cap, project_carbon_cap_areas, '
                'transmission_carbon_cap_zones'
            )
        elif not check_feature(scenario_id, 'of_carbon_cap'):
            scenario_detail_api = [
                {"name": "carbon_cap",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "projefct_carbon_cap_areas",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "transmission_carbon_cap_zone_scenario_id",
                 "value": "WARNING: carbon cap feature disabled"}
            ]
        else:
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'carbon_cap, project_carbon_cap_areas, '
                '"WARNING: tracking carbon imports feature disabled" AS'
                'transmission_carbon_cap_zone_scenario_id'
            )

        return scenario_detail_api


class ScenarioDetailPRM(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_prm'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'prm_requirement, project_prm_areas, '
                'project_elcc_chars, elcc_surface, project_prm_energy_only'
            )
        elif not check_feature(scenario_id, 'of_prm'):
            scenario_detail_api = [
                {"name": "prm_requirement",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "project_prm_areas",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "elcc_surface",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "project_elcc_chars",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "project_prm_energy_only",
                 "value": "WARNING: PRM feature disabled"}
            ]
        else:
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'prm_requirement, project_prm_areas, '
                '"WARNING: ELCC surface feature disabled" AS elcc_surface, '
                'project_prm_areas, '
                '"WARNING: ELCC surface feature disabled" AS '
                'project_elcc_chars, project_prm_energy_only'
            )

        return scenario_detail_api


class ScenarioDetailLocalCapacity(Resource):
    """

    """
    @staticmethod
    def get(scenario_id):
        if check_feature(scenario_id, 'of_local_capacity'):
            scenario_detail_api = get_scenario_detail(
                scenario_id,
                'local_capacity_requirement, project_local_capacity_areas, '
                'project_local_capacity_chars'
            )
        else:
            scenario_detail_api = [
                {"name": "local_capacity_requirement",
                 "value": "WARNING: local capacity feature disabled"},
                {"name": "project_local_capacity_areas",
                 "value": "WARNING: local capacity feature disabled"},
                {"name": "project_local_capacity_chars",
                 "value": "WARNING: local capacity feature disabled"}
            ]

        return scenario_detail_api


# ### API: New Scenario Settings ### #
class SettingTemporal(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='temporal_scenario_id',
            table='subscenarios_temporal'
        )
        return setting_options_api


class SettingLoadZones(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='load_zone_scenario_id',
            table='subscenarios_geography_load_zones'
        )
        return setting_options_api


# TODO: need to require setting 'name' column to be unique
# TODO: will need to show only project_load_zone_scenario_id for the
#  selected load_zone_scenario_id
class SettingProjectLoadZones(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_load_zone_scenario_id',
            table='subscenarios_project_load_zones'
        )
        return setting_options_api


# TODO: will need to show only transmission_load_zone_scenario_id for the
#  selected load_zone_scenario_id
class SettingTxLoadZones(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='transmission_load_zone_scenario_id',
            table='subscenarios_transmission_load_zones'
        )
        return setting_options_api


class SettingSystemLoad(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='load_scenario_id',
            table='subscenarios_system_load'
        )
        return setting_options_api


class SettingProjectPorftolio(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_portfolio_scenario_id',
            table='subscenarios_project_portfolios'
        )
        return setting_options_api


class SettingProjectExistingCapacity(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_existing_capacity_scenario_id',
            table='subscenarios_project_existing_capacity'
        )
        return setting_options_api


class SettingProjectExistingFixedCost(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_existing_fixed_cost_scenario_id',
            table='subscenarios_project_existing_fixed_cost'
        )
        return setting_options_api


class SettingProjectNewCost(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_new_cost_scenario_id',
            table='subscenarios_project_new_cost'
        )
        return setting_options_api


class SettingProjectNewPotential(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_new_potential_scenario_id',
            table='subscenarios_project_new_potential'
        )
        return setting_options_api


class SettingProjectAvailability(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_availability_scenario_id',
            table='subscenarios_project_availability'
        )
        return setting_options_api


class SettingProjectOpChar(Resource):
    """

    """
    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='project_operational_chars_scenario_id',
            table='subscenarios_project_operational_chars'
        )
        return setting_options_api


class SettingFuels(Resource):
    """

    """

    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='fuel_scenario_id',
            table='subscenarios_project_fuels'
        )
        return setting_options_api


class SettingFuelPrices(Resource):
    """

    """

    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='fuel_price_scenario_id',
            table='subscenarios_project_fuel_prices'
        )
        return setting_options_api


class SettingTransmissionPortfolio(Resource):
    """

    """

    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='transmission_portfolio_scenario_id',
            table='subscenarios_transmission_portfolios'
        )
        return setting_options_api


class SettingTransmissionExistingCapacity(Resource):
    """

    """

    @staticmethod
    def get():
        setting_options_api = get_setting_options(
            id_column='transmission_existing_capacity_scenario_id',
            table='subscenarios_transmission_existing_capacity'
        )
        return setting_options_api


# ### API: Status ### #
class ServerStatus(Resource):
    """
    Server status; response will be 'running'; if HTTP error is caught,
    server status will be set to 'down'
    """
    @staticmethod
    def get():
        return 'running'


# ##### API: Routes ##### #
# ### API Routes Scenario List ### #
# Scenario list
api.add_resource(Scenarios, '/scenarios/')

# ### API Routes Scenario Detail ### #
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

# ### API Routes New Scenario Settings ### #
api.add_resource(SettingTemporal, '/scenario-settings/temporal')
api.add_resource(SettingLoadZones, '/scenario-settings/load-zones')
api.add_resource(SettingProjectLoadZones,
                 '/scenario-settings/project-load-zones')
api.add_resource(SettingTxLoadZones,
                 '/scenario-settings/tx-load-zones')
api.add_resource(SettingSystemLoad,
                 '/scenario-settings/system-load')
api.add_resource(SettingProjectPorftolio,
                 '/scenario-settings/project-portfolio')
api.add_resource(SettingProjectExistingCapacity,
                 '/scenario-settings/project-existing-capacity')
api.add_resource(SettingProjectExistingFixedCost,
                 '/scenario-settings/project-existing-fixed-cost')
api.add_resource(SettingProjectNewCost,
                 '/scenario-settings/project-new-cost')
api.add_resource(SettingProjectNewPotential,
                 '/scenario-settings/project-new-potential')
api.add_resource(SettingProjectAvailability,
                 '/scenario-settings/project-availability')
api.add_resource(SettingProjectOpChar,
                 '/scenario-settings/project-opchar')
api.add_resource(SettingFuels,
                 '/scenario-settings/fuels')
api.add_resource(SettingFuelPrices,
                 '/scenario-settings/fuel-prices')
api.add_resource(SettingTransmissionPortfolio,
                 '/scenario-settings/transmission-portfolio')
api.add_resource(SettingTransmissionExistingCapacity,
                 '/scenario-settings/transmission-existing-capacity')


# Server status
api.add_resource(ServerStatus, '/server-status')


# ### API common functions ### #
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


def get_setting_options(id_column, table):
    """

    """
    io, c = connect_to_database()

    setting_options_query = c.execute(
        """SELECT {}, name FROM {};""".format(id_column, table)
    ).fetchall()

    setting_options_api = []
    for row in setting_options_query:
        setting_options_api.append(
            {'id': row[0], 'name': row[1]}
        )

    return setting_options_api


def get_setting_option_id(id_column, table, setting_name):
    """

    :param id_column:
    :param table:
    :param setting_name:
    :return:
    """
    io, c = connect_to_database()
    setting_id = c.execute(
        """SELECT {} FROM {} WHERE name = '{}'""".format(
            id_column, table, setting_name
        )
    ).fetchone()[0]

    return setting_id


def check_feature(scenario_id, column_string):
    """

    :param scenario_id:
    :param column_string:
    :return:
    """
    io, c = connect_to_database()

    scenario_feature_on = c.execute(
        """SELECT {}
        FROM scenarios
        WHERE scenario_id = {};""".format(column_string, scenario_id)
    ).fetchone()[0]

    return scenario_feature_on

# ### Socket Communication ### #
@socketio.on('add_new_scenario')
def add_new_scenario(msg):
    print('Inserting new scenario...')

    print(msg)

    io, c = connect_to_database()

    create_scenario(
        io=io, c=c,
        scenario_name=msg['scenarioName'],
        of_fuels=1 if msg['featureFuels'] == 'yes' else 0,
        of_multi_stage='NULL',
        of_transmission=1 if msg['featureTransmission'] == 'yes' else 0,
        of_transmission_hurdle_rates=1 if msg[
            'featureTransmissionHurdleRates'] == 'yes' else 0,
        of_simultaneous_flow_limits=1 if ['featureSimFlowLimits'] == 'yes' else 0,
        of_lf_reserves_up=1 if msg['featureLFUp'] == 'yes' else 0,
        of_lf_reserves_down=1 if msg['featureLFDown'] == 'yes' else 0,
        of_regulation_up=1 if msg['featureRegUp'] == 'yes' else 0,
        of_regulation_down=1 if msg['featureRegDown'] == 'yes' else 0,
        of_frequency_response=1 if msg['featureFreqResp'] == 'yes' else 0,
        of_spinning_reserves=1 if msg['featureSpin'] == 'yes' else 0,
        of_rps=1 if msg['featureRPS'] == 'yes' else 0,
        of_carbon_cap=1 if msg['featureCarbonCap'] == 'yes' else 0,
        of_track_carbon_imports=1 if msg['featureTrackCarbonImports'] == 'yes' else 0,
        of_prm=1 if msg['featurePRM'] == 'yes' else 0,
        of_local_capacity=1 if msg['featureELCCSurface'] == 'yes' else 0,
        of_elcc_surface=1 if msg['featureLocalCapacity'] == 'yes' else 0,
        temporal_scenario_id=get_setting_option_id(
            id_column='temporal_scenario_id',
            table='subscenarios_temporal',
            setting_name=msg['temporalSetting']
        ),
        load_zone_scenario_id=get_setting_option_id(
            id_column='load_zone_scenario_id',
            table='subscenarios_geography_load_zones',
            setting_name=msg['geographyLoadZonesSetting']
        ),
        lf_reserves_up_ba_scenario_id='NULL',
        lf_reserves_down_ba_scenario_id='NULL',
        regulation_up_ba_scenario_id='NULL',
        regulation_down_ba_scenario_id='NULL',
        frequency_response_ba_scenario_id='NULL',
        spinning_reserves_ba_scenario_id='NULL',
        rps_zone_scenario_id='NULL',
        carbon_cap_zone_scenario_id='NULL',
        prm_zone_scenario_id='NULL',
        local_capacity_zone_scenario_id='NULL',
        project_portfolio_scenario_id=get_setting_option_id(
            id_column='project_portfolio_scenario_id',
            table='subscenarios_project_portfolios',
            setting_name=msg['projectPortfolioSetting']
        ),
        project_operational_chars_scenario_id=get_setting_option_id(
            id_column='project_operational_chars_scenario_id',
            table='subscenarios_project_operational_chars',
            setting_name=msg['projectOperationalCharsSetting']
        ),
        project_availability_scenario_id=get_setting_option_id(
            id_column='project_availability_scenario_id',
            table='subscenarios_project_availability',
            setting_name=msg['projectAvailabilitySetting']
        ),
        fuel_scenario_id=get_setting_option_id(
            id_column='fuel_scenario_id',
            table='subscenarios_project_fuels',
            setting_name=msg['projectFuelsSetting']
        ),
        project_load_zone_scenario_id=get_setting_option_id(
            id_column='project_load_zone_scenario_id',
            table='subscenarios_project_load_zones',
            setting_name=msg['geographyProjectLoadZonesSetting']
        ),
        project_lf_reserves_up_ba_scenario_id='NULL',
        project_lf_reserves_down_ba_scenario_id='NULL',
        project_regulation_up_ba_scenario_id='NULL',
        project_regulation_down_ba_scenario_id='NULL',
        project_frequency_response_ba_scenario_id='NULL',
        project_spinning_reserves_ba_scenario_id='NULL',
        project_rps_zone_scenario_id='NULL',
        project_carbon_cap_zone_scenario_id='NULL',
        project_prm_zone_scenario_id='NULL',
        project_elcc_chars_scenario_id='NULL',
        prm_energy_only_scenario_id='NULL',
        project_local_capacity_zone_scenario_id='NULL',
        project_local_capacity_chars_scenario_id='NULL',
        project_existing_capacity_scenario_id=get_setting_option_id(
            id_column='project_existing_capacity_scenario_id',
            table='subscenarios_project_existing_capacity',
            setting_name=msg['projectExistingCapacitySetting']
        ),
        project_existing_fixed_cost_scenario_id=get_setting_option_id(
            id_column='project_existing_fixed_cost_scenario_id',
            table='subscenarios_project_existing_fixed_cost',
            setting_name=msg['projectExistingFixedCostSetting']
        ),
        fuel_price_scenario_id=get_setting_option_id(
            id_column='fuel_price_scenario_id',
            table='subscenarios_project_fuel_prices',
            setting_name=msg['fuelPricesSetting']
        ),
        project_new_cost_scenario_id=get_setting_option_id(
            id_column='project_new_cost_scenario_id',
            table='subscenarios_project_new_cost',
            setting_name=msg['projectNewCostSetting']
        ),
        project_new_potential_scenario_id=get_setting_option_id(
            id_column='project_new_potential_scenario_id',
            table='subscenarios_project_new_potential',
            setting_name=msg['projectNewPotentialSetting']
        ),
        transmission_portfolio_scenario_id=get_setting_option_id(
            id_column='transmission_portfolio_scenario_id',
            table='subscenarios_transmission_portfolios',
            setting_name=msg['transmissionPortfolioSetting']
        ),
        transmission_load_zone_scenario_id=get_setting_option_id(
            id_column='transmission_load_zone_scenario_id',
            table='subscenarios_transmission_load_zones',
            setting_name=msg['geographyTxLoadZonesSetting']
        ),
        transmission_existing_capacity_scenario_id=get_setting_option_id(
            id_column='transmission_existing_capacity_scenario_id',
            table='subscenarios_transmission_existing_capacity',
            setting_name=msg['transmissionExistingCapacitySetting']
        ),
        transmission_operational_chars_scenario_id='NULL',
        transmission_hurdle_rate_scenario_id='NULL',
        transmission_carbon_cap_zone_scenario_id='NULL',
        transmission_simultaneous_flow_limit_scenario_id='NULL',
        transmission_simultaneous_flow_limit_line_group_scenario_id='NULL',
        load_scenario_id=get_setting_option_id(
            id_column='load_scenario_id',
            table='subscenarios_system_load',
            setting_name=msg['systemLoadSetting']
        ),
        lf_reserves_up_scenario_id='NULL',
        lf_reserves_down_scenario_id='NULL',
        regulation_up_scenario_id='NULL',
        regulation_down_scenario_id='NULL',
        frequency_response_scenario_id='NULL',
        spinning_reserves_scenario_id='NULL',
        rps_target_scenario_id='NULL',
        carbon_cap_target_scenario_id='NULL',
        prm_requirement_scenario_id='NULL',
        elcc_surface_scenario_id='NULL',
        local_capacity_requirement_scenario_id='NULL',
        tuning_scenario_id='NULL'
    )


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
    # io = sqlite3.connect('/Users/ana/dev/gridpath-ui-dev/db/io.db')
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
