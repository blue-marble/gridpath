#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
System load
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def insert_system_static_loads(
        io, c,
        load_scenario_id,
        scenario_name,
        scenario_description,
        zone_stage_timepoint_static_loads
):
    """
    :param io: 
    :param c: 
    :param load_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param zone_stage_timepoint_static_loads:
    :return: 
    """

    print("system static loads")

    # Subscenario
    subs_data = [(load_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_system_load
        (load_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for z in list(zone_stage_timepoint_static_loads.keys()):
        for stage in list(zone_stage_timepoint_static_loads[z].keys()):
            for tmp in list(
                    zone_stage_timepoint_static_loads[z][stage].keys()
            ):
                inputs_data.append(
                    (load_scenario_id, z, stage, tmp,
                        zone_stage_timepoint_static_loads[z][stage][tmp])
                )
    inputs_sql = """
        INSERT INTO inputs_system_load
        (load_scenario_id, load_zone, stage_id, timepoint, load_mw)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
