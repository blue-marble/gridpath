#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""
from db.common_functions import spin_on_database_lock


def local_capacity_requirement(
        io, c,
        local_capacity_requirement_scenario_id,
        scenario_name,
        scenario_description,
        zone_period_requirement
):
    """

    :param io:
    :param c:
    :param local_capacity_requirement_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zone_period_requirement:
    :return:
    """
    # TODO: could refactor this with the other system requirements inputs
    #  such as PRM, load, ...
    # Subscenarios
    subs_data = [(local_capacity_requirement_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_system_local_capacity_requirement
        (local_capacity_requirement_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for zone in list(zone_period_requirement.keys()):
        for period in list(zone_period_requirement[zone].keys()):
            inputs_data.append(
                (local_capacity_requirement_scenario_id, zone, period,
                    zone_period_requirement[zone][period])
            )
    inputs_sql = """
        INSERT INTO inputs_system_local_capacity_requirement
        (local_capacity_requirement_scenario_id, 
        local_capacity_zone, period, local_capacity_requirement_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
