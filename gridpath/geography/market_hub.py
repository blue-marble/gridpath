#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Market hub with a particular set of prices; these can be different from
the load zones and other balancing areas.
"""

import csv
import os.path
from pyomo.environ import Set


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.MARKET_HUBS = Set()


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
    data_portal.load(
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "market_hubs.tab"
        ),
        set=m.MARKET_HUBS
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
    market_hubs = c.execute(
        """SELECT market_hub
        FROM market_hubs
        WHERE market_hub_scenario_id = {};
        """.format(
            subscenarios.MARKET_HUB_SCENARIO_ID
        )
    )

    return market_hubs


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and validate the inputs.
    """
    pass


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    local_capacity_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    market_hubs = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "market_hubs.tab"
            ), "w", newline=""
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["market_hub"])

        for row in market_hubs:
            writer.writerow([row[0]])
