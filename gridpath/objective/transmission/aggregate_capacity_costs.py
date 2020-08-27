#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates transmission-line-period-level capacity costs
for use in the objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    Add total transmission capacity costs to cost components
    :param d:
    :return:
    """

    getattr(d, total_cost_components).append("Total_Tx_Capacity_Costs")


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def total_tx_capacity_cost_rule(mod):
        """
        **Expression Name**: Total_Tx_Capacity_Costs

        The total transmission capacity cost is equal to the transmission
        capacity cost times the period's discount factor times the number of
        years represented in the period, summed up for each of the periods.
        """
        return sum(mod.Tx_Capacity_Cost_in_Prd[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.TX_OPR_PRDS)
    m.Total_Tx_Capacity_Costs = Expression(rule=total_tx_capacity_cost_rule)
