#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simultaneous flow limits
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def insert_transmission_simultaneous_flow_limits(
        io, c,
        transmission_simultaneous_flow_limit_scenario_id,
        scenario_name,
        scenario_description,
        group_period_limits
):
    """

    :param io: 
    :param c: 
    :param transmission_simultaneous_flow_limit_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param group_period_limits: 
    Two-level dictionary with the names of the transmission line groups as 
    top-level keys, the period as second key, and the flow limit
    :return: 
    """
    print("transmission simultaneous flow limits")

    # Subscenarios
    subs_data = [(transmission_simultaneous_flow_limit_scenario_id,
            scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for group in list(group_period_limits.keys()):
        for period in list(group_period_limits[group].keys()):
            inputs_data.append(
                (transmission_simultaneous_flow_limit_scenario_id,
                    group, period, group_period_limits[group][period])
            )
    inputs_sql = """
        INSERT INTO
        inputs_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id,
        transmission_simultaneous_flow_limit, period,
        max_flow_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
