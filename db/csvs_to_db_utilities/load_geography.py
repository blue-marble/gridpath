#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load geography data
"""

from collections import OrderedDict

from db.utilities import geography

def load_geography_load_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for sc_id in subscenario_input['id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input['id'] == sc_id]
        load_zones = data_input_subscenario['load_zone'].to_list()

        load_zone_overgen_penalties = {}

        for l_z in load_zones:
            load_zone_overgen_penalties[l_z] = (
                int(data_input_subscenario.loc[data_input_subscenario['load_zone'] == l_z, 'allow_overgeneration'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario['load_zone'] == l_z, 'overgeneration_penalty_per_mw'].iloc[0]))

        load_zone_unserved_energy_penalties = {}

        for l_z in load_zones:
            load_zone_unserved_energy_penalties[l_z] = (
                int(data_input_subscenario.loc[data_input_subscenario['load_zone'] == l_z, 'allow_unserved_energy'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario['load_zone'] == l_z, 'unserved_energy_penalty_per_mw'].iloc[0]))

        # Load data into GridPath database
        geography.geography_load_zones(
            io=io, c=c,
            load_zone_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zones=load_zones,
            zone_overgen_penalties=load_zone_overgen_penalties,
            zone_unserved_energy_penalties=load_zone_unserved_energy_penalties
        )

def load_geography_carbon_cap_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for sc_id in subscenario_input['id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input['id'] == sc_id]
        zones = data_input_subscenario['carbon_cap_zone'].to_list()

        zone_violation_penalties = {}

        for z in zones:
            zone_violation_penalties[z] = (
                int(data_input_subscenario.loc[data_input_subscenario['carbon_cap_zone'] == z, 'allow_violation'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario['carbon_cap_zone'] == z, 'violation_penalty_per_mmt'].iloc[0]))

        # Load data into GridPath database
        geography.geography_carbon_cap_zones(
            io=io, c=c,
            carbon_cap_zone_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zones=zones,
            zone_penalties=zone_violation_penalties
        )

def load_geography_local_capacity_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for sc_id in subscenario_input['id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input['id'] == sc_id]
        zones = data_input_subscenario['local_capacity_zone'].to_list()

        zone_violation_penalties = {}

        for z in zones:
            zone_violation_penalties[z] = (
                int(data_input_subscenario.loc[data_input_subscenario['local_capacity_zone'] == z, 'allow_violation'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario['local_capacity_zone'] == z, 'violation_penalty_per_mw'].iloc[0]))

        # Load data into GridPath database
        geography.geography_local_capacity_zones(
            io=io, c=c,
            local_capacity_zone_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zones=zones,
            zone_penalties=zone_violation_penalties
        )

def load_geography_prm_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for sc_id in subscenario_input['id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input['id'] == sc_id]
        zones = data_input_subscenario['prm_zone'].to_list()

        zone_violation_penalties = {}

        for z in zones:
            zone_violation_penalties[z] = (
                int(data_input_subscenario.loc[data_input_subscenario['prm_zone'] == z, 'allow_violation'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario['prm_zone'] == z, 'violation_penalty_per_mw'].iloc[0]))

        # Load data into GridPath database
        geography.geography_prm_zones(
            io=io, c=c,
            prm_zone_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zones=zones,
            zone_penalties=zone_violation_penalties
        )

def load_geography_rps_zones(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for sc_id in subscenario_input['id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input['id'] == sc_id,
                                  'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input['id'] == sc_id]
        zones = data_input_subscenario['rps_zone'].to_list()

        zone_violation_penalties = {}

        for z in zones:
            zone_violation_penalties[z] = (
                int(data_input_subscenario.loc[data_input_subscenario['rps_zone'] == z, 'allow_violation'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario['rps_zone'] == z, 'violation_penalty_per_mwh'].iloc[0]))

        # Load data into GridPath database
        geography.geography_rps_zones(
            io=io, c=c,
            rps_zone_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zones=zones,
            zone_penalties=zone_violation_penalties
        )

#### RESERVES ####

def load_geography_reserves_bas(io, c, subscenario_input, data_input, reserve_type_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all load subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :param reserve_type_input:
    :return:
    """

    for sc_id in subscenario_input[reserve_type_input + '_ba_scenario_id'].to_list():
        sc_name = \
            subscenario_input.loc[subscenario_input[reserve_type_input + '_ba_scenario_id'] == sc_id, 'name'].iloc[0]
        sc_description = \
            subscenario_input.loc[subscenario_input[reserve_type_input + '_ba_scenario_id'] == sc_id, 'description'].iloc[0]

        data_input_subscenario = data_input.loc[data_input[reserve_type_input + '_ba_scenario_id'] == sc_id]
        bas = data_input_subscenario[reserve_type_input + '_ba'].to_list()

        ba_violation_penalties = {}

        for ba in bas:
            ba_violation_penalties[ba] = (
                int(data_input_subscenario.loc[data_input_subscenario[reserve_type_input + '_ba'] == ba, 'allow_violation'].iloc[0]),
                float(data_input_subscenario.loc[
                    data_input_subscenario[reserve_type_input + '_ba'] == ba, 'violation_penalty_per_mw'].iloc[0]))

        ba_reserve_to_energy_adjustments = {}

        for ba in bas:
            ba_reserve_to_energy_adjustments[ba] = float(data_input_subscenario.loc[
                    data_input_subscenario[reserve_type_input + '_ba'] == ba, 'reserve_to_energy_adjustment'].iloc[0])

        # Load data into GridPath database
        # Frequency response
        if reserve_type_input == 'frequency_response':
            geography.geography_frequency_response_bas(
                io=io, c=c,
                reserve_ba_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                bas=bas,
                ba_penalties=ba_violation_penalties,
                reserve_to_energy_adjustments=ba_reserve_to_energy_adjustments
            )

        # Load Following reserves down
        if reserve_type_input == 'lf_reserves_down':
            geography.geography_lf_reserves_down_bas(
                io=io, c=c,
                reserve_ba_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                bas=bas,
                ba_penalties=ba_violation_penalties,
                reserve_to_energy_adjustments=ba_reserve_to_energy_adjustments
            )

        # Load Following reserves up
        if reserve_type_input == 'lf_reserves_up':
            geography.geography_lf_reserves_up_bas(
                io=io, c=c,
                reserve_ba_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                bas=bas,
                ba_penalties=ba_violation_penalties,
                reserve_to_energy_adjustments=ba_reserve_to_energy_adjustments
            )

        # Regulation down
        if reserve_type_input == 'regulation_down':
            geography.geography_regulation_down_bas(
                io=io, c=c,
                reserve_ba_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                bas=bas,
                ba_penalties=ba_violation_penalties,
                reserve_to_energy_adjustments=ba_reserve_to_energy_adjustments
            )

        # Regulation up
        if reserve_type_input == 'regulation_up':
            geography.geography_regulation_up_bas(
                io=io, c=c,
                reserve_ba_scenario_id=sc_id,
                scenario_name=sc_name,
                scenario_description=sc_description,
                bas=bas,
                ba_penalties=ba_violation_penalties,
                reserve_to_energy_adjustments=ba_reserve_to_energy_adjustments
            )

        # Spinning reserves
        if reserve_type_input == 'spinning_reserves':
            geography.geography_spinning_reserves_bas(
                    io=io, c=c,
                    reserve_ba_scenario_id=sc_id,
                    scenario_name=sc_name,
                    scenario_description=sc_description,
                    bas=bas,
                    ba_penalties=ba_violation_penalties,
                    reserve_to_energy_adjustments=ba_reserve_to_energy_adjustments
                )
