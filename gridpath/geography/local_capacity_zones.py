#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Zones where local capacity constraint is enforced; these can be different from
the load zones and other balancing areas.
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

    m.LOCAL_CAPACITY_ZONES = Set()


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs",
                                           "local_capacity_zones.tab"),
                     select=("local_capacity_zone",),
                     index=m.LOCAL_CAPACITY_ZONES,
                     param=()
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    ::param conn: database connection
    :return:
    """
    c = conn.cursor()
    local_capacity_zones = c.execute(
        """SELECT local_capacity_zone, 
        local_capacity_shortage_penalty_per_mw
        FROM inputs_geography_local_capacity_zones
        WHERE local_capacity_zone_scenario_id = {};
        """.format(
            subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID
        )
    )

    return local_capacity_zones


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # prm_zones = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    local_capacity_zones.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    ::param conn: database connection
    :return:
    """

    local_capacity_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "local_capacity_zones.tab"),
              "w") as \
            local_capacity_zones_file:
        writer = csv.writer(local_capacity_zones_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["local_capacity_zone", "local_capacity_shortage_penalty_per_mw"]
        )

        for row in local_capacity_zones:
            writer.writerow([row[0], row[1]])
