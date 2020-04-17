#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.geography.load_zones** module describes the geographic unit
at which load is met. Here, we also define whether violations
(overgeneration and unserved energy) are allowed and what the violation
costs are.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the dynamic inputs class object; not used here

    The module adds the *LOAD_ZONES* set to the model formulation.

    We will designate the *LOAD_ZONES* set with *Z* and the load zones index
    will be *z*.
    """
    m.LOAD_ZONES = Set()

    m.allow_overgeneration = Param(m.LOAD_ZONES, within=Boolean)
    m.overgeneration_penalty_per_mw = \
        Param(m.LOAD_ZONES, within=NonNegativeReals)
    m.allow_unserved_energy = Param(m.LOAD_ZONES, within=Boolean)
    m.unserved_energy_penalty_per_mw = \
        Param(m.LOAD_ZONES, within=NonNegativeReals)


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
    data_portal.load(filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                                           "inputs", "load_zones.tab"),
                     index=m.LOAD_ZONES,
                     param=(
                         m.allow_overgeneration,
                         m.overgeneration_penalty_per_mw,
                         m.allow_unserved_energy,
                         m.unserved_energy_penalty_per_mw)
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
    load_zones = c.execute("""
        SELECT load_zone, allow_overgeneration, overgeneration_penalty_per_mw, 
        allow_unserved_energy, unserved_energy_penalty_per_mw
        FROM inputs_geography_load_zones
        WHERE load_zone_scenario_id = {};
        """.format(subscenarios.LOAD_ZONE_SCENARIO_ID)
    )

    return load_zones


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
    # load_zones = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    load_zones.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    load_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "load_zones.tab"),
              "w", newline="") as \
            load_zones_tab_file:
        writer = csv.writer(load_zones_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["load_zone",
                         "allow_overgeneration",
                         "overgeneration_penalty_per_mw",
                         "allow_unserved_energy",
                         "unserved_energy_penalty_per_mw"])

        for row in load_zones:
            writer.writerow(row)
