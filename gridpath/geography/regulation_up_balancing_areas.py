#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.REGULATION_UP_ZONES = Set()


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
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "regulation_up_balancing_areas.tab"),
        select=("balancing_area",),
        index=m.REGULATION_UP_ZONES,
        param=()
    )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    ::param conn: database connection
    :return:
    """
    c = conn.cursor()
    reg_up_bas = c.execute(
        """SELECT regulation_up_ba, 
           violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_regulation_up_bas
           WHERE regulation_up_ba_scenario_id = {};""".format(
            subscenarios.REGULATION_UP_BA_SCENARIO_ID
        )
    )
    return reg_up_bas


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
    # reg_up_bas = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    regulation_up_balancing_areas.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    ::param conn: database connection
    :return:
    """

    reg_up_bas = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "regulation_up_balancing_areas.tab"), "w") as \
            reg_up_bas_tab_file:
        writer = csv.writer(reg_up_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in reg_up_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
