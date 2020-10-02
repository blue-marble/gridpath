#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    m.REGULATION_DOWN_ZONES = Set()

    m.regulation_down_allow_violation = Param(
        m.REGULATION_DOWN_ZONES, within=Boolean
    )
    m.regulation_down_violation_penalty_per_mw = Param(
        m.REGULATION_DOWN_ZONES, within=NonNegativeReals
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
                              "regulation_down_balancing_areas.tab"),
        select=("balancing_area", "allow_violation",
                "violation_penalty_per_mw"),
        index=m.REGULATION_DOWN_ZONES,
        param=(m.regulation_down_allow_violation,
               m.regulation_down_violation_penalty_per_mw)
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
    reg_down_bas = c.execute(
        """SELECT regulation_down_ba, allow_violation,
           violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_regulation_down_bas
           WHERE regulation_down_ba_scenario_id = {};""".format(
            subscenarios.REGULATION_DOWN_BA_SCENARIO_ID
        )
    )

    return reg_down_bas


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
    # reg_down_bas = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    regulation_down_balancing_areas.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    reg_down_bas = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "regulation_down_balancing_areas.tab"), "w", newline="") as \
            reg_down_bas_tab_file:
        writer = csv.writer(reg_down_bas_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["balancing_area", "allow_violation",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in reg_down_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
