#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project zones data
"""

from db.utilities import project_zones

def load_project_load_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    project load zones dictionary has project and load_zone
    {project: load_zone}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        prj_sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['id'] ==
                                                 prj_sc_id)]

        # Get projects and zones from input data and convert to dictionary with projects as key
        project_load_zones_input = dict()
        project_load_zones_input = data_input_subscenario[['project', 'load_zone']].set_index(
            'project')['load_zone'].to_dict()

        project_zones.project_load_zones(
            io=io, c=c,
            project_load_zone_scenario_id=prj_sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_load_zones=project_load_zones_input
        )


def load_project_reserve_bas(io, c, subscenario_input, data_input, reserve_type_input):
    """
    Reserve types include frequency response, load following up and down, regulation up and down, and spinning reserves
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :param reserve_type_input:
    :return:
    """
    #TODO: Include "contribute_to_partial" column for inputs_project_frequency_response_bas table

    for i in subscenario_input.index:
        prj_sc_id = int(subscenario_input['project_' + reserve_type_input + '_ba_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[
            (data_input['project_' + reserve_type_input + '_ba_scenario_id'] == prj_sc_id)]

        # Get projects and bas from input data and convert to dictionary with projects as key
        project_bas_input = dict()
        project_bas_input = data_input_subscenario[['project', reserve_type_input + '_ba']].set_index(
            'project')[reserve_type_input + '_ba'].to_dict()

        project_zones.project_reserve_bas(
            io=io, c=c,
            reserve_type=reserve_type_input,
            project_reserve_scenario_id=prj_sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_bas=project_bas_input
        )

def load_project_policy_zones(io, c, subscenario_input, data_input, policy_type_input):
    """
    Policy types include carbon cap, prm, and rps
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :param policy_type_input:
    :return:
    """

    for i in subscenario_input.index:
        prj_sc_id = int(subscenario_input['project_' + policy_type_input + '_zone_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[
            (data_input['project_' + policy_type_input + '_zone_scenario_id'] == prj_sc_id)]

        # Get projects and zones from input data and convert to dictionary with projects as key
        project_policy_zones_input = dict()
        project_policy_zones_input = data_input_subscenario[['project', policy_type_input + '_zone']].set_index(
            'project')[policy_type_input + '_zone'].to_dict()

        project_zones.project_policy_zones(
            io=io, c=c,
            policy_type=policy_type_input,
            project_policy_zone_scenario_id=prj_sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_zones=project_policy_zones_input
        )
