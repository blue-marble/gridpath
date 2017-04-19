#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate simple PRM contribution from the project level to the PRM zone level 
for each period.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import \
    prm_balance_provision_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_prm_provision_rule(mod, z, p):
        """
        
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.PRM_Simple_Contribution_MW[g, p]
                   for g in mod.PRM_PROJECTS_BY_PRM_ZONE[z]
                   if (g, p) in mod.PRM_PROJECT_OPERATIONAL_PERIODS)

    m.Total_PRM_Simple_Contribution_MW = Expression(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        rule=total_prm_provision_rule
    )

    # Add to emission imports to carbon balance
    getattr(d, prm_balance_provision_components).append(
        "Total_PRM_Simple_Contribution_MW"
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
    pass
