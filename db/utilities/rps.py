#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
RPS targets
"""


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
    c.execute(
        """INSERT INTO subscenarios_system_rps_targets
        (rps_target_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            rps_target_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for zone in zone_period_targets.keys():
        for period in zone_period_targets[zone].keys():
            c.execute(
                """INSERT INTO inputs_system_rps_targets
                (rps_target_scenario_id, rps_zone, period,
                rps_target_mwh)
                VALUES ({}, '{}', {}, {});""".format(
                    rps_target_scenario_id, zone, period,
                    zone_period_targets[zone][period]
                )
            )
    io.commit()


if __name__ == "__main__":
    pass
