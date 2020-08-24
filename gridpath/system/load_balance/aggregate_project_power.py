#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module, aggregates the power production by all operational projects
to create a load-balance production component, and adds it to the
load-balance constraint.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import \
    load_balance_production_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    This method adds the power production to the dynamic components.
    :param d:
    :return:
    """
    getattr(d, load_balance_production_components).append(
        "Power_Production_in_Zone_MW")


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we add the *Power_Production_in_Zone_MW* expression -- an
    aggregation of power production by all operational projects in each load
    zone *z* and timepoint *tmp* --and add it to the dynamic load-balance
    production components that will go into the load balance constraint in
    the *load_balance* module (i.e. the constraint's lhs).

    :math:`Power\_Production\_in\_Zone\_MW_{z, tmp} =
    \sum_{r^z\in OR_{tmp}}{Power\_Provision\_MW_{r, tmp}}`
    """

    # Add power generation to load balance constraint
    # TODO: is this better done with a set intersection (all projects in the
    #  zone intersected with all operational project sin the timepoint)
    def total_power_production_rule(mod, z, tmp):
        return sum(mod.Power_Provision_MW[g, tmp]
                   for g in mod.OPR_PRJS_IN_TMP[tmp]
                   if mod.load_zone[g] == z)
    m.Power_Production_in_Zone_MW = \
        Expression(m.LOAD_ZONES, m.TMPS,
                   rule=total_power_production_rule)
