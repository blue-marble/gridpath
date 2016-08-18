#!/usr/bin/env python

"""
Describe operational costs.
"""
from pyomo.environ import *


def add_model_components(m):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :return:
    """

    # ### Aggregate power costs for objective function ### #
    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def generation_cost_rule(m):
        """
        Power production cost for all generators across all timepoints
        :param m:
        :return:
        """
        return sum(m.Power_Provision[g, tmp] * m.variable_cost[g]
                   for g in m.GENERATORS for tmp in m.TIMEPOINTS)

    m.Total_Generation_Cost = Expression(rule=generation_cost_rule)
    m.total_cost_components.append("Total_Generation_Cost")

    # ### Startup and shutdown costs ### #
    m.Startup_Cost = Var(m.STARTUP_COST_GENERATORS, m.TIMEPOINTS,
                         within=NonNegativeReals)
    m.Shutdown_Cost = Var(m.SHUTDOWN_COST_GENERATORS, m.TIMEPOINTS,
                          within=NonNegativeReals)

    def startup_cost_rule(mod, g, tmp):
        """
        Startup expression is positive when more units are on in the current
        timepoint that were on in the previous timepoint. Startup_Cost is
        defined to be non-negative, so if Startup_Expression is 0 or negative
        (i.e. no units started or units shut down since the previous timepoint),
        Startup_Cost will be 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Startup_Cost[g, tmp] \
            >= mod.Startup_Expression[g, tmp] * mod.startup_cost[g]
    m.Startup_Cost_Constraint = Constraint(m.STARTUP_COST_GENERATORS,
                                           m.TIMEPOINTS,
                                           rule=startup_cost_rule)

    def shutdown_cost_rule(mod, g, tmp):
        """
        Shutdown expression is positive when more units were on in the previous
        timepoint that are on in the current timepoint. Shutdown_Cost is
        defined to be non-negative, so if Shutdown_Expression is 0 or negative
        (i.e. no units shut down or units started since the previous timepoint),
        Shutdown_Cost will be 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Shutdown_Cost[g, tmp] \
            >= mod.Shutdown_Expression[g, tmp] * mod.shutdown_cost[g]
    m.Shutdown_Cost_Constraint = Constraint(m.SHUTDOWN_COST_GENERATORS,
                                            m.TIMEPOINTS,
                                            rule=shutdown_cost_rule)

    # Add to objective function
    def total_startup_cost_rule(mod):
        """
        Sum startup costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Startup_Cost[g, tmp]
                   for g in mod.STARTUP_COST_GENERATORS
                   for tmp in mod.TIMEPOINTS)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)
    m.total_cost_components.append("Total_Startup_Cost")

    # Add to objective function
    def total_shutdown_cost_rule(mod):
        """
        Sum shutdown costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Shutdown_Cost[g, tmp]
                   for g in mod.SHUTDOWN_COST_GENERATORS
                   for tmp in mod.TIMEPOINTS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)
    m.total_cost_components.append("Total_Shutdown_Cost")
