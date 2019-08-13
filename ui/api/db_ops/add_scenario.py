from flask_socketio import emit

from db.utilities.create_scenario import create_scenario
from db.utilities.update_scenario import update_scenario_multiple_columns
from ui.api.common_functions import connect_to_database


def add_or_update_scenario(db_path, msg):
    print(msg)
    io, c = connect_to_database(db_path=db_path)

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
             db_path=db_path,
             id_column='temporal_scenario_id',
             table='subscenarios_temporal',
             setting_name=msg['temporal_scenario_id']
            ),
            'load_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='load_zone_scenario_id',
             table='subscenarios_geography_load_zones',
             setting_name=msg['load_zone_scenario_id']
            ),
            'lf_reserves_up_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='lf_reserves_up_ba_scenario_id',
             table='subscenarios_geography_lf_reserves_up_bas',
             setting_name=msg['lf_reserves_up_ba_scenario_id']
            ),
            'lf_reserves_down_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='lf_reserves_down_ba_scenario_id',
             table='subscenarios_geography_lf_reserves_down_bas',
             setting_name=msg['lf_reserves_down_ba_scenario_id']
            ),
            'regulation_up_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='regulation_up_ba_scenario_id',
             table='subscenarios_geography_regulation_up_bas',
             setting_name=msg['regulation_up_ba_scenario_id']
            ),
            'regulation_down_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='regulation_down_ba_scenario_id',
             table='subscenarios_geography_regulation_down_bas',
             setting_name=msg['regulation_down_ba_scenario_id']
            ),
            'frequency_response_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='frequency_response_ba_scenario_id',
             table='subscenarios_geography_frequency_response_bas',
             setting_name=msg['frequency_response_ba_scenario_id']
            ),
            'spinning_reserves_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='spinning_reserves_ba_scenario_id',
             table='subscenarios_geography_spinning_reserves_bas',
             setting_name=msg['spinning_reserves_ba_scenario_id']
            ),
            'rps_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='rps_zone_scenario_id',
             table='subscenarios_geography_rps_zones',
             setting_name=msg['rps_zone_scenario_id']
            ),
            'carbon_cap_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='carbon_cap_zone_scenario_id',
             table='subscenarios_geography_carbon_cap_zones',
             setting_name=msg['carbon_cap_zone_scenario_id']
            ),
            'prm_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='prm_zone_scenario_id',
             table='subscenarios_geography_prm_zones',
             setting_name=msg['prm_zone_scenario_id']
            ),
            'local_capacity_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='local_capacity_zone_scenario_id',
             table='subscenarios_geography_local_capacity_zones',
             setting_name=msg['local_capacity_zone_scenario_id']
            ),
            'project_portfolio_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_portfolio_scenario_id',
             table='subscenarios_project_portfolios',
             setting_name=msg['project_portfolio_scenario_id']
            ),
            'project_operational_chars_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_operational_chars_scenario_id',
             table='subscenarios_project_operational_chars',
             setting_name=msg['project_operational_chars_scenario_id']
            ),
            'project_availability_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_availability_scenario_id',
             table='subscenarios_project_availability',
             setting_name=msg['project_availability_scenario_id']
            ),
            'fuel_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='fuel_scenario_id',
             table='subscenarios_project_fuels',
             setting_name=msg['fuel_scenario_id']
            ),
            'project_load_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_load_zone_scenario_id',
             table='subscenarios_project_load_zones',
             setting_name=msg['project_load_zone_scenario_id']
            ),
            'project_lf_reserves_up_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_lf_reserves_up_ba_scenario_id',
             table='subscenarios_project_lf_reserves_up_bas',
             setting_name=msg['project_lf_reserves_up_ba_scenario_id']
            ),
            'project_lf_reserves_down_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_lf_reserves_down_ba_scenario_id',
             table='subscenarios_project_lf_reserves_down_bas',
             setting_name=msg['project_lf_reserves_down_ba_scenario_id']
            ),
            'project_regulation_up_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_regulation_up_ba_scenario_id',
             table='subscenarios_project_regulation_up_bas',
             setting_name=msg['project_regulation_up_ba_scenario_id']
            ),
            'project_regulation_down_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_regulation_down_ba_scenario_id',
             table='subscenarios_project_regulation_down_bas',
             setting_name=msg['project_regulation_down_ba_scenario_id']
            ),
            'project_frequency_response_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_frequency_response_ba_scenario_id',
             table='subscenarios_project_frequency_response_bas',
             setting_name=msg['project_frequency_response_ba_scenario_id']
            ),
            'project_spinning_reserves_ba_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_spinning_reserves_ba_scenario_id',
             table='subscenarios_project_spinning_reserves_bas',
             setting_name=msg['project_spinning_reserves_ba_scenario_id']
            ),
            'project_rps_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_rps_zone_scenario_id',
             table='subscenarios_project_rps_zones',
             setting_name=msg['project_rps_zone_scenario_id']
            ),
            'project_carbon_cap_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_carbon_cap_zone_scenario_id',
             table='subscenarios_project_carbon_cap_zones',
             setting_name=msg['project_carbon_cap_zone_scenario_id']
            ),
            'project_prm_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_prm_zone_scenario_id',
             table='subscenarios_project_prm_zones',
             setting_name=msg['project_prm_zone_scenario_id']
            ),
            'project_elcc_chars_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_elcc_chars_scenario_id',
             table='subscenarios_project_elcc_chars',
             setting_name=msg['project_elcc_chars_scenario_id']
            ),
            'prm_energy_only_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='prm_energy_only_scenario_id',
             table='subscenarios_project_prm_energy_only',
             setting_name=msg['prm_energy_only_scenario_id']
            ),
            'project_local_capacity_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_local_capacity_zone_scenario_id',
             table='subscenarios_project_local_capacity_zones',
             setting_name=msg['project_local_capacity_zone_scenario_id']
            ),
            'project_local_capacity_chars_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_local_capacity_chars_scenario_id',
             table='subscenarios_project_local_capacity_chars',
             setting_name=msg['project_local_capacity_chars_scenario_id']
            ),
            'project_existing_capacity_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_existing_capacity_scenario_id',
             table='subscenarios_project_existing_capacity',
             setting_name=msg['project_existing_capacity_scenario_id']
            ),
            'project_existing_fixed_cost_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_existing_fixed_cost_scenario_id',
             table='subscenarios_project_existing_fixed_cost',
             setting_name=msg['project_existing_fixed_cost_scenario_id']
            ),
            'fuel_price_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='fuel_price_scenario_id',
             table='subscenarios_project_fuel_prices',
             setting_name=msg['fuel_price_scenario_id']
            ),
            'project_new_cost_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_new_cost_scenario_id',
             table='subscenarios_project_new_cost',
             setting_name=msg['project_new_cost_scenario_id']
            ),
            'project_new_potential_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='project_new_potential_scenario_id',
             table='subscenarios_project_new_potential',
             setting_name=msg['project_new_potential_scenario_id']
            ),
            'transmission_portfolio_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='transmission_portfolio_scenario_id',
             table='subscenarios_transmission_portfolios',
             setting_name=msg['transmission_portfolio_scenario_id']
            ),
            'transmission_load_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='transmission_load_zone_scenario_id',
             table='subscenarios_transmission_load_zones',
             setting_name=msg['transmission_load_zone_scenario_id']
            ),
            'transmission_existing_capacity_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='transmission_existing_capacity_scenario_id',
             table='subscenarios_transmission_existing_capacity',
             setting_name=msg['transmission_existing_capacity_scenario_id']
            ),
            'transmission_operational_chars_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='transmission_operational_chars_scenario_id',
             table='subscenarios_transmission_operational_chars',
             setting_name=msg['transmission_operational_chars_scenario_id']
            ),
            'transmission_hurdle_rate_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='transmission_hurdle_rate_scenario_id',
             table='subscenarios_transmission_hurdle_rates',
             setting_name=msg['transmission_hurdle_rate_scenario_id']
            ),
            'transmission_carbon_cap_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             id_column='transmission_carbon_cap_zone_scenario_id',
             table='subscenarios_transmission_carbon_cap_zones',
             setting_name=msg['transmission_carbon_cap_zone_scenario_id']
            ),
            'transmission_simultaneous_flow_limit_scenario_id':
                get_setting_option_id(
                    db_path=db_path,
                    id_column=
                    'transmission_simultaneous_flow_limit_scenario_id',
                    table='subscenarios_transmission_simultaneous_flow_limits',
                    setting_name=msg[
                      'transmission_simultaneous_flow_limit_scenario_id']
                ),
            'transmission_simultaneous_flow_limit_line_group_scenario_id':
                get_setting_option_id(
                    db_path=db_path,
                    id_column='transmission_simultaneous_flow_limit_line_group_scenario_id',
                    table='subscenarios_transmission_simultaneous_flow_limit_line_groups',
                    setting_name=msg['transmission_simultaneous_flow_limit_line_group_scenario_id']
             ),
            'load_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='load_scenario_id',
                 table='subscenarios_system_load',
                 setting_name=msg['load_scenario_id']
            ),
            'lf_reserves_up_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='lf_reserves_up_scenario_id',
                 table='subscenarios_system_lf_reserves_up',
                 setting_name=msg['lf_reserves_up_scenario_id']
            ),
            'lf_reserves_down_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='lf_reserves_down_scenario_id',
                 table='subscenarios_system_lf_reserves_down',
                 setting_name=msg['lf_reserves_down_scenario_id']
            ),
            'regulation_up_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='regulation_up_scenario_id',
                 table='subscenarios_system_regulation_up',
                 setting_name=msg['regulationUpRequirementSetting']
            ),
            'regulation_down_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='regulation_down_scenario_id',
                 table='subscenarios_system_regulation_down',
                 setting_name=msg['regulation_up_scenario_id']
            ),
            'frequency_response_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='frequency_response_scenario_id',
                 table='subscenarios_system_frequency_response',
                 setting_name=msg['frequency_response_scenario_id']
            ),
            'spinning_reserves_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='spinning_reserves_scenario_id',
                 table='subscenarios_system_spinning_reserves',
                 setting_name=msg['spinning_reserves_scenario_id']
            ),
            'rps_target_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='rps_target_scenario_id',
                 table='subscenarios_system_rps_targets',
                 setting_name=msg['rps_target_scenario_id']
            ),
            'carbon_cap_target_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='carbon_cap_target_scenario_id',
                 table='subscenarios_system_carbon_cap_targets',
                 setting_name=msg['carbon_cap_target_scenario_id']
            ),
            'prm_requirement_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='prm_requirement_scenario_id',
                 table='subscenarios_system_prm_requirement',
                 setting_name=msg['prm_requirement_scenario_id']
            ),
            'elcc_surface_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='elcc_surface_scenario_id',
                 table='subscenarios_system_elcc_surface',
                 setting_name=msg['elcc_surface_scenario_id']
            ),
            'local_capacity_requirement_scenario_id': get_setting_option_id(
                 db_path=db_path,
                 id_column='local_capacity_requirement_scenario_id',
                 table='subscenarios_system_local_capacity_requirement',
                 setting_name=msg['local_capacity_requirement_scenario_id']
            ),
            # TODO: add tuning
            'tuning_scenario_id': 'no_tuning'
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
                db_path=db_path,
                id_column='temporal_scenario_id',
                table='subscenarios_temporal',
                setting_name=msg['temporal_scenario_id']
            ),
            load_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='load_zone_scenario_id',
                table='subscenarios_geography_load_zones',
                setting_name=msg['load_zone_scenario_id']
            ),
            lf_reserves_up_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='lf_reserves_up_ba_scenario_id',
                table='subscenarios_geography_lf_reserves_up_bas',
                setting_name=msg['lf_reserves_up_ba_scenario_id']
            ),
            lf_reserves_down_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='lf_reserves_down_ba_scenario_id',
                table='subscenarios_geography_lf_reserves_down_bas',
                setting_name=msg['lf_reserves_down_ba_scenario_id']
            ),
            regulation_up_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='regulation_up_ba_scenario_id',
                table='subscenarios_geography_regulation_up_bas',
                setting_name=msg['regulation_up_ba_scenario_id']
            ),
            regulation_down_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='regulation_down_ba_scenario_id',
                table='subscenarios_geography_regulation_down_bas',
                setting_name=msg['regulation_down_ba_scenario_id']
            ),
            frequency_response_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='frequency_response_ba_scenario_id',
                table='subscenarios_geography_frequency_response_bas',
                setting_name=msg['frequency_response_ba_scenario_id']
            ),
            spinning_reserves_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='spinning_reserves_ba_scenario_id',
                table='subscenarios_geography_spinning_reserves_bas',
                setting_name=msg['spinning_reserves_ba_scenario_id']
            ),
            rps_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='rps_zone_scenario_id',
                table='subscenarios_geography_rps_zones',
                setting_name=msg['rps_zone_scenario_id']
            ),
            carbon_cap_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='carbon_cap_zone_scenario_id',
                table='subscenarios_geography_carbon_cap_zones',
                setting_name=msg['carbon_cap_zone_scenario_id']
            ),
            prm_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='prm_zone_scenario_id',
                table='subscenarios_geography_prm_zones',
                setting_name=msg['prm_zone_scenario_id']
            ),
            local_capacity_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='local_capacity_zone_scenario_id',
                table='subscenarios_geography_local_capacity_zones',
                setting_name=msg['local_capacity_zone_scenario_id']
            ),
            project_portfolio_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_portfolio_scenario_id',
                table='subscenarios_project_portfolios',
                setting_name=msg['project_portfolio_scenario_id']
            ),
            project_operational_chars_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_operational_chars_scenario_id',
                table='subscenarios_project_operational_chars',
                setting_name=msg['project_operational_chars_scenario_id']
            ),
            project_availability_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_availability_scenario_id',
                table='subscenarios_project_availability',
                setting_name=msg['project_availability_scenario_id']
            ),
            fuel_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='fuel_scenario_id',
                table='subscenarios_project_fuels',
                setting_name=msg['fuel_scenario_id']
            ),
            project_load_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_load_zone_scenario_id',
                table='subscenarios_project_load_zones',
                setting_name=msg['project_load_zone_scenario_id']
            ),
            project_lf_reserves_up_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_lf_reserves_up_ba_scenario_id',
                table='subscenarios_project_lf_reserves_up_bas',
                setting_name=msg['project_lf_reserves_up_ba_scenario_id']
            ),
            project_lf_reserves_down_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_lf_reserves_down_ba_scenario_id',
                table='subscenarios_project_lf_reserves_down_bas',
                setting_name=msg['project_lf_reserves_down_ba_scenario_id']
            ),
            project_regulation_up_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_regulation_up_ba_scenario_id',
                table='subscenarios_project_regulation_up_bas',
                setting_name=msg['project_regulation_up_ba_scenario_id']
            ),
            project_regulation_down_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_regulation_down_ba_scenario_id',
                table='subscenarios_project_regulation_down_bas',
                setting_name=msg['project_regulation_down_ba_scenario_id']
            ),
            project_frequency_response_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_frequency_response_ba_scenario_id',
                table='subscenarios_project_frequency_response_bas',
                setting_name=msg['project_frequency_response_ba_scenario_id']
            ),
            project_spinning_reserves_ba_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_spinning_reserves_ba_scenario_id',
                table='subscenarios_project_spinning_reserves_bas',
                setting_name=msg['project_spinning_reserves_ba_scenario_id']
            ),
            project_rps_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_rps_zone_scenario_id',
                table='subscenarios_project_rps_zones',
                setting_name=msg['project_rps_zone_scenario_id']
            ),
            project_carbon_cap_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_carbon_cap_zone_scenario_id',
                table='subscenarios_project_carbon_cap_zones',
                setting_name=msg['project_carbon_cap_zone_scenario_id']
            ),
            project_prm_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_prm_zone_scenario_id',
                table='subscenarios_project_prm_zones',
                setting_name=msg['project_prm_zone_scenario_id']
            ),
            project_elcc_chars_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_elcc_chars_scenario_id',
                table='subscenarios_project_elcc_chars',
                setting_name=msg['project_elcc_chars_scenario_id']
            ),
            prm_energy_only_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='prm_energy_only_scenario_id',
                table='subscenarios_project_prm_energy_only',
                setting_name=msg['prm_energy_only_scenario_id']
            ),
            project_local_capacity_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_local_capacity_zone_scenario_id',
                table='subscenarios_project_local_capacity_zones',
                setting_name=msg['project_local_capacity_zone_scenario_id']
            ),
            project_local_capacity_chars_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_local_capacity_chars_scenario_id',
                table='subscenarios_project_local_capacity_chars',
                setting_name=msg['project_local_capacity_chars_scenario_id']
            ),
            project_existing_capacity_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_existing_capacity_scenario_id',
                table='subscenarios_project_existing_capacity',
                setting_name=msg['project_existing_capacity_scenario_id']
            ),
            project_existing_fixed_cost_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_existing_fixed_cost_scenario_id',
                table='subscenarios_project_existing_fixed_cost',
                setting_name=msg['project_existing_fixed_cost_scenario_id']
            ),
            fuel_price_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='fuel_price_scenario_id',
                table='subscenarios_project_fuel_prices',
                setting_name=msg['fuel_price_scenario_id']
            ),
            project_new_cost_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_new_cost_scenario_id',
                table='subscenarios_project_new_cost',
                setting_name=msg['project_new_cost_scenario_id']
            ),
            project_new_potential_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='project_new_potential_scenario_id',
                table='subscenarios_project_new_potential',
                setting_name=msg['project_new_potential_scenario_id']
            ),
            transmission_portfolio_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_portfolio_scenario_id',
                table='subscenarios_transmission_portfolios',
                setting_name=msg['transmission_portfolio_scenario_id']
            ),
            transmission_load_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_load_zone_scenario_id',
                table='subscenarios_transmission_load_zones',
                setting_name=msg['transmission_load_zone_scenario_id']
            ),
            transmission_existing_capacity_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_existing_capacity_scenario_id',
                table='subscenarios_transmission_existing_capacity',
                setting_name=msg['transmission_existing_capacity_scenario_id']
            ),
            transmission_operational_chars_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_operational_chars_scenario_id',
                table='subscenarios_transmission_operational_chars',
                setting_name=msg['transmission_operational_chars_scenario_id']
            ),
            transmission_hurdle_rate_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_hurdle_rate_scenario_id',
                table='subscenarios_transmission_hurdle_rates',
                setting_name=msg['transmission_hurdle_rate_scenario_id']
            ),
            transmission_carbon_cap_zone_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_carbon_cap_zone_scenario_id',
                table='subscenarios_transmission_carbon_cap_zones',
                setting_name=msg['transmission_carbon_cap_zone_scenario_id']
            ),
            transmission_simultaneous_flow_limit_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='transmission_simultaneous_flow_limit_scenario_id',
                table='subscenarios_transmission_simultaneous_flow_limits',
                setting_name=msg['transmission_simultaneous_flow_limit_scenario_id']
            ),
            transmission_simultaneous_flow_limit_line_group_scenario_id=
            get_setting_option_id(
                db_path=db_path,
                id_column=
                'transmission_simultaneous_flow_limit_line_group_scenario_id',
                table=
                'subscenarios_transmission_simultaneous_flow_limit_line_groups',
                setting_name=msg[
                    'transmission_simultaneous_flow_limit_line_group_scenario_id'
                ]
            ),
            load_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='load_scenario_id',
                table='subscenarios_system_load',
                setting_name=msg['load_scenario_id']
            ),
            lf_reserves_up_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='lf_reserves_up_scenario_id',
                table='subscenarios_system_lf_reserves_up',
                setting_name=msg['lf_reserves_up_scenario_id']
            ),
            lf_reserves_down_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='lf_reserves_down_scenario_id',
                table='subscenarios_system_lf_reserves_down',
                setting_name=msg['lf_reserves_down_scenario_id']
            ),
            regulation_up_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='regulation_up_scenario_id',
                table='subscenarios_system_regulation_up',
                setting_name=msg['regulation_up_scenario_id']
            ),
            regulation_down_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='regulation_down_scenario_id',
                table='subscenarios_system_regulation_down',
                setting_name=msg['regulation_down_scenario_id']
            ),
            frequency_response_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='frequency_response_scenario_id',
                table='subscenarios_system_frequency_response',
                setting_name=msg['frequency_response_scenario_id']
            ),
            spinning_reserves_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='spinning_reserves_scenario_id',
                table='subscenarios_system_spinning_reserves',
                setting_name=msg['spinning_reserves_scenario_id']
            ),
            rps_target_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='rps_target_scenario_id',
                table='subscenarios_system_rps_targets',
                setting_name=msg['rps_target_scenario_id']
            ),
            carbon_cap_target_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='carbon_cap_target_scenario_id',
                table='subscenarios_system_carbon_cap_targets',
                setting_name=msg['carbon_cap_target_scenario_id']
            ),
            prm_requirement_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='prm_requirement_scenario_id',
                table='subscenarios_system_prm_requirement',
                setting_name=msg['prm_requirement_scenario_id']
            ),
            elcc_surface_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='elcc_surface_scenario_id',
                table='subscenarios_system_elcc_surface',
                setting_name=msg['elcc_surface_scenario_id']
            ),
            local_capacity_requirement_scenario_id=get_setting_option_id(
                db_path=db_path,
                id_column='local_capacity_requirement_scenario_id',
                table='subscenarios_system_local_capacity_requirement',
                setting_name=msg['local_capacity_requirement_scenario_id']
            ),
            tuning_scenario_id=0
        )

    scenario_id = c.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_name = '{}'".format
        (msg['scenarioName']
         )
    ).fetchone()[0]

    emit('return_new_scenario_id', scenario_id)


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
