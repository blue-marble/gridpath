# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

# ### API: New Scenario Settings ### #

# TODO: need to require setting 'name' column to be unique
# TODO: figure out how to deal with tables with two (or more) subscenario IDs
from ui.api.common_functions import connect_to_database


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
