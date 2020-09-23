#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Local capacity requirement for each local capacity zone
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT = \
        Set(dimen=2, within=m.LOCAL_CAPACITY_ZONES * m.PERIODS)
    m.local_capacity_requirement_mw = Param(
        m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
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
                                           "inputs",
                                           "local_capacity_requirement.tab"),
                     index=m.LOCAL_CAPACITY_ZONE_PERIODS_WITH_REQUIREMENT,
                     param=m.local_capacity_requirement_mw,
                     select=("local_capacity_zone", "period",
                             "local_capacity_requirement_mw")
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    c = conn.cursor()
    local_capacity_requirement = c.execute(
        """SELECT local_capacity_zone, period, 
        local_capacity_requirement_mw
        FROM inputs_system_local_capacity_requirement
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        JOIN
        (SELECT local_capacity_zone
        FROM inputs_geography_local_capacity_zones
        WHERE local_capacity_zone_scenario_id = {}) as relevant_zones
        using (local_capacity_zone)
        WHERE local_capacity_requirement_scenario_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.LOCAL_CAPACITY_REQUIREMENT_SCENARIO_ID
        )
    )
    return local_capacity_requirement


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
    # local_capacity_requirement = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    local_capacity_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    local_capacity_requirement = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "local_capacity_requirement.tab"), "w", newline="") as \
            local_capacity_requirement_tab_file:
        writer = csv.writer(local_capacity_requirement_tab_file,
                            delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["local_capacity_zone", "period", "local_capacity_requirement_mw"]
        )

        for row in local_capacity_requirement:
            writer.writerow(row)
