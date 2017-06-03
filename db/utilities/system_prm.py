#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
ELCC characteristics of projects
"""

import warnings


def prm_requirement(
        io, c,
        prm_requirement_scenario_id,
        scenario_name,
        scenario_description,
        zone_period_requirement
):
    """

    :param io:
    :param c:
    :param prm_requirement_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zone_period_requirement:
    :param prm_zone_scenario_id:
    :return:
    """
    print("prm requirement")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_system_prm_requirement
        (prm_requirement_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            prm_requirement_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for zone in zone_period_requirement.keys():
        for period in zone_period_requirement[zone].keys():
            c.execute(
                """INSERT INTO inputs_system_prm_requirement
                (prm_requirement_scenario_id, 
                prm_zone, period, prm_requirement_mw)
                VALUES ({}, '{}', {}, {});""".format(
                    prm_requirement_scenario_id, zone, period,
                    zone_period_requirement[zone][period]
                )
            )
    io.commit()
