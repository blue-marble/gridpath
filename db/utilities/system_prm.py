#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
ELCC characteristics of projects
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def prm_requirement(
        io, c,
        prm_requirement_scenario_id,
        scenario_name,
        scenario_description,
        zone_period_requirement
):
    """

    :param io:
    :param c:
    :param prm_requirement_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zone_period_requirement:
    :param prm_zone_scenario_id:
    :return:
    """

    # Subscenarios
    subs_data = [(prm_requirement_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_system_prm_requirement
        (prm_requirement_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for zone in list(zone_period_requirement.keys()):
        for period in list(zone_period_requirement[zone].keys()):
            inputs_data.append(
                (prm_requirement_scenario_id, zone, period,
                    zone_period_requirement[zone][period])
            )
    inputs_sql = """
        INSERT INTO inputs_system_prm_requirement
        (prm_requirement_scenario_id, 
        prm_zone, period, prm_requirement_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
