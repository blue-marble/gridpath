#!/usr/bin/env python

from pyomo.environ import Expression, Objective, minimize


def add_model_components(m):
    """
    Aggregate costs and components to objective function.
    :param m:
    :return:
    """
    # Power production variable costs
    # TODO: fix this when periods added, etc.
    def total_generation_cost_rule(m):
        """
        Power production cost for all generators across all timepoints
        :param m:
        :return:
        """
        return sum(m.Generation_Cost[g, tmp]
                   for g in m.GENERATORS
                   for tmp in m.TIMEPOINTS)

    m.Total_Generation_Cost = Expression(rule=total_generation_cost_rule)
    m.total_cost_components.append("Total_Generation_Cost")

    # Startup and shutdown costs
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

    # Define objective function
    def total_cost_rule(m):

        return sum(getattr(m, c)
                   for c in m.total_cost_components)

    m.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)