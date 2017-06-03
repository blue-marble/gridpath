#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon cap targets
"""


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

    print("carbon cap targets")

    # Subscenario
    c.execute(
        """INSERT INTO subscenarios_system_carbon_cap_targets
        (carbon_cap_target_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            carbon_cap_target_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for zone in zone_period_targets.keys():
        for period in zone_period_targets[zone].keys():
            c.execute(
                """INSERT INTO inputs_system_carbon_cap_targets
                (carbon_cap_target_scenario_id, carbon_cap_zone, period,
                carbon_cap_mmt)
                VALUES ({}, '{}', {}, {});""".format(
                    carbon_cap_target_scenario_id, zone, period,
                    zone_period_targets[zone][period]
                )
            )
    io.commit()


if __name__ == "__main__":
    pass
