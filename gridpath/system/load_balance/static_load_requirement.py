#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Param, Var, Constraint, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    load_balance_consumption_components, load_balance_production_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
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
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "load_mw.tab"),
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
            FROM loads
            WHERE period_scenario_id = {}
            AND horizon_scenario_id = {}
            AND timepoint_scenario_id = {}
            AND load_zone_scenario_id = {}
            AND load_scenario_id = {}
            """.format(
                subscenarios.PERIOD_SCENARIO_ID,
                subscenarios.HORIZON_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.LOAD_SCENARIO_ID
            )
        )
        for row in loads:
            writer.writerow(row)
