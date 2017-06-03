#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Transmission load zones
"""


def insert_transmission_load_zones(
        io, c,
        load_zone_scenario_id,
        transmission_load_zone_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_load_zones
):
    """

    :param io: 
    :param c: 
    :param load_zone_scenario_id: 
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
    c.execute(
        """INSERT INTO subscenarios_transmission_load_zones
        (load_zone_scenario_id, transmission_load_zone_scenario_id, 
        name, description)
        VALUES ({}, {}, '{}', '{}');""".format(
            load_zone_scenario_id,
            transmission_load_zone_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for tx_line in tx_line_load_zones.keys():
        c.execute(
            """INSERT INTO inputs_transmission_load_zones
               (load_zone_scenario_id, 
               transmission_load_zone_scenario_id,
               transmission_line, load_zone_from, load_zone_to)
               VALUES ({}, {}, '{}', '{}', '{}');""".format(
                load_zone_scenario_id,
                transmission_load_zone_scenario_id,
                tx_line,
                tx_line_load_zones[tx_line][0],
                tx_line_load_zones[tx_line][1]
        )
        )
    io.commit()


def insert_transmission_carbon_cap_zones(
        io, c,
        carbon_cap_zone_scenario_id,
        transmission_carbon_cap_zone_scenario_id,
        scenario_name,
        scenario_description,
        tx_line_carbon_cap_zones
):
    """

    :param io: 
    :param c: 
    :param carbon_cap_zone_scenario_id: 
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
    c.execute(
        """INSERT INTO subscenarios_transmission_carbon_cap_zones
        (carbon_cap_zone_scenario_id, transmission_carbon_cap_zone_scenario_id, 
        name, description)
        VALUES ({}, {}, '{}', '{}');""".format(
            carbon_cap_zone_scenario_id,
            transmission_carbon_cap_zone_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for tx_line in tx_line_carbon_cap_zones.keys():
        c.execute(
            """INSERT INTO inputs_transmission_carbon_cap_zones
               (carbon_cap_zone_scenario_id,
               transmission_carbon_cap_zone_scenario_id,
               transmission_line, carbon_cap_zone, import_direction,
               tx_co2_intensity_tons_per_mwh)
               VALUES ({}, {}, '{}', '{}', '{}', {});""".format(
                carbon_cap_zone_scenario_id,
                transmission_carbon_cap_zone_scenario_id,
                tx_line,
                tx_line_carbon_cap_zones[tx_line][0],
                tx_line_carbon_cap_zones[tx_line][1],
                tx_line_carbon_cap_zones[tx_line][2]
            )
        )
    io.commit()
