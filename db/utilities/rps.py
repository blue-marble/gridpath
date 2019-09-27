#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
RPS targets
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def insert_rps_targets(
        io, c,
        rps_target_scenario_id,
        scenario_name,
        scenario_description,
        zone_period_targets
):
    """
    :param io: 
    :param c: 
    :param rps_target_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param zone_period_targets: 
    :return: 
    """

    print("rps targets")

    # Subscenario
    subs_data = [(rps_target_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = \
        """INSERT INTO subscenarios_system_rps_targets
        (rps_target_scenario_id, name, description)
        VALUES (?, ?, ?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for zone in list(zone_period_targets.keys()):
        for period in list(zone_period_targets[zone].keys()):
            inputs_data.append(
                (rps_target_scenario_id, zone, period,
                 zone_period_targets[zone][period])
            )
    inputs_sql = \
        """INSERT INTO inputs_system_rps_targets
        (rps_target_scenario_id, rps_zone, period,
        rps_target_mwh)
        VALUES (?, ?, ?, ?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
