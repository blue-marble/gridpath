from flask_socketio import emit

from db.utilities.create_scenario import create_scenario
from db.utilities.update_scenario import update_scenario_multiple_columns
from ui.server.common_functions import connect_to_database


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
            'of_fuels': 1 if msg['features$fuels'] else 0,
            'of_multi_stage': 'NULL',
            'of_transmission': 1 if msg['features$transmission'] else 0,
            'of_transmission_hurdle_rates':
                1 if msg['features$transmission_hurdle_rates'] else 0,
            'of_simultaneous_flow_limits':
                1 if ['features$transmission_sim_flow'] else 0,
            'of_lf_reserves_up': 1 if msg['features$load_following_up'] else 0,
            'of_lf_reserves_down': 1 if msg['features$load_following_down']
            else 0,
            'of_regulation_up': 1 if msg['features$regulation_up'] else 0,
            'of_regulation_down': 1 if msg['features$regulation_down'] else 0,
            'of_frequency_response': 1 if msg['features$frequency_response']
            else 0,
            'of_spinning_reserves': 1 if msg['features$spinning_reserves']
            else 0,
            'of_rps': 1 if msg['features$rps'] else 0,
            'of_carbon_cap': 1 if msg['features$carbon_cap'] else 0,
            'of_track_carbon_imports':
                1 if msg['features$track_carbon_imports'] else 0,
            'of_prm': 1 if msg['features$prm'] else 0,
            'of_local_capacity': 1 if msg['features$elcc_surface'] else 0,
            'of_elcc_surface': 1 if msg['features$local_capacity'] else 0,
            'temporal_scenario_id': get_setting_option_id(
             db_path=db_path,
             msg=msg,
             key='temporal$temporal'
            ),
            'load_zone_scenario_id': get_setting_option_id(
             db_path=db_path,
             msg=msg,
             key='load_zones$load_zones'
            ),
            'lf_reserves_up_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$bas'
            ),
            'lf_reserves_down_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_down$bas'
            ),
            'regulation_up_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_up$bas'
            ),
            'regulation_down_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_down$bas'
            ),
            'frequency_response_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='frequency_response$bas'
            ),
            'spinning_reserves_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='spinning_reserves$bas'
            ),
            'rps_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='rps$bas'
            ),
            'carbon_cap_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$bas'
            ),
            'prm_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$bas'
            ),
            'local_capacity_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$bas'
            ),
            'project_portfolio_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$portfolio'
            ),
            'project_operational_chars_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_opchar$opchar'
            ),
            'project_availability_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$availability'
            ),
            'fuel_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='fuels$fuels'
            ),
            'project_load_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_zones$project_load_zones'
            ),
            'project_lf_reserves_up_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$projects'
            ),
            'project_lf_reserves_down_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$projects'
            ),
            'project_regulation_up_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_up$projects'
            ),
            'project_regulation_down_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_down$projects'
            ),
            'project_frequency_response_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='frequency_response$projects'
            ),
            'project_spinning_reserves_ba_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='spinning_reserves$projects'
            ),
            'project_rps_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='rps$projects'
            ),
            'project_carbon_cap_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$projects'
            ),
            'project_prm_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$projects'
            ),
            'project_elcc_chars_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$project_elcc'
            ),
            'prm_energy_only_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$energy_only'
            ),
            'project_local_capacity_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$projects'
            ),
            'project_local_capacity_chars_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$project_chars'
            ),
            'project_existing_capacity_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$specified_capacity'
            ),
            'project_existing_fixed_cost_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$specified_fixed_cost'
            ),
            'fuel_price_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='fuels$fuel_prices'
            ),
            'project_new_cost_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$new_cost'
            ),
            'project_new_potential_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$new_potential'
            ),
            'transmission_portfolio_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_capacity$portfolio'
            ),
            'transmission_load_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_zones$transmission_load_zones'
            ),
            'transmission_existing_capacity_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_capacity$specified_capacity'
            ),
            'transmission_operational_chars_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_opchar$opchar'
            ),
            'transmission_hurdle_rate_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_hurdle_rates$hurdle_rates'
            ),
            'transmission_carbon_cap_zone_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$transmission'
            ),
            'transmission_simultaneous_flow_limit_scenario_id':
                get_setting_option_id(
                  db_path=db_path,
                  msg=msg,
                  key='transmission_sim_flow_limits$limits'
                ),
            'transmission_simultaneous_flow_limit_line_group_scenario_id':
                get_setting_option_id(
                  db_path=db_path,
                  msg=msg,
                  key='transmission_sim_flow_limits$groups'
             ),
            'load_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='system_load$system_load'
            ),
            'lf_reserves_up_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$req'
            ),
            'lf_reserves_down_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_down$req'
            ),
            'regulation_up_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_up$req'
            ),
            'regulation_down_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_down$req'
            ),
            'frequency_response_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='frequency_response$req'
            ),
            'spinning_reserves_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='spinning_reserves$req'
            ),
            'rps_target_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='rps$req'
            ),
            'carbon_cap_target_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$req'
            ),
            'prm_requirement_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$req'
            ),
            'elcc_surface_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$elcc'
            ),
            'local_capacity_requirement_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$req'
            ),
            'tuning_scenario_id': get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='tuning$tuning'
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
            of_fuels=1 if msg['features$fuels'] else 0,
            of_multi_stage='NULL',
            of_transmission=1 if msg['features$transmission'] else 0,
            of_transmission_hurdle_rates=1 if msg[
                'features$transmission_hurdle_rates'] else 0,
            of_simultaneous_flow_limits=1 if ['features$transmission_sim_flow']
            else 0,
            of_lf_reserves_up=1 if msg['features$load_following_up'] else 0,
            of_lf_reserves_down=1 if msg['features$load_following_down'] else 0,
            of_regulation_up=1 if msg['features$regulation_up'] else 0,
            of_regulation_down=1 if msg['features$regulation_down'] else 0,
            of_frequency_response=1 if msg['features$frequency_response']
            else 0,
            of_spinning_reserves=1 if msg['features$spinning_reserves'] else 0,
            of_rps=1 if msg['features$rps'] else 0,
            of_carbon_cap=1 if msg['features$carbon_cap'] else 0,
            of_track_carbon_imports=1 if msg['features$track_carbon_imports']
            else 0,
            of_prm=1 if msg['features$prm'] else 0,
            of_local_capacity=1 if msg['features$elcc_surface'] else 0,
            of_elcc_surface=1 if msg['features$local_capacity'] else 0,
            temporal_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='temporal$temporal'
            ),
            load_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_zones$load_zones'
            ),
            lf_reserves_up_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$bas'
            ),
            lf_reserves_down_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_down$bas'
            ),
            regulation_up_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_up$bas'
            ),
            regulation_down_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_down$bas'
            ),
            frequency_response_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='frequency_response$bas'
            ),
            spinning_reserves_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='spinning_reserves$bas'
            ),
            rps_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='rps$bas'
            ),
            carbon_cap_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$bas'
            ),
            prm_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$bas'
            ),
            local_capacity_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$bas'
            ),
            project_portfolio_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$portfolio'
            ),
            project_operational_chars_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_opchar$opchar'
            ),
            project_availability_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$availability'
            ),
            fuel_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='fuels$fuels'
            ),
            project_load_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_zones$project_load_zones'
            ),
            project_lf_reserves_up_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$projects'
            ),
            project_lf_reserves_down_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$projects'
            ),
            project_regulation_up_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_up$projects'
            ),
            project_regulation_down_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_down$projects'
            ),
            project_frequency_response_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='frequency_response$projects'
            ),
            project_spinning_reserves_ba_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='spinning_reserves$projects'
            ),
            project_rps_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='rps$projects'
            ),
            project_carbon_cap_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$projects'
            ),
            project_prm_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$projects'
            ),
            project_elcc_chars_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$project_elcc'
            ),
            prm_energy_only_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$energy_only'
            ),
            project_local_capacity_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$projects'
            ),
            project_local_capacity_chars_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$project_chars'
            ),
            project_existing_capacity_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$specified_capacity'
            ),
            project_existing_fixed_cost_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$specified_fixed_cost'
            ),
            fuel_price_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='fuels$fuel_prices'
            ),
            project_new_cost_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$new_cost'
            ),
            project_new_potential_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='project_capacity$new_potential'
            ),
            transmission_portfolio_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_capacity$portfolio'
            ),
            transmission_load_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_zones$transmission_load_zones'
            ),
            transmission_existing_capacity_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_capacity$specified_capacity'
            ),
            transmission_operational_chars_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_opchar$opchar'
            ),
            transmission_hurdle_rate_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_hurdle_rates$hurdle_rates'
            ),
            transmission_carbon_cap_zone_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$transmission'
            ),
            transmission_simultaneous_flow_limit_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_sim_flow_limits$limits'
            ),
            transmission_simultaneous_flow_limit_line_group_scenario_id=
            get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='transmission_sim_flow_limits$groups'
            ),
            load_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='system_load$system_load'
            ),
            lf_reserves_up_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_up$req'
            ),
            lf_reserves_down_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='load_following_down$req'
            ),
            regulation_up_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_up$req'
            ),
            regulation_down_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='regulation_down$req'
            ),
            frequency_response_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='frequency_response$req'
            ),
            spinning_reserves_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='spinning_reserves$req'
            ),
            rps_target_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='rps$req'
            ),
            carbon_cap_target_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='carbon_cap$req'
            ),
            prm_requirement_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$req'
            ),
            elcc_surface_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='prm$elcc'
            ),
            local_capacity_requirement_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='local_capacity$req'
            ),
            tuning_scenario_id=get_setting_option_id(
              db_path=db_path,
              msg=msg,
              key='tuning$tuning'
            )
        )

    scenario_id = c.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_name = '{}'".format
        (msg['scenarioName']
         )
    ).fetchone()[0]

    emit('return_new_scenario_id', scenario_id)


def get_setting_option_id(db_path, msg, key):
    """
    :param db_path: the path to the database file
    :param msg: the form data sent by Angular, dictionary
    :param key: the key for the values we want to get from the form data
    :return:
    """

    io, c = connect_to_database(db_path=db_path)
    table, id_column = get_meta_data(c=c, form_key=key)

    setting_id = c.execute(
        """SELECT {} FROM {} WHERE name = '{}'""".format(
            id_column, table, msg[key]
        )
    ).fetchone()[0]

    return setting_id


def get_meta_data(c, form_key):
    """

    :param c:
    :param form_key:
    :return:
    """
    sep = form_key.index("$")
    ui_table = form_key[:sep]
    ui_table_row = form_key[sep+1:]

    (subscenario_table, subscenario_id_column) = c.execute(
      """SELECT ui_row_db_subscenario_table, 
      ui_row_db_subscenario_table_id_column
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}'
      AND ui_table_row = '{}';""".format(ui_table, ui_table_row)
    ).fetchone()

    return subscenario_table, subscenario_id_column
