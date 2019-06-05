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


def get_inputs_from_database(subscenarios, subproblem, stage,
                             c, inputs_directory):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param c:
    :param inputs_directory:
    :return:
    """
    # frequency_response_balancing_areas.tab
    with open(os.path.join(inputs_directory,
                           "frequency_response_balancing_areas.tab"),
              "w") as \
            lf_down_bas_tab_file:
        writer = csv.writer(lf_down_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        lf_down_bas = c.execute(
            """SELECT frequency_response_ba, 
               violation_penalty_per_mw, reserve_to_energy_adjustment
               FROM inputs_geography_frequency_response_bas
               WHERE frequency_response_ba_scenario_id = {};""".format(
                subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID
            )
        ).fetchall()

        for row in lf_down_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
