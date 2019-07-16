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
    m.SPINNING_RESERVES_ZONES = Set()


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
                              "spinning_reserves_balancing_areas.tab"),
        select=("balancing_area",),
        index=m.SPINNING_RESERVES_ZONES,
        param=()
    )


def load_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    spinning_reserves_bas = c.execute(
        """SELECT spinning_reserves_ba, 
           violation_penalty_per_mw, reserve_to_energy_adjustment
           FROM inputs_geography_spinning_reserves_bas
           WHERE spinning_reserves_ba_scenario_id = {};""".format(
            subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID
        )
    ).fetchall()

    return spinning_reserves_bas


def validate_inputs(subscenarios, subproblem, stage, c):
    """
    Load the inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    pass
    # Validation to be added
    # spinning_bas = load_inputs_from_database(
    #     subscenarios, subproblem, stage, c)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Load the inputs from database and write out the model input
    spinning_reserves_balancing_areas.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    spinning_reserves_bas = load_inputs_from_database(
        subscenarios, subproblem, stage, c)

    with open(os.path.join(inputs_directory,
                           "spinning_reserves_balancing_areas.tab"), "w") as \
            spinning_reserve_bas_tab_file:
        writer = csv.writer(spinning_reserve_bas_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["balancing_area",
                         "violation_penalty_per_mw",
                         "reserve_to_energy_adjustment"])

        for row in spinning_reserves_bas:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
