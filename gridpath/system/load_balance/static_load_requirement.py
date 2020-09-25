#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module adds the main load-balance consumption component, the static
load requirement to the load-balance constraint.
"""

import csv
import os.path
from pyomo.environ import Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    load_balance_consumption_components


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds the static load to the load balance dynamic components.
    """
    print("Load dynamic components")
    getattr(dynamic_components, load_balance_consumption_components).append(
        "static_load_mw")
    print(dynamic_components.load_balance_consumption_components)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we add the *static_load_mw* parameter -- the load requirement --
    defined for each load zone *z* and timepoint *tmp*, and add it to the
    dynamic load-balance consumption components that will go into the load
    balance constraint in the *load_balance* module (i.e. the constraint's
    rhs).
    """

    # Static load
    m.static_load_mw = Param(m.LOAD_ZONES, m.TMPS,
                             within=NonNegativeReals)

    record_dynamic_components(dynamic_components=d)


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
        filename=os.path.join(
            scenario_directory, subproblem, stage, "inputs", "load_mw.tab"
        ),
        param=m.static_load_mw
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
    # Select only profiles for timepoints form the correct temporal
    # scenario and the correct subproblem
    # Select only profiles of load_zones that are part of the correct
    # load_zone_scenario
    # Select only profiles for the correct load_scenario
    loads = c.execute(
        """SELECT load_zone, timepoint, load_mw
        FROM inputs_system_load
        INNER JOIN
        (SELECT timepoint
        FROM inputs_temporal
        WHERE temporal_scenario_id = {}
        AND subproblem_id ={}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT load_zone
        FROM inputs_geography_load_zones
        WHERE load_zone_scenario_id = {}) as relevant_load_zones
        USING (load_zone)
        WHERE load_scenario_id = {}
        and stage_id = {}
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.LOAD_ZONE_SCENARIO_ID,
            subscenarios.LOAD_SCENARIO_ID,
            stage
        )
    )

    return loads


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
    # loads = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    load_mw.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    loads = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "load_mw.tab"), "w", newline="") as \
            load_tab_file:
        writer = csv.writer(load_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["LOAD_ZONES", "timepoint", "load_mw"]
        )

        for row in loads:
            writer.writerow(row)
