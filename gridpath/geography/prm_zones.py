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
                                           "inputs", "prm_zones.tab"),
                     set=m.PRM_ZONES
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    prm_zones = c.execute(
        """SELECT prm_zone
        FROM inputs_geography_prm_zones
        WHERE prm_zone_scenario_id = {};
        """.format(
            subscenarios.PRM_ZONE_SCENARIO_ID
        )
    )

    return prm_zones


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
    prm_zones.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    prm_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "prm_zones.tab"),
              "w", newline="") as \
            prm_zones_tab_file:
        writer = csv.writer(prm_zones_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["prm_zone"])

        for row in prm_zones:
            writer.writerow(row)
