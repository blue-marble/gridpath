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


def add_model_components(m, d):
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
    m.static_load_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS,
                             within=NonNegativeReals)
    getattr(d, load_balance_consumption_components).append("static_load_mw")


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(
            scenario_directory, horizon, stage, "inputs", "load_mw.tab"
        ),
        param=m.static_load_mw
    )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # load_mw.tab
    with open(os.path.join(inputs_directory,
                           "load_mw.tab"), "w") as \
            load_tab_file:
        writer = csv.writer(load_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["LOAD_ZONES", "TIMEPOINTS", "load_mw"]
        )

        loads = c.execute(
            """SELECT load_zone, timepoint, load_mw
            FROM inputs_system_load
            INNER JOIN
            (SELECT timepoint
            FROM inputs_temporal_timepoints
            WHERE timepoint_scenario_id = {}) as relevant_timepoints
            USING (timepoint)
            INNER JOIN
            (SELECT load_zone
            FROM inputs_geography_load_zones
            WHERE load_zone_scenario_id = {}) as relevant_load_zones
            USING (load_zone)
            WHERE load_scenario_id = {}
            """.format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.LOAD_SCENARIO_ID
            )
        )
        for row in loads:
            writer.writerow(row)
