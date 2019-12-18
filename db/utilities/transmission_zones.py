#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission load zones
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def insert_transmission_load_zones(
        io, c,
        transmission_load_zone_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_load_zones
):
    """

    :param io: 
    :param c:
    :param transmission_load_zone_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_load_zones: 
    Dictionary with the names of the transmission line as keys and tuples 
    containing the 'load zone from' and 'load zone to' as values
    :return: 
    """
    print("transmission load_zones")

    # Subscenarios
    subs_data = [(transmission_load_zone_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_load_zones
        (transmission_load_zone_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for tx_line in list(tx_line_load_zones.keys()):
        inputs_data.append(
            (transmission_load_zone_scenario_id,
             tx_line,
             tx_line_load_zones[tx_line][0],
             tx_line_load_zones[tx_line][1])
        )
    inputs_sql = """
        INSERT INTO inputs_transmission_load_zones
        (transmission_load_zone_scenario_id,
        transmission_line, load_zone_from, load_zone_to)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def insert_transmission_carbon_cap_zones(
        io, c,
        transmission_carbon_cap_zone_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_carbon_cap_zones
):
    """

    :param io: 
    :param c: 
    :param transmission_carbon_cap_zone_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param tx_line_carbon_cap_zones: 
    Dictionary with the names of the transmission line as keys and tuples 
    containing the carbon_cap_zone, direction, and emissions intensity as 
    values
    :return: 
    """
    print("transmission carbon cap zones")

    # Subscenarios
    subs_data = [(transmission_carbon_cap_zone_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_carbon_cap_zones
        (transmission_carbon_cap_zone_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for tx_line in list(tx_line_carbon_cap_zones.keys()):
        inputs_data.append(
            (transmission_carbon_cap_zone_scenario_id,
             tx_line,
             tx_line_carbon_cap_zones[tx_line][0],
             tx_line_carbon_cap_zones[tx_line][1],
             tx_line_carbon_cap_zones[tx_line][2])
        )
    inputs_sql = """
        INSERT INTO inputs_transmission_carbon_cap_zones
        (transmission_carbon_cap_zone_scenario_id,
        transmission_line, carbon_cap_zone, import_direction,
        tx_co2_intensity_tons_per_mwh)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
