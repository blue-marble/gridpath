#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, di, dc):
    """

    :param m:
    :param d:
    :return:
    """
    m.SPINNING_RESERVES_ZONES = Set()

    m.spinning_reserves_allow_violation = Param(
        m.SPINNING_RESERVES_ZONES, within=Boolean
    )
    m.spinning_reserves_violation_penalty_per_mw = Param(
        m.SPINNING_RESERVES_ZONES, within=NonNegativeReals
    )


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
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "spinning_reserves_balancing_areas.tab"),
        select=("balancing_area", "allow_violation",
                "violation_penalty_per_mw"),
        index=m.SPINNING_RESERVES_ZONES,
        param=(m.spinning_reserves_allow_violation,
               m.spinning_reserves_violation_penalty_per_mw)
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
    spinning_reserves_bas = c.execute(
        """SELECT spinning_reserves_ba, allow_violation,
           violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_spinning_reserves_bas
           WHERE spinning_reserves_ba_scenario_id = {};""".format(
            subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID
        )
    )

    return spinning_reserves_bas


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
    # spinning_bas = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    spinning_reserves_balancing_areas.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    spinning_reserves_bas = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "spinning_reserves_balancing_areas.tab"), "w", newline="") as \
            spinning_reserve_bas_tab_file:
        writer = csv.writer(spinning_reserve_bas_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["balancing_area", "allow_violation",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in spinning_reserves_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
