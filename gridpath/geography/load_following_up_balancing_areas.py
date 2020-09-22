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
    m.LF_RESERVES_UP_ZONES = Set()

    m.lf_reserves_up_allow_violation = Param(
        m.LF_RESERVES_UP_ZONES, within=Boolean
    )
    m.lf_reserves_up_violation_penalty_per_mw = Param(
        m.LF_RESERVES_UP_ZONES, within=NonNegativeReals
    )


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
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "load_following_up_balancing_areas.tab"),
        select=("balancing_area", "allow_violation",
                "violation_penalty_per_mw"),
        index=m.LF_RESERVES_UP_ZONES,
        param=(m.lf_reserves_up_allow_violation,
               m.lf_reserves_up_violation_penalty_per_mw)
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
    lf_up_bas = c.execute(
        """SELECT lf_reserves_up_ba, allow_violation,
        violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_lf_reserves_up_bas
           WHERE lf_reserves_up_ba_scenario_id = {};""".format(
            subscenarios.LF_RESERVES_UP_BA_SCENARIO_ID
        )
    )

    return lf_up_bas


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
    # lf_up_bas = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    load_following_up_balancing_areas.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    lf_up_bas = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "load_following_up_balancing_areas.tab"), "w", newline="") as \
            lf_up_bas_tab_file:
        writer = csv.writer(lf_up_bas_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["balancing_area", "allow_violation",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in lf_up_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
