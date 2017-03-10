#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Zones where RPS will be enforced; these can be different from the load zones
and reserve balancing areas.
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

    m.RPS_ZONES = Set()


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "rps_zones.tab"),
                     set=m.RPS_ZONES
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # rps_zones.tab

    with open(os.path.join(inputs_directory, "rps_zones.tab"),
              "w") as \
            rps_zones_tab_file:
        writer = csv.writer(rps_zones_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["rps_zone"])

        rps_zones = c.execute(
            """SELECT rps_zone
               FROM inputs_geography_rps_zones
               WHERE rps_zone_scenario_id = {};""".format(
                subscenarios.RPS_ZONE_SCENARIO_ID
            )
        ).fetchall()

        for row in rps_zones:
            writer.writerow(row)