import atexit
from flask import Flask
from flask_socketio import SocketIO, emit
import os
import psutil
import signal
import sqlite3
import subprocess
import sys

from flask_restful import Resource, Api

# Gridpath modules
from db.utilities.create_scenario import create_scenario
from db.utilities.update_scenario import update_scenario_multiple_columns


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

# ### API: Scenarios List ### #
class Scenarios(Resource):
    """
    The list of scenarios.
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        io, c = connect_to_database(self.db_path)

        scenarios_query = c.execute(
            """SELECT scenario_id, scenario_name, validation_status, run_status
            FROM scenarios_view
            ORDER by scenario_id ASC;"""
        )

        scenarios_api = []
        for s in scenarios_query:
            # TODO: make this more robust than relying on column order
            scenarios_api.append(
                {'id': s[0], 'name': s[1], 'validationStatus': s[2],
                 'runStatus': s[3]}
            )

        return scenarios_api


# ### API: Scenario Detail ### #
class ScenarioDetailName(Resource):
    """
    The name of the a scenario by scenario ID
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='scenario_name'
        )[0]["value"]

        return scenario_detail_api


class ScenarioDetailAll(Resource):
    """
    All settings for a scenario ID.
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='*'
        )

        scenario_edit_api = {}
        for column in scenario_detail_api:
            scenario_edit_api[column['name']] = column['value']

        return scenario_edit_api


class ScenarioDetailFeatures(Resource):
    """
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string=
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='temporal'
        )

        return scenario_detail_api


class ScenarioDetailGeographyLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_load_zones, project_load_zones, '
                               'transmission_load_zones'
            )
        else:
            scenario_detail_api = get_scenario_detail(
              db_path=self.db_path,
              scenario_id=scenario_id,
              columns_string='geography_load_zones, project_load_zones, '
                             '"WARNING: transmission feature disabled" AS '
                             'transmission_load_zones'
            )

        return scenario_detail_api


class ScenarioDetailLoad(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='load_profile'
        )

        return scenario_detail_api


class ScenarioDetailProjectCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='project_portfolio, project_existing_capacity, '
                           'project_existing_fixed_cost, project_new_cost, '
                           'project_new_potential, project_availability'
        )

        return scenario_detail_api


class ScenarioDetailProjectOpChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='project_operating_chars'
        )

        return scenario_detail_api


class ScenarioDetailFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_fuels'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='project_fuels, fuel_prices'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='transmission_portfolio, '
                               'transmission_existing_capacity '
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='transmission_operational_chars'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string=
                                  'of_transmission_hurdle_rates'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='transmission_hurdle_rates'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and not check_feature(db_path=self.db_path,
                                      scenario_id=scenario_id,
                                      column_string=
                                      'of_transmission_hurdle_rates'):
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: both transmission and transmission "
                          "hurdle rates features disabled"}
            ]
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string=
                                  'of_transmission_hurdle_rates'):
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string='of_simultaneous_flow_limits'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string=
                'transmission_simultaneous_flow_limits, '
                'transmission_simultaneous_flow_limit_line_groups'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and not check_feature(db_path=self.db_path,
                                      scenario_id=scenario_id,
                                      column_string=
                                      'of_simultaneous_flow_limits'):
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: both transmission and simultaneous flow "
                          "limits features disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: both transmission and simultaneous flow "
                          "limits features disabled"}
            ]
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string='of_simultaneous_flow_limits'):
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_lf_reserves_up'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_lf_up_bas, '
                               'load_following_reserves_up_profile, '
                               'project_lf_up_bas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_lf_reserves_down'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_lf_down_bas, '
                               'load_following_reserves_down_profile, '
                               'project_lf_down_bas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_regulation_up'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_reg_up_bas, '
                               'regulation_up_profile, '
                               'project_reg_up_bas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_regulation_down'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_reg_down_bas, '
                               'regulation_down_profile, '
                               'project_reg_down_bas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_spinning_reserves'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_spin_bas, '
                               'spinning_reserves_profile, '
                               'project_spin_bas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_frequency_response'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_freq_resp_bas, '
                               'frequency_response_profile, '
                               'project_freq_resp_bas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_rps'):
            scenario_detail_api = get_scenario_detail(
              db_path=self.db_path,
              scenario_id=scenario_id,
              columns_string='geography_rps_areas, '
                             'rps_target, '
                             'project_rps_areas'
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_carbon_cap') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string='of_track_carbon_imports'):
            scenario_detail_api = get_scenario_detail(
              db_path=self.db_path,
              scenario_id=scenario_id,
              columns_string='carbon_cap_areas, '
                             'carbon_cap, '
                             'project_carbon_cap_areas, '
                             'transmission_carbon_cap_zones'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_carbon_cap'):
            scenario_detail_api = [
                {"name": "carbon_cap_areas",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "carbon_cap",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "projefct_carbon_cap_areas",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "transmission_carbon_cap_zone_scenario_id",
                 "value": "WARNING: carbon cap feature disabled"}
            ]
        else:
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='carbon_cap_areas, '
                               'carbon_cap, '
                               'project_carbon_cap_areas, '
                               '"WARNING: tracking carbon imports feature '
                               'disabled" AS'
                               'transmission_carbon_cap_zone_scenario_id'
            )

        return scenario_detail_api


class ScenarioDetailPRM(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_prm'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='prm_areas, '
                               'prm_requirement, '
                               'project_prm_areas, '
                               'project_elcc_chars, '
                               'elcc_surface, '
                               'project_prm_energy_only'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_prm'):
            scenario_detail_api = [
                {"name": "prm_areas",
                 "value": "WARNING: PRM feature disabled"},
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
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='prm_areas, '
                               'prm_requirement, '
                               'project_prm_areas, '
                               '"WARNING: ELCC surface feature disabled" '
                               'AS elcc_surface, '
                               'project_prm_areas, '
                               '"WARNING: ELCC surface feature disabled" '
                               'AS project_elcc_chars, '
                               'project_prm_energy_only'
            )

        return scenario_detail_api


class ScenarioDetailLocalCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_local_capacity'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='local_capacity_areas, '
                               'local_capacity_requirement, '
                               'project_local_capacity_areas, '
                               'project_local_capacity_chars'
            )
        else:
            scenario_detail_api = [
                {"name": "local_capacity_areas",
                 "value": "WARNING: local capacity feature disabled"},
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
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='temporal_scenario_id',
            table='subscenarios_temporal'
        )
        return setting_options_api


class SettingLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
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

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_load_zone_scenario_id',
            table='subscenarios_project_load_zones'
        )
        return setting_options_api


# TODO: will need to show only transmission_load_zone_scenario_id for the
#  selected load_zone_scenario_id
class SettingTxLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
      self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_load_zone_scenario_id',
            table='subscenarios_transmission_load_zones'
        )
        return setting_options_api


class SettingSystemLoad(Resource):
    """

    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='load_scenario_id',
            table='subscenarios_system_load'
        )
        return setting_options_api


class SettingProjectPorftolio(Resource):
    """

    """

    def __init__(self, **kwargs):
      self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_portfolio_scenario_id',
            table='subscenarios_project_portfolios'
        )
        return setting_options_api


class SettingProjectExistingCapacity(Resource):
    """

    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_existing_capacity_scenario_id',
            table='subscenarios_project_existing_capacity'
        )
        return setting_options_api


class SettingProjectExistingFixedCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_existing_fixed_cost_scenario_id',
            table='subscenarios_project_existing_fixed_cost'
        )
        return setting_options_api


class SettingProjectNewCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_new_cost_scenario_id',
            table='subscenarios_project_new_cost'
        )
        return setting_options_api


class SettingProjectNewPotential(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_new_potential_scenario_id',
            table='subscenarios_project_new_potential'
        )
        return setting_options_api


class SettingProjectAvailability(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_availability_scenario_id',
            table='subscenarios_project_availability'
        )
        return setting_options_api


class SettingProjectOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_operational_chars_scenario_id',
            table='subscenarios_project_operational_chars'
        )
        return setting_options_api


class SettingFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='fuel_scenario_id',
            table='subscenarios_project_fuels'
        )
        return setting_options_api


class SettingFuelPrices(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='fuel_price_scenario_id',
            table='subscenarios_project_fuel_prices'
        )
        return setting_options_api


class SettingTransmissionPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_portfolio_scenario_id',
            table='subscenarios_transmission_portfolios'
        )
        return setting_options_api


class SettingTransmissionExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_existing_capacity_scenario_id',
            table='subscenarios_transmission_existing_capacity'
        )
        return setting_options_api


class SettingTransmissionOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_operational_chars_scenario_id',
            table='subscenarios_transmission_operational_chars'
        )
        return setting_options_api


class SettingTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_hurdle_rate_scenario_id',
            table='subscenarios_transmission_hurdle_rates'
        )
        return setting_options_api


class SettingTransmissionSimFlowLimits(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_simultaneous_flow_limit_scenario_id',
            table='subscenarios_transmission_simultaneous_flow_limits'
        )
        return setting_options_api


class SettingTransmissionSimFlowLimitGroups(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column=
            'transmission_simultaneous_flow_limit_line_group_scenario_id',
            table=
            'subscenarios_transmission_simultaneous_flow_limit_line_groups'
        )
        return setting_options_api


class SettingLFReservesUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='lf_reserves_up_ba_scenario_id',
            table='subscenarios_geography_lf_reserves_up_bas'
        )
        return setting_options_api


# TODO: link two IDs
class SettingProjectLFReservesUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_lf_reserves_up_ba_scenario_id',
            table='subscenarios_project_lf_reserves_up_bas'
        )
        return setting_options_api


class SettingLFReservesUpRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='lf_reserves_up_scenario_id',
            table='subscenarios_system_lf_reserves_up'
        )
        return setting_options_api
 
    
class SettingLFReservesDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='lf_reserves_down_ba_scenario_id',
            table='subscenarios_geography_lf_reserves_down_bas'
        )
        return setting_options_api


# TODO: link two IDs
class SettingProjectLFReservesDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_lf_reserves_down_ba_scenario_id',
            table='subscenarios_project_lf_reserves_down_bas'
        )
        return setting_options_api


class SettingLFReservesDownRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='lf_reserves_down_scenario_id',
            table='subscenarios_system_lf_reserves_down'
        )
        return setting_options_api


class SettingRegulationUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='regulation_up_ba_scenario_id',
            table='subscenarios_geography_regulation_up_bas'
        )
        return setting_options_api


class SettingProjectRegulationUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_regulation_up_ba_scenario_id',
            table='subscenarios_project_regulation_up_bas'
        )
        return setting_options_api


class SettingRegulationUpRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='regulation_up_scenario_id',
            table='subscenarios_system_regulation_up'
        )
        return setting_options_api


class SettingRegulationDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='regulation_down_ba_scenario_id',
            table='subscenarios_geography_regulation_down_bas'
        )
        return setting_options_api


class SettingProjectRegulationDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_regulation_down_ba_scenario_id',
            table='subscenarios_project_regulation_down_bas'
        )
        return setting_options_api


class SettingRegulationDownRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='regulation_down_scenario_id',
            table='subscenarios_system_regulation_down'
        )
        return setting_options_api


class SettingSpinningReservesBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='spinning_reserves_ba_scenario_id',
            table='subscenarios_geography_spinning_reserves_bas'
        )
        return setting_options_api


class SettingProjectSpinningReservesBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_spinning_reserves_ba_scenario_id',
            table='subscenarios_project_spinning_reserves_bas'
        )
        return setting_options_api


class SettingSpinningReservesRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='spinning_reserves_scenario_id',
            table='subscenarios_system_spinning_reserves'
        )
        return setting_options_api
    
    
class SettingFrequencyResponseBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='frequency_response_ba_scenario_id',
            table='subscenarios_geography_frequency_response_bas'
        )
        return setting_options_api


class SettingProjectFrequencyResponseBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_frequency_response_ba_scenario_id',
            table='subscenarios_project_frequency_response_bas'
        )
        return setting_options_api


class SettingFrequencyResponseRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='frequency_response_scenario_id',
            table='subscenarios_system_frequency_response'
        )
        return setting_options_api


class SettingRPSAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='rps_zone_scenario_id',
            table='subscenarios_geography_rps_zones'
        )
        return setting_options_api


# TODO: link two IDs
class SettingProjectRPSAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_rps_zone_scenario_id',
            table='subscenarios_project_rps_zones'
        )
        return setting_options_api


class SettingRPSRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='rps_target_scenario_id',
            table='subscenarios_system_rps_targets'
        )
        return setting_options_api
    

class SettingCarbonCapAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='carbon_cap_zone_scenario_id',
            table='subscenarios_geography_carbon_cap_zones'
        )
        return setting_options_api


# TODO: link two IDs
class SettingProjectCarbonCapAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_carbon_cap_zone_scenario_id',
            table='subscenarios_project_carbon_cap_zones'
        )
        return setting_options_api


class SettingTransmissionCarbonCapAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='transmission_carbon_cap_zone_scenario_id',
            table='subscenarios_transmission_carbon_cap_zones'
        )
        return setting_options_api


class SettingCarbonCapRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='carbon_cap_target_scenario_id',
            table='subscenarios_system_carbon_cap_targets'
        )
        return setting_options_api


class SettingPRMAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='prm_zone_scenario_id',
            table='subscenarios_geography_prm_zones'
        )
        return setting_options_api


class SettingPRMRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='prm_requirement_scenario_id',
            table='subscenarios_system_prm_requirement'
        )
        return setting_options_api


class SettingProjectPRMAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_prm_zone_scenario_id',
            table='subscenarios_project_prm_zones'
        )
        return setting_options_api


# TODO: two ids
class SettingProjectELCCChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_elcc_chars_scenario_id',
            table='subscenarios_project_elcc_chars'
        )
        return setting_options_api


class SettingProjectPRMEnergyOnly(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='prm_energy_only_scenario_id',
            table='subscenarios_project_prm_energy_only'
        )
        return setting_options_api


class SettingELCCSurface(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='elcc_surface_scenario_id',
            table='subscenarios_system_elcc_surface'
        )
        return setting_options_api


class SettingLocalCapacityAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='local_capacity_zone_scenario_id',
            table='subscenarios_geography_local_capacity_zones'
        )
        return setting_options_api


class SettingLocalCapacityRequirement(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='local_capacity_requirement_scenario_id',
            table='subscenarios_system_local_capacity_requirement'
        )
        return setting_options_api


class SettingProjectLocalCapacityAreas(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_local_capacity_zone_scenario_id',
            table='subscenarios_project_local_capacity_zones'
        )
        return setting_options_api


class SettingProjectLocalCapacityChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='project_local_capacity_chars_scenario_id',
            table='subscenarios_project_local_capacity_chars'
        )
        return setting_options_api


class SettingTuning(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        setting_options_api = get_setting_options(
            db_path=self.db_path,
            id_column='tuning_scenario_id',
            table='subscenarios_tuning'
        )
        return setting_options_api


# ### API: View Data ### #
# TODO: add the subscenario names (not just IDs) to the inputs tables --
#  this will make it easier to show the right information to the user
#  without having to resort to JOINS

class ViewDataTemporalTimepoints(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='temporal',
            caption='Timepoints',
            table='inputs_temporal_timepoints'
        )


class ViewDataGeographyLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_load_zones',
            caption='Load Zones',
            table='inputs_geography_load_zones'
        )


class ViewDataProjectLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_load_zones',
            caption='Project Load Zones',
            table='inputs_project_load_zones'
        )


class ViewDataTransmissionLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_load_zones',
            caption='Transmission Load Zones',
            table='inputs_transmission_load_zones'
        )


class ViewDataSystemLoad(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='load_profile',
            caption='System Load',
            table='inputs_system_load'
        )


class ViewDataProjectPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_portfolio',
            caption='Project Portfolio',
            table='inputs_project_portfolios'
        )


class ViewDataProjectExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_existing_capacity',
            caption='Project Specified Capacity',
            table='inputs_project_existing_capacity'
        )


class ViewDataProjectExistingFixedCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_existing_fixed_cost',
            caption='Project Specified Fixed Cost',
            table='inputs_project_existing_fixed_cost'
        )


class ViewDataProjectNewPotential(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_new_potential',
            caption='Project New Potential',
            table='inputs_project_new_potential'
        )


class ViewDataProjectNewCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_new_cost',
            caption='Project New Costs',
            table='inputs_project_new_cost'
        )


class ViewDataProjectAvailability(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_availability',
            caption='Project Availability',
            table='inputs_project_availability'
        )


class ViewDataProjectOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_operating_chars',
            caption='Project Operational Characteristics',
            table='inputs_project_operational_chars'
        )


class ViewDataFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_fuels',
            caption='Fuels',
            table='inputs_project_fuels'
        )


class ViewDataFuelPrices(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='fuel_prices',
            caption='Fuel Prices',
            table='inputs_project_fuel_prices'
        )


class ViewDataTransmissionPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_portfolio',
            caption='Transmission',
            table='inputs_transmission_portfolios'
        )


class ViewDataTransmissionExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_existing_capacity',
            caption='Transmission Specified Capacity',
            table='inputs_transmission_existing_capacity'
        )


class ViewDataTransmissionOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_operational_chars',
            caption='Transmission Operational Characteristics',
            table='inputs_transmission_operational_chars'
        )


class ViewDataTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_hurdle_rates',
            caption='Transmission Hurdle Rates',
            table='inputs_transmission_hurdle_rates'
        )


class ViewDataTransmissionSimFlowLimits(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_simultaneous_flow_limits',
            caption='Transmission Simultaneous Flow Limits',
            table='inputs_transmission_simultaneous_flow_limits'
        )


class ViewDataTransmissionSimFlowLimitsLineGroups(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_simultaneous_flow_limit_line_groups',
            caption='Transmission Simultaneous Flow Limits Line Groups',
            table='inputs_transmission_simultaneous_flow_limit_line_groups'
        )


class ViewDataLFUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_lf_up_bas',
            caption='Load Following Up Balancing Areas',
            table='inputs_geography_lf_reserves_up_bas'
        )


class ViewDataProjectLFUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_lf_up_bas',
            caption='Project Load Following Up Balancing Areas',
            table='inputs_project_lf_reserves_up_bas'
        )


class ViewDataLFUpReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='load_following_reserves_up_profile',
            caption='Load Following Up Requirement',
            table='inputs_system_lf_reserves_up'
        )


class ViewDataLFDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_lf_down_bas',
            caption='Load Following Down Balancing Areas',
            table='inputs_geography_lf_reserves_down_bas'
        )


class ViewDataProjectLFDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_lf_down_bas',
            caption='Project Load Following Down Balancing Areas',
            table='inputs_project_lf_reserves_down_bas'
        )


class ViewDataLFDownReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='load_following_reserves_down_profile',
            caption='Load Following Down Requirement',
            table='inputs_system_lf_reserves_down'
        )


class ViewDataRegUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_reg_up_bas',
            caption='Regulation Up Balancing Areas',
            table='inputs_geography_regulation_up_bas'
        )


class ViewDataProjectRegUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_reg_up_bas',
            caption='Project Regulation Up Balancing Areas',
            table='inputs_project_regulation_up_bas'
        )


class ViewDataRegUpReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='regulation_up_profile',
            caption='Regulation Up Requirement',
            table='inputs_system_regulation_up'
        )


class ViewDataRegDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_reg_down_bas',
            caption='Regulation Down Balancing Areas',
            table='inputs_geography_regulation_down_bas'
        )


class ViewDataProjectRegDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_reg_down_bas',
            caption='Project Regulation Down Balancing Areas',
            table='inputs_project_regulation_down_bas'
        )


class ViewDataRegDownReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='regulation_down_profile',
            caption='Regulation Down Requirement',
            table='inputs_system_regulation_down'
        )


class ViewDataSpinBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_spin_bas',
            caption='Spinning Reserves Balancing Areas',
            table='inputs_geography_spinning_reserves_bas'
        )


class ViewDataProjectSpinBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_spin_bas',
            caption='Project Spinning Reserves Balancing Areas',
            table='inputs_project_spinning_reserves_bas'
        )


class ViewDataSpinReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='spinning_reserves_profile',
            caption='Spinning Reserves Requirement',
            table='inputs_system_spinning_reserves'
        )


class ViewDataFreqRespBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_freq_resp_bas',
            caption='Frequency Response Balancing Areas',
            table='inputs_geography_frequency_response_bas'
        )


class ViewDataProjectFreqRespBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_freq_resp_bas',
            caption='Project Frequency Response Balancing Areas',
            table='inputs_project_frequency_response_bas'
        )


class ViewDataFreqRespReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='frequency_response_profile',
            caption='Frequency Response Requirement',
            table='inputs_system_frequency_response'
        )


class ViewDataRPSBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_rps_areas',
            caption='RPS Areas',
            table='inputs_geography_rps_zones'
        )


class ViewDataProjectRPSBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_rps_areas',
            caption='Project RPS Areas',
            table='inputs_project_rps_zones'
        )


class ViewDataRPSReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='rps_target',
            caption='RPS Target',
            table='inputs_system_rps_targets'
        )


class ViewDataCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='geography_carbon_cap_areas',
            caption='Carbon Cap Areas',
            table='inputs_geography_carbon_cap_zones'
        )


class ViewDataProjectCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_carbon_cap_areas',
            caption='Project Carbon Cap Areas',
            table='inputs_project_carbon_cap_zones'
        )


class ViewDataTransmissionCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='transmission_carbon_cap_zones',
            caption='Transmission Carbon Cap Areas',
            table='inputs_transmission_carbon_cap_zones'
        )


class ViewDataCarbonCapReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='carbon_cap_target',
            caption='Carbon Cap Target',
            table='inputs_system_carbon_cap_targets'
        )
    

class ViewDataPRMBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='prm_areas',
            caption='PRM Areas',
            table='inputs_geography_prm_zones'
        )


class ViewDataProjectPRMBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_prm_areas',
            caption='Project PRM Areas',
            table='inputs_project_prm_zones'
        )


class ViewDataPRMReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='prm_requirement',
            caption='PRM Target',
            table='inputs_system_prm_requirement'
        )


class ViewDataProjectELCCChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_elcc_chars',
            caption='Project ELCC Characteristics',
            table='inputs_project_elcc_chars'
        )


class ViewDataELCCSurface(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='elcc_surface',
            caption='ELCC Surface',
            table='inputs_project_elcc_surface'
        )


class ViewDataEnergyOnly(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_prm_energy_only',
            caption='Project Energy-Only Characteristics',
            table='inputs_project_prm_energy_only'
        )


class ViewDataLocalCapacityBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='local_capacity_areas',
            caption='Local Capacity Areas',
            table='inputs_geography_local_capacity_zones'
        )


class ViewDataProjectLocalCapacityBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_local_capacity_areas',
            caption='Project Local Capacity Areas',
            table='inputs_project_local_capacity_zones'
        )


class ViewDataLocalCapacityReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='local_capacity_requirement',
            caption='Local Capacity Target',
            table='inputs_system_local_capacity_requirement'
        )


class ViewDataProjectLocalCapacityChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]
        
    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='project_local_capacity_chars',
            caption='Project Local Capacity Characteristics',
            table='inputs_project_local_capacity_chars'
        )
    

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
api.add_resource(Scenarios, '/scenarios/',
                 resource_class_kwargs={'db_path': DATABASE_PATH}
)

# ### API Routes Scenario Detail ### #
# Name
# TODO: is this used?
api.add_resource(
    ScenarioDetailName,
    '/scenarios/<scenario_id>/name',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# All
api.add_resource(
  ScenarioDetailAll,
  '/scenarios/<scenario_id>',
  resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Features
api.add_resource(
    ScenarioDetailFeatures,
    '/scenarios/<scenario_id>/features',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Temporal
api.add_resource(
    ScenarioDetailTemporal,
    '/scenarios/<scenario_id>/temporal',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Geography load zones
api.add_resource(
    ScenarioDetailGeographyLoadZones,
    '/scenarios/<scenario_id>/geography-load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# System load
api.add_resource(
    ScenarioDetailLoad,
    '/scenarios/<scenario_id>/load',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Project capacity
api.add_resource(
    ScenarioDetailProjectCapacity,
    '/scenarios/<scenario_id>/project-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Project operating characteristics
api.add_resource(
    ScenarioDetailProjectOpChars,
    '/scenarios/<scenario_id>/project-opchars',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Fuels
api.add_resource(
    ScenarioDetailFuels,
    '/scenarios/<scenario_id>/fuels',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Transmission capacity
api.add_resource(
    ScenarioDetailTransmissionCapacity,
    '/scenarios/<scenario_id>/transmission-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Transmission operating characteristics
api.add_resource(
    ScenarioDetailTransmissionOpChars,
    '/scenarios/<scenario_id>/transmission-opchars',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Transmission hurdle rates
api.add_resource(
    ScenarioDetailTransmissionHurdleRates,
    '/scenarios/<scenario_id>/transmission-hurdle-rates',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Transmission simultaneous flow limits
api.add_resource(
    ScenarioDetailTransmissionSimFlow,
    '/scenarios/<scenario_id>/transmission-sim-flow',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Reserves
api.add_resource(
    ScenarioDetailLoadFollowingUp,
    '/scenarios/<scenario_id>/lf-up',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailLoadFollowingDown,
    '/scenarios/<scenario_id>/lf-down',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailRegulationUp,
    '/scenarios/<scenario_id>/reg-up',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailRegulationDown,
    '/scenarios/<scenario_id>/reg-down',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailSpinningReserves,
    '/scenarios/<scenario_id>/spin',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailFrequencyResponse,
    '/scenarios/<scenario_id>/freq-resp',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
# Policy and reliability
api.add_resource(
    ScenarioDetailRPS,
    '/scenarios/<scenario_id>/rps',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailCarbonCap,
    '/scenarios/<scenario_id>/carbon-cap',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailPRM,
    '/scenarios/<scenario_id>/prm',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    ScenarioDetailLocalCapacity,
    '/scenarios/<scenario_id>/local-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

# ### API Routes New Scenario Settings ### #
api.add_resource(
    SettingTemporal, '/scenario-settings/temporal',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLoadZones,
    '/scenario-settings/load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectLoadZones,
    '/scenario-settings/project-load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTxLoadZones,
    '/scenario-settings/tx-load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingSystemLoad,
    '/scenario-settings/system-load',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectPorftolio,
    '/scenario-settings/project-portfolio',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectExistingCapacity,
    '/scenario-settings/project-existing-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectExistingFixedCost,
    '/scenario-settings/project-existing-fixed-cost',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectNewCost,
    '/scenario-settings/project-new-cost',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectNewPotential,
    '/scenario-settings/project-new-potential',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectAvailability,
    '/scenario-settings/project-availability',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectOpChar,
    '/scenario-settings/project-opchar',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingFuels,
    '/scenario-settings/fuels',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingFuelPrices,
    '/scenario-settings/fuel-prices',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionPortfolio,
    '/scenario-settings/transmission-portfolio',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionExistingCapacity,
    '/scenario-settings/transmission-existing-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionOpChar,
    '/scenario-settings/transmission-opchar',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionHurdleRates,
    '/scenario-settings/transmission-hurdle-rates',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionSimFlowLimits,
    '/scenario-settings/transmission-simflow-limits',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionSimFlowLimitGroups,
    '/scenario-settings/transmission-simflow-limit-groups',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLFReservesUpBAs,
    '/scenario-settings/lf-reserves-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectLFReservesUpBAs,
    '/scenario-settings/project-lf-reserves-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLFReservesUpRequirement,
    '/scenario-settings/lf-reserves-up-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLFReservesDownBAs,
    '/scenario-settings/lf-reserves-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectLFReservesDownBAs,
    '/scenario-settings/project-lf-reserves-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLFReservesDownRequirement,
    '/scenario-settings/lf-reserves-down-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingRegulationUpBAs,
    '/scenario-settings/regulation-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectRegulationUpBAs,
    '/scenario-settings/project-regulation-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingRegulationUpRequirement,
    '/scenario-settings/regulation-up-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingRegulationDownBAs,
    '/scenario-settings/regulation-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectRegulationDownBAs,
    '/scenario-settings/project-regulation-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingRegulationDownRequirement,
                 '/scenario-settings/regulation-down-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingSpinningReservesBAs,
    '/scenario-settings/spin-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectSpinningReservesBAs,
    '/scenario-settings/project-spin-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingSpinningReservesRequirement,
    '/scenario-settings/spin-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingFrequencyResponseBAs,
    '/scenario-settings/freq-resp-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectFrequencyResponseBAs,
    '/scenario-settings/project-freq-resp-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingFrequencyResponseRequirement,
    '/scenario-settings/freq-resp-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingRPSAreas,
    '/scenario-settings/rps-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectRPSAreas,
    '/scenario-settings/project-rps-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingRPSRequirement,
    '/scenario-settings/rps-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    SettingCarbonCapAreas,
  '/scenario-settings/carbon-cap-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectCarbonCapAreas,
    '/scenario-settings/project-carbon-cap-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTransmissionCarbonCapAreas,
    '/scenario-settings/transmission-carbon-cap-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingCarbonCapRequirement,
    '/scenario-settings/carbon-cap-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    SettingPRMAreas,
    '/scenario-settings/prm-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingPRMRequirement,
    '/scenario-settings/prm-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectPRMAreas,
    '/scenario-settings/project-prm-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingELCCSurface,
    '/scenario-settings/elcc-surface',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectELCCChars,
    '/scenario-settings/project-elcc-chars',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectPRMEnergyOnly,
    '/scenario-settings/project-energy-only',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLocalCapacityAreas,
    '/scenario-settings/local-capacity-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectLocalCapacityAreas,
    '/scenario-settings/project-local-capacity-areas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingLocalCapacityRequirement,
    '/scenario-settings/local-capacity-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingProjectLocalCapacityChars,
    '/scenario-settings/project-local-capacity-chars',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)
api.add_resource(
    SettingTuning,
    '/scenario-settings/tuning',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

# ### API Routes View Input Data Tables ### #
api.add_resource(
    ViewDataTemporalTimepoints,
    '/view-data/temporal-timepoints',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataGeographyLoadZones,
    '/view-data/geography-load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectLoadZones,
    '/view-data/project-load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionLoadZones,
    '/view-data/transmission-load-zones',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataSystemLoad,
    '/view-data/system-load',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectPortfolio,
    '/view-data/project-portfolio',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectExistingCapacity,
    '/view-data/project-existing-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectExistingFixedCost,
    '/view-data/project-fixed-cost',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectNewPotential,
    '/view-data/project-new-potential',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectNewCost,
    '/view-data/project-new-cost',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectAvailability,
    '/view-data/project-availability',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectOpChar,
    '/view-data/project-opchar',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataFuels,
    '/view-data/fuels',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataFuelPrices,
    '/view-data/fuel-prices',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionPortfolio,
    '/view-data/transmission-portfolio',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionExistingCapacity,
    '/view-data/transmission-existing-capacity',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionOpChar,
    '/view-data/transmission-opchar',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionHurdleRates,
    '/view-data/transmission-hurdle-rates',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionSimFlowLimits,
    '/view-data/transmission-sim-flow-limits',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionSimFlowLimitsLineGroups,
    '/view-data/transmission-sim-flow-limit-line-groups',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataLFUpBAs,
    '/view-data/geography-lf-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectLFUpBAs,
    '/view-data/project-lf-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataLFUpReq,
    '/view-data/system-lf-up-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataLFDownBAs,
    '/view-data/geography-lf-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectLFDownBAs,
    '/view-data/project-lf-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataLFDownReq,
    '/view-data/system-lf-down-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataRegUpBAs,
    '/view-data/geography-reg-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectRegUpBAs,
    '/view-data/project-reg-up-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataRegUpReq,
    '/view-data/system-reg-up-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataRegDownBAs,
    '/view-data/geography-reg-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectRegDownBAs,
    '/view-data/project-reg-down-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataRegDownReq,
    '/view-data/system-reg-down-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataSpinBAs,
    '/view-data/geography-spin-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectSpinBAs,
    '/view-data/project-spin-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataSpinReq,
    '/view-data/system-spin-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataFreqRespBAs,
    '/view-data/geography-freq-resp-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectFreqRespBAs,
    '/view-data/project-freq-resp-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataFreqRespReq,
    '/view-data/system-freq-resp-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)


api.add_resource(
    ViewDataRPSBAs,
    '/view-data/geography-rps-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectRPSBAs,
    '/view-data/project-rps-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataRPSReq,
    '/view-data/system-rps-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataCarbonCapBAs,
    '/view-data/geography-carbon-cap-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectCarbonCapBAs,
    '/view-data/project-carbon-cap-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataTransmissionCarbonCapBAs,
    '/view-data/transmission-carbon-cap-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataCarbonCapReq,
    '/view-data/system-carbon-cap-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataPRMBAs,
    '/view-data/geography-prm-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectPRMBAs,
    '/view-data/project-prm-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataPRMReq,
    '/view-data/system-prm-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectELCCChars,
    '/view-data/project-elcc-chars',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataELCCSurface,
    '/view-data/project-elcc-surface',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataEnergyOnly,
    '/view-data/project-energy-only')

api.add_resource(
    ViewDataLocalCapacityBAs,
    '/view-data/geography-local-capacity-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectLocalCapacityBAs,
    '/view-data/project-local-capacity-bas',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataLocalCapacityReq,
    '/view-data/local-capacity-req',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)

api.add_resource(
    ViewDataProjectLocalCapacityChars,
    '/view-data/project-local-capacity-chars',
    resource_class_kwargs={'db_path': DATABASE_PATH}
)


# ### API Routes Server Status ### #
api.add_resource(ServerStatus, '/server-status')


# ### API common functions ### #
def get_scenario_detail(db_path, scenario_id, columns_string):
    """
    :param db_path: the path to the database
    :param scenario_id: integer, the scenario ID
    :param columns_string: string defining which columns to select
    :return:


    """
    io, c = connect_to_database(db_path=db_path)

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


def get_setting_options(db_path, id_column, table):
    """
    :param db_path: the path to the database file
    :param id_column: subscenario ID column name
    :param table: the table to select from
    :return: 
    """
    io, c = connect_to_database(db_path=db_path)

    setting_options_query = c.execute(
        """SELECT {}, name FROM {};""".format(id_column, table)
    ).fetchall()

    setting_options_api = []
    for row in setting_options_query:
        setting_options_api.append(
            {'id': row[0], 'name': row[1]}
        )

    return setting_options_api


def get_setting_option_id(db_path, id_column, table, setting_name):
    """
    :param db_path: the path to the database file
    :param id_column:
    :param table:
    :param setting_name:
    :return:
    """
    io, c = connect_to_database(db_path=db_path)
    setting_id = c.execute(
        """SELECT {} FROM {} WHERE name = '{}'""".format(
            id_column, table, setting_name
        )
    ).fetchone()[0]

    return setting_id


def check_feature(db_path, scenario_id, column_string):
    """
    :param db_path: path to to the database file
    :param scenario_id: integer, the scenario_id value in the database
    :param column_string: the columns to check
    :return: 1 or 0, depending on whether the feature is selected
    """
    io, c = connect_to_database(db_path=db_path)

    scenario_feature_on = c.execute(
        """SELECT {}
        FROM scenarios
        WHERE scenario_id = {};""".format(column_string, scenario_id)
    ).fetchone()[0]

    return scenario_feature_on


def get_table_data(db_path, table):
    """
    :param db_path: 
    :param table: 
    :return: 
    """
    io, c = connect_to_database(db_path=db_path)

    table_data_query = c.execute("""SELECT * FROM {};""".format(table))

    column_names = [s[0] for s in table_data_query.description]

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    return column_names, rows_data


def create_data_table_api(db_path, ngifkey, caption, table):
    """
    :param db_path:
    :param ngifkey:
    :param caption:
    :param table:
    :return:
    """
    data_table_api = dict()
    data_table_api['ngIfKey'] = ngifkey
    data_table_api['caption'] = caption
    column_names, data_rows = get_table_data(db_path=db_path, table=table)
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


# ### Socket Communication ### #
@socketio.on('add_new_scenario')
def add_new_scenario(msg):
    io, c = connect_to_database(db_path=DATABASE_PATH)

    # Check if this is a new scenario or if we're updating an existing scenario
    # TODO: implement UI warnings if updating
    scenario_exists = c.execute(
            "SELECT scenario_name"
            " FROM scenarios "
            "WHERE scenario_name = '{}';".format(msg['scenarioName'])
    ).fetchone()

    if scenario_exists is not None:
        print('Updating scenario {}'.format(msg['scenarioName']))
        # TODO: this won't work if updating the scenario name; need a
        #  different process & warnings for it
        update_dict = {
            # 'scenario_name': msg['scenarioName'],
            'of_fuels': 1 if msg['featureFuels'] == 'yes' else 0,
            'of_multi_stage': 'NULL',
            'of_transmission': 1 if msg[
                                     'featureTransmission'] == 'yes' else 0,
            'of_transmission_hurdle_rates':
                1 if msg['featureTransmissionHurdleRates'] == 'yes' else 0,
            'of_simultaneous_flow_limits':
                1 if ['featureSimFlowLimits'] == 'yes' else 0,
            'of_lf_reserves_up': 1 if msg['featureLFUp'] == 'yes' else 0,
            'of_lf_reserves_down': 1 if msg['featureLFDown'] == 'yes' else 0,
            'of_regulation_up': 1 if msg['featureRegUp'] == 'yes' else 0,
            'of_regulation_down': 1 if msg['featureRegDown'] == 'yes' else 0,
            'of_frequency_response': 1 if msg[
                                           'featureFreqResp'] == 'yes' else 0,
            'of_spinning_reserves': 1 if msg['featureSpin'] == 'yes' else 0,
            'of_rps': 1 if msg['featureRPS'] == 'yes' else 0,
            'of_carbon_cap': 1 if msg['featureCarbonCap'] == 'yes' else 0,
            'of_track_carbon_imports':
                1 if msg['featureTrackCarbonImports'] == 'yes' else 0,
            'of_prm': 1 if msg['featurePRM'] == 'yes' else 0,
            'of_local_capacity':
                1 if msg['featureELCCSurface'] == 'yes' else 0,
            'of_elcc_surface':
                1 if msg['featureLocalCapacity'] == 'yes' else 0,
            'temporal_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='temporal_scenario_id',
             table='subscenarios_temporal',
             setting_name=msg['temporalSetting']
            ),
            'load_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='load_zone_scenario_id',
             table='subscenarios_geography_load_zones',
             setting_name=msg['geographyLoadZonesSetting']
            ),
            'lf_reserves_up_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='lf_reserves_up_ba_scenario_id',
             table='subscenarios_geography_lf_reserves_up_bas',
             setting_name=msg['geographyLoadFollowingUpBAsSetting']
            ),
            'lf_reserves_down_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='lf_reserves_down_ba_scenario_id',
             table='subscenarios_geography_lf_reserves_down_bas',
             setting_name=msg['geographyLoadFollowingDownBAsSetting']
            ),
            'regulation_up_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='regulation_up_ba_scenario_id',
             table='subscenarios_geography_regulation_up_bas',
             setting_name=msg['geographyRegulationUpBAsSetting']
            ),
            'regulation_down_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='regulation_down_ba_scenario_id',
             table='subscenarios_geography_regulation_down_bas',
             setting_name=msg['geographyRegulationDownBAsSetting']
            ),
            'frequency_response_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='frequency_response_ba_scenario_id',
             table='subscenarios_geography_frequency_response_bas',
             setting_name=msg['geographyFrequencyResponseBAsSetting']
            ),
            'spinning_reserves_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='spinning_reserves_ba_scenario_id',
             table='subscenarios_geography_spinning_reserves_bas',
             setting_name=msg['geographySpinningReservesBAsSetting']
            ),
            'rps_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='rps_zone_scenario_id',
             table='subscenarios_geography_rps_zones',
             setting_name=msg['geographyRPSAreasSetting']
            ),
            'carbon_cap_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='carbon_cap_zone_scenario_id',
             table='subscenarios_geography_carbon_cap_zones',
             setting_name=msg['geographyCarbonCapAreasSetting']
            ),
            'prm_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='prm_zone_scenario_id',
             table='subscenarios_geography_prm_zones',
             setting_name=msg['geographyPRMAreasSetting']
            ),
            'local_capacity_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='local_capacity_zone_scenario_id',
             table='subscenarios_geography_local_capacity_zones',
             setting_name=msg['geographyLocalCapacityAreasSetting']
            ),
            'project_portfolio_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_portfolio_scenario_id',
             table='subscenarios_project_portfolios',
             setting_name=msg['projectPortfolioSetting']
            ),
            'project_operational_chars_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_operational_chars_scenario_id',
             table='subscenarios_project_operational_chars',
             setting_name=msg['projectOperationalCharsSetting']
            ),
            'project_availability_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_availability_scenario_id',
             table='subscenarios_project_availability',
             setting_name=msg['projectAvailabilitySetting']
            ),
            'fuel_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='fuel_scenario_id',
             table='subscenarios_project_fuels',
             setting_name=msg['projectFuelsSetting']
            ),
            'project_load_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_load_zone_scenario_id',
             table='subscenarios_project_load_zones',
             setting_name=msg['geographyProjectLoadZonesSetting']
            ),
            'project_lf_reserves_up_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_lf_reserves_up_ba_scenario_id',
             table='subscenarios_project_lf_reserves_up_bas',
             setting_name=msg['projectLoadFollowingUpBAsSetting']
            ),
            'project_lf_reserves_down_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_lf_reserves_down_ba_scenario_id',
             table='subscenarios_project_lf_reserves_down_bas',
             setting_name=msg['projectLoadFollowingDownBAsSetting']
            ),
            'project_regulation_up_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_regulation_up_ba_scenario_id',
             table='subscenarios_project_regulation_up_bas',
             setting_name=msg['projectRegulationUpBAsSetting']
            ),
            'project_regulation_down_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_regulation_down_ba_scenario_id',
             table='subscenarios_project_regulation_down_bas',
             setting_name=msg['projectRegulationDownBAsSetting']
            ),
            'project_frequency_response_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_frequency_response_ba_scenario_id',
             table='subscenarios_project_frequency_response_bas',
             setting_name=msg['projectFrequencyResponseBAsSetting']
            ),
            'project_spinning_reserves_ba_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_spinning_reserves_ba_scenario_id',
             table='subscenarios_project_spinning_reserves_bas',
             setting_name=msg['projectSpinningReservesBAsSetting']
            ),
            'project_rps_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_rps_zone_scenario_id',
             table='subscenarios_project_rps_zones',
             setting_name=msg['projectRPSAreasSetting']
            ),
            'project_carbon_cap_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_carbon_cap_zone_scenario_id',
             table='subscenarios_project_carbon_cap_zones',
             setting_name=msg['projectCarbonCapAreasSetting']
            ),
            'project_prm_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_prm_zone_scenario_id',
             table='subscenarios_project_prm_zones',
             setting_name=msg['projectPRMAreasSetting']
            ),
            'project_elcc_chars_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_elcc_chars_scenario_id',
             table='subscenarios_project_elcc_chars',
             setting_name=msg['projectELCCCharsSetting']
            ),
            'prm_energy_only_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='prm_energy_only_scenario_id',
             table='subscenarios_project_prm_energy_only',
             setting_name=msg['projectPRMEnergyOnlySetting']
            ),
            'project_local_capacity_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_local_capacity_zone_scenario_id',
             table='subscenarios_project_local_capacity_zones',
             setting_name=msg['projectLocalCapacityAreasSetting']
            ),
            'project_local_capacity_chars_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_local_capacity_chars_scenario_id',
             table='subscenarios_project_local_capacity_chars',
             setting_name=msg['projectLocalCapacityCharsSetting']
            ),
            'project_existing_capacity_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_existing_capacity_scenario_id',
             table='subscenarios_project_existing_capacity',
             setting_name=msg['projectExistingCapacitySetting']
            ),
            'project_existing_fixed_cost_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_existing_fixed_cost_scenario_id',
             table='subscenarios_project_existing_fixed_cost',
             setting_name=msg['projectExistingFixedCostSetting']
            ),
            'fuel_price_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='fuel_price_scenario_id',
             table='subscenarios_project_fuel_prices',
             setting_name=msg['fuelPricesSetting']
            ),
            'project_new_cost_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_new_cost_scenario_id',
             table='subscenarios_project_new_cost',
             setting_name=msg['projectNewCostSetting']
            ),
            'project_new_potential_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='project_new_potential_scenario_id',
             table='subscenarios_project_new_potential',
             setting_name=msg['projectNewPotentialSetting']
            ),
            'transmission_portfolio_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='transmission_portfolio_scenario_id',
             table='subscenarios_transmission_portfolios',
             setting_name=msg['transmissionPortfolioSetting']
            ),
            'transmission_load_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='transmission_load_zone_scenario_id',
             table='subscenarios_transmission_load_zones',
             setting_name=msg['geographyTxLoadZonesSetting']
            ),
            'transmission_existing_capacity_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='transmission_existing_capacity_scenario_id',
             table='subscenarios_transmission_existing_capacity',
             setting_name=msg['transmissionExistingCapacitySetting']
            ),
            'transmission_operational_chars_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='transmission_operational_chars_scenario_id',
             table='subscenarios_transmission_operational_chars',
             setting_name=msg['transmissionOperationalCharsSetting']
            ),
            'transmission_hurdle_rate_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='transmission_hurdle_rate_scenario_id',
             table='subscenarios_transmission_hurdle_rates',
             setting_name=msg['transmissionHurdleRatesSetting']
            ),
            'transmission_carbon_cap_zone_scenario_id': get_setting_option_id(
             db_path=DATABASE_PATH,
             id_column='transmission_carbon_cap_zone_scenario_id',
             table='subscenarios_transmission_carbon_cap_zones',
             setting_name=msg['transmissionCarbonCapAreasSetting']
            ),
            'transmission_simultaneous_flow_limit_scenario_id':
                get_setting_option_id(
                    db_path=DATABASE_PATH,
                    id_column=
                    'transmission_simultaneous_flow_limit_scenario_id',
                    table='subscenarios_transmission_simultaneous_flow_limits',
                    setting_name=msg[
                      'transmissionSimultaneousFlowLimitsSetting']
                ),
            'transmission_simultaneous_flow_limit_line_group_scenario_id':
                get_setting_option_id(
                    db_path=DATABASE_PATH,
                    id_column='transmission_simultaneous_flow_limit_line_group_scenario_id',
                    table='subscenarios_transmission_simultaneous_flow_limit_line_groups',
                    setting_name=msg['transmissionSimultaneousFlowLimitLineGroupsSetting']
             ),
            'load_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='load_scenario_id',
                 table='subscenarios_system_load',
                 setting_name=msg['systemLoadSetting']
            ),
            'lf_reserves_up_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='lf_reserves_up_scenario_id',
                 table='subscenarios_system_lf_reserves_up',
                 setting_name=msg['loadFollowingUpRequirementSetting']
            ),
            'lf_reserves_down_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='lf_reserves_down_scenario_id',
                 table='subscenarios_system_lf_reserves_down',
                 setting_name=msg['loadFollowingDownRequirementSetting']
            ),
            'regulation_up_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='regulation_up_scenario_id',
                 table='subscenarios_system_regulation_up',
                 setting_name=msg['regulationUpRequirementSetting']
            ),
            'regulation_down_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='regulation_down_scenario_id',
                 table='subscenarios_system_regulation_down',
                 setting_name=msg['regulationDownRequirementSetting']
            ),
            'frequency_response_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='frequency_response_scenario_id',
                 table='subscenarios_system_frequency_response',
                 setting_name=msg['frequencyResponseRequirementSetting']
            ),
            'spinning_reserves_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='spinning_reserves_scenario_id',
                 table='subscenarios_system_spinning_reserves',
                 setting_name=msg['spinningReservesRequirementSetting']
            ),
            'rps_target_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='rps_target_scenario_id',
                 table='subscenarios_system_rps_targets',
                 setting_name=msg['rpsTargetSetting']
            ),
            'carbon_cap_target_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='carbon_cap_target_scenario_id',
                 table='subscenarios_system_carbon_cap_targets',
                 setting_name=msg['carbonCapTargetSetting']
            ),
            'prm_requirement_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='prm_requirement_scenario_id',
                 table='subscenarios_system_prm_requirement',
                 setting_name=msg['prmRequirementSetting']
            ),
            'elcc_surface_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='elcc_surface_scenario_id',
                 table='subscenarios_system_elcc_surface',
                 setting_name=msg['elccSurfaceSetting']
            ),
            'local_capacity_requirement_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='local_capacity_requirement_scenario_id',
                 table='subscenarios_system_local_capacity_requirement',
                 setting_name=msg['localCapacityRequirementSetting']
            ),
            'tuning_scenario_id': get_setting_option_id(
                 db_path=DATABASE_PATH,
                 id_column='tuning_scenario_id',
                 table='subscenarios_tuning',
                 setting_name=msg['tuningSetting']
            )
        }
        update_scenario_multiple_columns(
            io=io, c=c,
            scenario_name=msg['scenarioName'],
            column_values_dict=update_dict
        )
    else:
        print('Inserting new scenario {}'.format(msg['scenarioName']))
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
                db_path=DATABASE_PATH,
                id_column='temporal_scenario_id',
                table='subscenarios_temporal',
                setting_name=msg['temporalSetting']
            ),
            load_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='load_zone_scenario_id',
                table='subscenarios_geography_load_zones',
                setting_name=msg['geographyLoadZonesSetting']
            ),
            lf_reserves_up_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='lf_reserves_up_ba_scenario_id',
                table='subscenarios_geography_lf_reserves_up_bas',
                setting_name=msg['geographyLoadFollowingUpBAsSetting']
            ),
            lf_reserves_down_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='lf_reserves_down_ba_scenario_id',
                table='subscenarios_geography_lf_reserves_down_bas',
                setting_name=msg['geographyLoadFollowingDownBAsSetting']
            ),
            regulation_up_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='regulation_up_ba_scenario_id',
                table='subscenarios_geography_regulation_up_bas',
                setting_name=msg['geographyRegulationUpBAsSetting']
            ),
            regulation_down_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='regulation_down_ba_scenario_id',
                table='subscenarios_geography_regulation_down_bas',
                setting_name=msg['geographyRegulationDownBAsSetting']
            ),
            frequency_response_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='frequency_response_ba_scenario_id',
                table='subscenarios_geography_frequency_response_bas',
                setting_name=msg['geographyFrequencyResponseBAsSetting']
            ),
            spinning_reserves_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='spinning_reserves_ba_scenario_id',
                table='subscenarios_geography_spinning_reserves_bas',
                setting_name=msg['geographySpinningReservesBAsSetting']
            ),
            rps_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='rps_zone_scenario_id',
                table='subscenarios_geography_rps_zones',
                setting_name=msg['geographyRPSAreasSetting']
            ),
            carbon_cap_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='carbon_cap_zone_scenario_id',
                table='subscenarios_geography_carbon_cap_zones',
                setting_name=msg['geographyCarbonCapAreasSetting']
            ),
            prm_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='prm_zone_scenario_id',
                table='subscenarios_geography_prm_zones',
                setting_name=msg['geographyPRMAreasSetting']
            ),
            local_capacity_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='local_capacity_zone_scenario_id',
                table='subscenarios_geography_local_capacity_zones',
                setting_name=msg['geographyLocalCapacityAreasSetting']
            ),
            project_portfolio_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_portfolio_scenario_id',
                table='subscenarios_project_portfolios',
                setting_name=msg['projectPortfolioSetting']
            ),
            project_operational_chars_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_operational_chars_scenario_id',
                table='subscenarios_project_operational_chars',
                setting_name=msg['projectOperationalCharsSetting']
            ),
            project_availability_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_availability_scenario_id',
                table='subscenarios_project_availability',
                setting_name=msg['projectAvailabilitySetting']
            ),
            fuel_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='fuel_scenario_id',
                table='subscenarios_project_fuels',
                setting_name=msg['projectFuelsSetting']
            ),
            project_load_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_load_zone_scenario_id',
                table='subscenarios_project_load_zones',
                setting_name=msg['geographyProjectLoadZonesSetting']
            ),
            project_lf_reserves_up_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_lf_reserves_up_ba_scenario_id',
                table='subscenarios_project_lf_reserves_up_bas',
                setting_name=msg['projectLoadFollowingUpBAsSetting']
            ),
            project_lf_reserves_down_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_lf_reserves_down_ba_scenario_id',
                table='subscenarios_project_lf_reserves_down_bas',
                setting_name=msg['projectLoadFollowingDownBAsSetting']
            ),
            project_regulation_up_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_regulation_up_ba_scenario_id',
                table='subscenarios_project_regulation_up_bas',
                setting_name=msg['projectRegulationUpBAsSetting']
            ),
            project_regulation_down_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_regulation_down_ba_scenario_id',
                table='subscenarios_project_regulation_down_bas',
                setting_name=msg['projectRegulationDownBAsSetting']
            ),
            project_frequency_response_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_frequency_response_ba_scenario_id',
                table='subscenarios_project_frequency_response_bas',
                setting_name=msg['projectFrequencyResponseBAsSetting']
            ),
            project_spinning_reserves_ba_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_spinning_reserves_ba_scenario_id',
                table='subscenarios_project_spinning_reserves_bas',
                setting_name=msg['projectSpinningReservesBAsSetting']
            ),
            project_rps_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_rps_zone_scenario_id',
                table='subscenarios_project_rps_zones',
                setting_name=msg['projectRPSAreasSetting']
            ),
            project_carbon_cap_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_carbon_cap_zone_scenario_id',
                table='subscenarios_project_carbon_cap_zones',
                setting_name=msg['projectCarbonCapAreasSetting']
            ),
            project_prm_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_prm_zone_scenario_id',
                table='subscenarios_project_prm_zones',
                setting_name=msg['projectPRMAreasSetting']
            ),
            project_elcc_chars_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_elcc_chars_scenario_id',
                table='subscenarios_project_elcc_chars',
                setting_name=msg['projectELCCCharsSetting']
            ),
            prm_energy_only_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='prm_energy_only_scenario_id',
                table='subscenarios_project_prm_energy_only',
                setting_name=msg['projectPRMEnergyOnlySetting']
            ),
            project_local_capacity_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_local_capacity_zone_scenario_id',
                table='subscenarios_project_local_capacity_zones',
                setting_name=msg['projectLocalCapacityAreasSetting']
            ),
            project_local_capacity_chars_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_local_capacity_chars_scenario_id',
                table='subscenarios_project_local_capacity_chars',
                setting_name=msg['projectLocalCapacityCharsSetting']
            ),
            project_existing_capacity_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_existing_capacity_scenario_id',
                table='subscenarios_project_existing_capacity',
                setting_name=msg['projectExistingCapacitySetting']
            ),
            project_existing_fixed_cost_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_existing_fixed_cost_scenario_id',
                table='subscenarios_project_existing_fixed_cost',
                setting_name=msg['projectExistingFixedCostSetting']
            ),
            fuel_price_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='fuel_price_scenario_id',
                table='subscenarios_project_fuel_prices',
                setting_name=msg['fuelPricesSetting']
            ),
            project_new_cost_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_new_cost_scenario_id',
                table='subscenarios_project_new_cost',
                setting_name=msg['projectNewCostSetting']
            ),
            project_new_potential_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='project_new_potential_scenario_id',
                table='subscenarios_project_new_potential',
                setting_name=msg['projectNewPotentialSetting']
            ),
            transmission_portfolio_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_portfolio_scenario_id',
                table='subscenarios_transmission_portfolios',
                setting_name=msg['transmissionPortfolioSetting']
            ),
            transmission_load_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_load_zone_scenario_id',
                table='subscenarios_transmission_load_zones',
                setting_name=msg['geographyTxLoadZonesSetting']
            ),
            transmission_existing_capacity_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_existing_capacity_scenario_id',
                table='subscenarios_transmission_existing_capacity',
                setting_name=msg['transmissionExistingCapacitySetting']
            ),
            transmission_operational_chars_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_operational_chars_scenario_id',
                table='subscenarios_transmission_operational_chars',
                setting_name=msg['transmissionOperationalCharsSetting']
            ),
            transmission_hurdle_rate_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_hurdle_rate_scenario_id',
                table='subscenarios_transmission_hurdle_rates',
                setting_name=msg['transmissionHurdleRatesSetting']
            ),
            transmission_carbon_cap_zone_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_carbon_cap_zone_scenario_id',
                table='subscenarios_transmission_carbon_cap_zones',
                setting_name=msg['transmissionCarbonCapAreasSetting']
            ),
            transmission_simultaneous_flow_limit_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='transmission_simultaneous_flow_limit_scenario_id',
                table='subscenarios_transmission_simultaneous_flow_limits',
                setting_name=msg['transmissionSimultaneousFlowLimitsSetting']
            ),
            transmission_simultaneous_flow_limit_line_group_scenario_id=
            get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column=
                'transmission_simultaneous_flow_limit_line_group_scenario_id',
                table=
                'subscenarios_transmission_simultaneous_flow_limit_line_groups',
                setting_name=msg[
                    'transmissionSimultaneousFlowLimitLineGroupsSetting'
                ]
            ),
            load_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='load_scenario_id',
                table='subscenarios_system_load',
                setting_name=msg['systemLoadSetting']
            ),
            lf_reserves_up_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='lf_reserves_up_scenario_id',
                table='subscenarios_system_lf_reserves_up',
                setting_name=msg['loadFollowingUpRequirementSetting']
            ),
            lf_reserves_down_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='lf_reserves_down_scenario_id',
                table='subscenarios_system_lf_reserves_down',
                setting_name=msg['loadFollowingDownRequirementSetting']
            ),
            regulation_up_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='regulation_up_scenario_id',
                table='subscenarios_system_regulation_up',
                setting_name=msg['regulationUpRequirementSetting']
            ),
            regulation_down_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='regulation_down_scenario_id',
                table='subscenarios_system_regulation_down',
                setting_name=msg['regulationDownRequirementSetting']
            ),
            frequency_response_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='frequency_response_scenario_id',
                table='subscenarios_system_frequency_response',
                setting_name=msg['frequencyResponseRequirementSetting']
            ),
            spinning_reserves_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='spinning_reserves_scenario_id',
                table='subscenarios_system_spinning_reserves',
                setting_name=msg['spinningReservesRequirementSetting']
            ),
            rps_target_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='rps_target_scenario_id',
                table='subscenarios_system_rps_targets',
                setting_name=msg['rpsTargetSetting']
            ),
            carbon_cap_target_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='carbon_cap_target_scenario_id',
                table='subscenarios_system_carbon_cap_targets',
                setting_name=msg['carbonCapTargetSetting']
            ),
            prm_requirement_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='prm_requirement_scenario_id',
                table='subscenarios_system_prm_requirement',
                setting_name=msg['prmRequirementSetting']
            ),
            elcc_surface_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='elcc_surface_scenario_id',
                table='subscenarios_system_elcc_surface',
                setting_name=msg['elccSurfaceSetting']
            ),
            local_capacity_requirement_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='local_capacity_requirement_scenario_id',
                table='subscenarios_system_local_capacity_requirement',
                setting_name=msg['localCapacityRequirementSetting']
            ),
            tuning_scenario_id=get_setting_option_id(
                db_path=DATABASE_PATH,
                id_column='tuning_scenario_id',
                table='subscenarios_tuning',
                setting_name=msg['tuningSetting']
            )
        )

    scenario_id = c.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_name = '{}'".format
        (msg['scenarioName']
         )
    ).fetchone()[0]

    emit('return_new_scenario_id', scenario_id)


# ### RUNNING SCENARIOS ### #
# TODO: incomplete functionality

@socketio.on('launch_scenario_process')
def launch_scenario_process(client_message):
    """
    Launch a process to run the scenario.
    :param client_message:
    :return:
    """
    scenario_id = str(client_message['scenario'])

    # Get the scenario name for this scenario ID
    # TODO: pass both from the client and do a check here that they exist
    io, c = connect_to_database()
    scenario_name = c.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    # First, check if the scenario is already running
    process_status = check_scenario_process_status(
        client_message=client_message)
    if process_status:
        # TODO: what should happen if the scenario is already running? At a
        #  minimum, it should be a warning and perhaps a way to stop the
        #  process and re-start the scenario run.
        print("Scenario already running.")
        emit(
            'scenario_already_running',
            'scenario already running'
        )
    # If the scenario is not found among the running processes, launch a
    # multiprocessing process
    else:
        print("Starting process for scenario_id " + scenario_id)
        # p = multiprocessing.Process(
        #     target=run_scenario,
        #     name=scenario_id,
        #     args=(scenario_name,),
        # )
        # p.start()
        os.chdir(GRIDPATH_DIRECTORY)
        p = subprocess.Popen(
            [sys.executable, '-u',
             os.path.join(GRIDPATH_DIRECTORY, 'run_start_to_end.py'),
             '--log', '--scenario', scenario_name])

        # Needed to ensure child processes are terminated when server exits
        atexit.register(p.terminate)

        # Save the scenario's process ID
        # TODO: we should save to Electron instead, as closing the UI will
        #  delete the global data for the server
        global SCENARIO_STATUS
        SCENARIO_STATUS[(scenario_id, scenario_name)] = dict()
        SCENARIO_STATUS[(scenario_id, scenario_name)]['process_id'] = p.pid


# TODO: implement functionality to check on the process from the UI (
#  @socketio is not linked to anything yet)
@socketio.on('check_scenario_process_status')
def check_scenario_process_status(db_path, client_message):
    """
    Check if there is any running process that contains the given scenario
    """
    scenario_id = str(client_message['scenario'])
    io, c = connect_to_database(db_path=db_path)
    scenario_name = c.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    global SCENARIO_STATUS

    if (scenario_id, scenario_name) in SCENARIO_STATUS.keys():
        pid = SCENARIO_STATUS[(scenario_id, scenario_name)]['process_id']
        # Process ID saved in global and process is still running
        if pid in [p.pid for p in psutil.process_iter()] \
                and psutil.Process(pid).status() == 'running':
            return True
        else:
            # Process ID saved in global but process is not running
            return False
    else:
        return False


# ### Common functions ### #
# TODO: use flask built-in DB tools?
def connect_to_database(db_path):
    """
    :param db_path: the path to the database we're connecting to
    :return: the database connection object and a cursor object for the
      connection

    Connect to a database and return the connection object and a
    connection cursor object.
    """
    io = sqlite3.connect(db_path)
    c = io.cursor()

    return io, c


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
