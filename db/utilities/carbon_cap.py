#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon cap targets
"""

from db.common_functions import spin_on_database_lock


def insert_carbon_cap_targets(
        io, c,
        carbon_cap_target_scenario_id,
        scenario_name,
        scenario_description,
        zone_period_targets
):
    """
    :param io: 
    :param c: 
    :param carbon_cap_target_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param zone_period_targets: 
    :return: 
    """

    # Subscenario
    subs_data = [(carbon_cap_target_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_carbon_cap_targets
        (carbon_cap_target_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for zone in list(zone_period_targets.keys()):
        for period in list(zone_period_targets[zone].keys()):
            for subproblem in list(zone_period_targets[zone][period].keys()):
                for stage in list(zone_period_targets[zone][period][subproblem]
                                  .keys()):
                    inputs_data.append(
                        (carbon_cap_target_scenario_id, zone, period,
                         subproblem, stage,
                         zone_period_targets[zone][period][subproblem][stage])
                    )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_system_carbon_cap_targets
        (carbon_cap_target_scenario_id, carbon_cap_zone, period,
        subproblem_id, stage_id,
        carbon_cap)
        VALUES (?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
