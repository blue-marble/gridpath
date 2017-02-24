#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Constraint total carbon emissions to be less than cap
"""

import csv
import os.path

from pyomo.environ import Constraint, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def carbon_cap_target_rule(mod, z, p):
        """
        Total carbon emitted must be less than target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Carbon_Emissions_Tons[z, p] \
            <= mod.carbon_cap_target_mmt[z, p] * 10**6  # convert to tons

    m.Carbon_Cap_Constraint = Constraint(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=carbon_cap_target_rule
    )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "carbon_cap.csv"), "wb") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["carbon_cap_zone", "period", "carbon_cap_target_mmt",
                         "carbon_emissions_mmt"])
        for (z, p) in m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP:
            writer.writerow([
                z,
                p,
                float(m.carbon_cap_target_mmt[z, p]),
                value(m.Total_Carbon_Emissions_Tons[z, p]) / 10**6  # MMT
            ])


def save_duals(m):
    m.constraint_indices["Carbon_Cap_Constraint"] = \
        ["carbon_cap_zone", "period", "dual"]
