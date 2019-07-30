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
    m.FREQUENCY_RESPONSE_BAS = Set()


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
                              "frequency_response_balancing_areas.tab"),
        select=("balancing_area",),
        index=m.FREQUENCY_RESPONSE_BAS,
        param=()
    )


def get_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    freq_resp_bas = c.execute(
        """SELECT frequency_response_ba, 
           violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_frequency_response_bas
           WHERE frequency_response_ba_scenario_id = {};""".format(
            subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID
        )
    ).fetchall()

    return freq_resp_bas


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
    # freq_resp_bas = get_inputs_from_database(
    #     subscenarios, subproblem, stage, c)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Get inputs from database and write out the model input
    frequency_response_balancing_areas.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    freq_resp_bas = get_inputs_from_database(
        subscenarios, subproblem, stage, c)

    with open(os.path.join(inputs_directory,
                           "frequency_response_balancing_areas.tab"), "w") as \
            freq_resp_bas_tab_file:
        writer = csv.writer(freq_resp_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in freq_resp_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
