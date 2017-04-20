#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Zones where PRM is enforced; these can be different from the load
zones and other balancing areas.
"""

import csv
import os.path
from pyomo.environ import Set


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.PRM_ZONES = Set()


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """
    
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param horizon: 
    :param stage: 
    :return: 
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "prm_zones.tab"),
                     set=m.PRM_ZONES
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """
    prm_zones.tab
    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    with open(os.path.join(inputs_directory,
                           "prm_zones.tab"), "w") as \
            prm_zones_file:
        writer = csv.writer(prm_zones_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["prm_zone"]
        )

        prm_zones = c.execute(
            """SELECT prm_zone
            FROM inputs_geography_prm_zones
            WHERE prm_zone_scenario_id = {};
            """.format(
                subscenarios.PRM_ZONE_SCENARIO_ID
            )
        )
        for row in prm_zones:
            writer.writerow(row)
