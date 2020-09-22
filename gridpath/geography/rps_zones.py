#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Zones where RPS will be enforced; these can be different from the load zones
and reserve balancing areas.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, di, dc):
    """

    :param m:
    :param d:
    :return:
    """

    m.RPS_ZONES = Set()

    m.rps_allow_violation = Param(
        m.RPS_ZONES, within=Boolean, default=0
    )
    m.rps_violation_penalty_per_mwh = Param(
        m.RPS_ZONES, within=NonNegativeReals, default=0
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):

    data_portal.load(filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                                           "inputs", "rps_zones.tab"),
                     index=m.RPS_ZONES,
                     param=(m.rps_allow_violation,
                            m.rps_violation_penalty_per_mwh)
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    rps_zones = c.execute(
        """SELECT rps_zone, allow_violation, violation_penalty_per_mwh
           FROM inputs_geography_rps_zones
           WHERE rps_zone_scenario_id = {};""".format(
            subscenarios.RPS_ZONE_SCENARIO_ID
        )
    )

    return rps_zones


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
    # rps_zones = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    rps_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    rps_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "rps_zones.tab"),
              "w", newline="") as \
            rps_zones_tab_file:
        writer = csv.writer(rps_zones_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["rps_zone", "allow_violation",
                         "violation_penalty_per_mwh"])

        for row in rps_zones:
            writer.writerow(row)
