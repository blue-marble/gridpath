#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Zones where carbon cap enforced; these can be different from the load
zones and other balancing areas.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.CARBON_CAP_ZONES = Set()

    m.carbon_cap_allow_violation = Param(
        m.CARBON_CAP_ZONES, within=Boolean
    )
    m.carbon_cap_violation_penalty_per_mmt = Param(
        m.CARBON_CAP_ZONES, within=NonNegativeReals
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):

    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "carbon_cap_zones.tab"),
                     index=m.CARBON_CAP_ZONES,
                     param=(m.carbon_cap_allow_violation,
                            m.carbon_cap_violation_penalty_per_mmt)
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
    carbon_cap_zone = c.execute(
        """SELECT carbon_cap_zone, allow_violation, violation_penalty_per_mmt
        FROM inputs_geography_carbon_cap_zones
        WHERE carbon_cap_zone_scenario_id = {};
        """.format(
            subscenarios.CARBON_CAP_ZONE_SCENARIO_ID
        )
    )

    return carbon_cap_zone


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
    # carbon_cap_zone = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    carbon_cap_zones.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    carbon_cap_zone = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "carbon_cap_zones.tab"), "w", newline="") as \
            carbon_cap_zones_file:
        writer = csv.writer(carbon_cap_zones_file, delimiter="\t")

        # Write header
        writer.writerow(["carbon_cap_zone", "violation",
                         "violation_penalty_per_mmt"])

        for row in carbon_cap_zone:
            writer.writerow(row)
