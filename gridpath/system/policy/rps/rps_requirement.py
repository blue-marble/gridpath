#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simplest implementation with a MWh target
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

    m.RPS_ZONE_PERIODS_WITH_RPS = \
        Set(dimen=2, within=m.RPS_ZONES * m.PERIODS)
    m.rps_target_mwh = Param(m.RPS_ZONE_PERIODS_WITH_RPS,
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
                                           "inputs", "rps_targets.tab"),
                     index=m.RPS_ZONE_PERIODS_WITH_RPS,
                     param=m.rps_target_mwh,
                     select=("rps_zone", "period", "rps_target_mwh")
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # rps_targets.tab
    with open(os.path.join(inputs_directory,
                           "rps_targets.tab"), "w") as \
            rps_targets_tab_file:
        writer = csv.writer(rps_targets_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["rps_zone", "period", "rps_target_mwh"]
        )

        rps_targets = c.execute(
            """SELECT rps_zone, period, rps_target_mwh
            FROM rps_targets
            WHERE period_scenario_id = {}
            AND horizon_scenario_id = {}
            AND timepoint_scenario_id = {}
            AND load_zone_scenario_id = {}
            AND rps_zone_scenario_id = {}
            AND rps_target_scenario_id = {};
            """.format(
                subscenarios.PERIOD_SCENARIO_ID,
                subscenarios.HORIZON_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.RPS_ZONE_SCENARIO_ID,
                subscenarios.RPS_TARGET_SCENARIO_ID
            )
        )
        for row in rps_targets:
            writer.writerow(row)
