#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon cap for each carbon_cap zone
"""

import csv
import os.path
import pandas as pd

from pyomo.environ import Set, Param, NonNegativeReals, value


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP = \
        Set(dimen=2, within=m.CARBON_CAP_ZONES * m.PERIODS)
    m.carbon_cap_target = Param(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                                           "inputs", "carbon_cap.tab"),
                     index=m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
                     param=m.carbon_cap_target,
                     select=("carbon_cap_zone", "period",
                             "carbon_cap_target")
                     )


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
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
    carbon_cap_targets = c.execute(
        """SELECT carbon_cap_zone, period, carbon_cap
        FROM inputs_system_carbon_cap_targets
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        JOIN
        (SELECT carbon_cap_zone
        FROM inputs_geography_carbon_cap_zones
        WHERE carbon_cap_zone_scenario_id = {}) as relevant_zones
        using (carbon_cap_zone)
        WHERE carbon_cap_target_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.CARBON_CAP_ZONE_SCENARIO_ID,
            subscenarios.CARBON_CAP_TARGET_SCENARIO_ID,
            subproblem,
            stage
        )
    )

    return carbon_cap_targets


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
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
    # carbon_cap_targets = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    carbon_cap.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    carbon_cap_targets = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "carbon_cap.tab"), "w", newline="") as \
            carbon_cap_file:
        writer = csv.writer(carbon_cap_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["carbon_cap_zone", "period", "carbon_cap_target"]
        )

        for row in carbon_cap_targets:
            writer.writerow(row)
