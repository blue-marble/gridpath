#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
System load
"""
from __future__ import print_function


def insert_system_static_loads(
        io, c,
        load_scenario_id,
        scenario_name,
        scenario_description,
        zone_timepoint_static_loads
):
    """
    :param io: 
    :param c: 
    :param load_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param zone_timepoint_static_loads: 
    :return: 
    """

    print("system static loads")

    # Subscenario
    c.execute(
        """INSERT INTO subscenarios_system_load
        (load_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            load_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for z in list(zone_timepoint_static_loads.keys()):
        for tmp in list(zone_timepoint_static_loads[z].keys()):
            c.execute(
                """INSERT INTO inputs_system_load
                (load_scenario_id, load_zone, timepoint, load_mw)
                VALUES ({}, '{}', {}, {});""".format(
                    load_scenario_id, z, tmp,
                    zone_timepoint_static_loads[z][tmp]
                )
            )


if __name__ == "__main__":
    pass
