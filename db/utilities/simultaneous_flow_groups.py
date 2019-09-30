#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Groups of transmission lines over which simultaneous flow constraints will 
be applied
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def insert_transmission_simultaneous_flow_groups(
        io, c,
        transmission_simultaneous_flow_limit_line_group_scenario_id,
        scenario_name,
        scenario_description,
        group_lines
):
    """

    :param io: 
    :param c: 
    :param transmission_simultaneous_flow_limit_line_group_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param group_lines: 
    Dictionary with the group name as key and lists of tuples with the 
    lines in that group as the first tuple element and the line direction 
    (1 or -1) as the second tuple element as dictionary values 
    :return: 
    """
    print("transmission simultaneous flow groups")

    # Subscenarios
    subs_data = [(transmission_simultaneous_flow_limit_line_group_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_transmission_simultaneous_flow_limit_line_groups
        (transmission_simultaneous_flow_limit_line_group_scenario_id, name,
        description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for group in list(group_lines.keys()):
        for tx_line in group_lines[group]:
            inputs_data.append(
                (transmission_simultaneous_flow_limit_line_group_scenario_id,
                    group, tx_line[0], tx_line[1])
            )
    inputs_sql = """
        INSERT INTO 
        inputs_transmission_simultaneous_flow_limit_line_groups
        (transmission_simultaneous_flow_limit_line_group_scenario_id,
        transmission_simultaneous_flow_limit,
        transmission_line, simultaneous_flow_direction)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
