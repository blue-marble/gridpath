#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Groups of transmission lines over which simultaneous flow constraints will 
be applied
"""


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
    c.execute(
        """INSERT INTO subscenarios_transmission_simultaneous_flow_limit_line_groups
        (transmission_simultaneous_flow_limit_line_group_scenario_id, name,
        description)
        VALUES ({}, '{}', '{}');""".format(
            transmission_simultaneous_flow_limit_line_group_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for group in group_lines.keys():
        for tx_line in group_lines[group]:
            c.execute(
                """INSERT INTO 
                inputs_transmission_simultaneous_flow_limit_line_groups
                (transmission_simultaneous_flow_limit_line_group_scenario_id,
                transmission_simultaneous_flow_limit,
                transmission_line, simultaneous_flow_direction)
                VALUES ({}, '{}', '{}', {});""".format(
                    transmission_simultaneous_flow_limit_line_group_scenario_id,
                    group, tx_line[0], tx_line[1]
                )
            )
    io.commit()
