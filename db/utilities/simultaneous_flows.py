#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simultaneous flow limits
"""


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
    c.execute(
        """INSERT INTO subscenarios_transmission_simultaneous_flow_limits
        (transmission_simultaneous_flow_limit_scenario_id, name,
        description)
        VALUES ({}, '{}', '{}');""".format(
            transmission_simultaneous_flow_limit_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for group in group_period_limits.keys():
        for period in group_period_limits[group].keys():
            c.execute(
                """INSERT INTO
                inputs_transmission_simultaneous_flow_limits
                (transmission_simultaneous_flow_limit_scenario_id,
                transmission_simultaneous_flow_limit, period,
                max_flow_mw)
                VALUES ({}, '{}', {}, {})""".format(
                    transmission_simultaneous_flow_limit_scenario_id,
                    group, period, group_period_limits[group][period]
                )
            )
    io.commit()
