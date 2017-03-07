#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon cap for each carbon_cap zone
"""

import csv
import os.path
import pandas as pd

from pyomo.environ import Set, Param, NonNegativeReals, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP = \
        Set(dimen=2, within=m.CARBON_CAP_ZONES * m.PERIODS)
    m.carbon_cap_target_mmt = Param(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        within=NonNegativeReals)


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
                                           "inputs", "carbon_cap.tab"),
                     index=m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
                     param=m.carbon_cap_target_mmt,
                     select=("carbon_cap_zone", "period",
                             "carbon_cap_target_mmt")
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # carbon_cap.tab
    with open(os.path.join(inputs_directory,
                           "carbon_cap.tab"), "w") as \
            carbon_cap_file:
        writer = csv.writer(carbon_cap_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["carbon_cap_zone", "period", "carbon_cap_target_mmt"]
        )

        carbon_cap = c.execute(
            """SELECT carbon_cap_zone, period, carbon_cap_target_mmt
            FROM carbon_cap_targets
            WHERE period_scenario_id = {}
            AND carbon_cap_zone_scenario_id = {}
            AND carbon_cap_target_scenario_id = {};
            """.format(
                subscenarios.PERIOD_SCENARIO_ID,
                subscenarios.CARBON_CAP_ZONE_SCENARIO_ID,
                subscenarios.CARBON_CAP_TARGET_SCENARIO_ID
            )
        )
        for row in carbon_cap:
            writer.writerow(row)
