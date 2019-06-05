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
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "rps_targets.tab"),
        index=m.RPS_ZONE_PERIODS_WITH_RPS,
        param=m.rps_target_mwh,
        select=("rps_zone", "period", "rps_target_mwh")
    )


def get_inputs_from_database(subscenarios, subproblem, stage,
                             c, inputs_directory):
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
            FROM inputs_system_rps_targets
            JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {}) as relevant_periods
            USING (period)
            JOIN
            (SELECT rps_zone
            FROM inputs_geography_rps_zones
            WHERE rps_zone_scenario_id = {}) as relevant_zones
            using (rps_zone)
            WHERE rps_target_scenario_id = {};
            """.format(
                subscenarios.TEMPORAL_SCENARIO_ID,
                subscenarios.RPS_ZONE_SCENARIO_ID,
                subscenarios.RPS_TARGET_SCENARIO_ID
            )
        )
        for row in rps_targets:
            writer.writerow(row)
