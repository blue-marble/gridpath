#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simplest PRM contribution where each PRM project contributes a fraction of 
its installed capacity.
"""

import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # The fraction of installed capacity that counts for the PRM
    # Set this to 0 if project is included in an endogenous method for
    # determining ELCC
    m.prm_simple_fraction = Param(m.PRM_PROJECTS, within=PercentFraction)

    def prm_simple_rule(mod, g, p):
        """
        
        :param g: 
        :param p: 
        :return: 
        """
        return mod.Capacity_MW[g, p] * mod.prm_simple_fraction[g]

    m.PRM_Simple_Contribution_MW = Expression(
        m.PRM_PROJECT_OPERATIONAL_PERIODS, rule=prm_simple_rule
    )


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
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "prm_simple_fraction"),
                     param=(m.prm_simple_fraction,)
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
                           "project_prm_simple_contribution.csv"), "wb") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period",
                         "capacity_mw",
                         "prm_simple_fraction",
                         "prm_contribution_mw"])
        for (prj, period) in m.PRM_PROJECT_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                period,
                value(m.Capacity_MW[prj, period]),
                value(m.prm_simple_fraction[prj]),
                value(m.PRM_Simple_Contribution_MW[prj, period])
            ])
