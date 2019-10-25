#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.LF_RESERVES_DOWN_ZONES = Set()

    m.lf_reserves_down_allow_violation = Param(
        m.LF_RESERVES_DOWN_ZONES, within=Boolean
    )
    m.lf_reserves_down_violation_penalty_per_mw = Param(
        m.LF_RESERVES_DOWN_ZONES, within=NonNegativeReals
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
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "load_following_down_balancing_areas.tab"),
        select=("balancing_area", "allow_violation",
                "violation_penalty_per_mw"),
        index=m.LF_RESERVES_DOWN_ZONES,
        param=(m.lf_reserves_down_allow_violation,
               m.lf_reserves_down_violation_penalty_per_mw)
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
    lf_down_bas = c.execute(
            """SELECT lf_reserves_down_ba, allow_violation,
               violation_penalty_per_mw, reserve_to_energy_adjustment
               FROM inputs_geography_lf_reserves_down_bas
               WHERE lf_reserves_down_ba_scenario_id = {};""".format(
                subscenarios.LF_RESERVES_DOWN_BA_SCENARIO_ID
            )
    )

    return lf_down_bas


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
    # lf_down_bas = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    load_following_down_balancing_areas.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    lf_down_bas = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "load_following_down_balancing_areas.tab"), "w", newline="") as \
            lf_down_bas_tab_file:
        writer = csv.writer(lf_down_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area", "allow_violation",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in lf_down_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
