#!/usr/bin/env python

from pyomo.environ import *


def add_model_components(m):

    m.Power = Var(m.GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)

    def max_power_rule(m, g, t):
        return m.Power[g, t] <= m.capacity[g]

    m.Max_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS, rule=max_power_rule)

    # TODO: make this generators in the zone only when multiple zones actually are implemented
    def generation_power_rule(m, z, tmp):
        return sum(m.Power[g, tmp] for g in m.GENERATORS)
    m.Generation_Power = Expression(m.LOAD_ZONES, m.TIMEPOINTS, rule=generation_power_rule)

    m.energy_generation_components.append("Generation_Power")


    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def generation_cost_rule(m):
        """
        Power production cost for all generators across all timepoints
        :param m:
        :return:
        """
        return sum(m.Power[g, tmp] * m.variable_cost[g] for g in m.GENERATORS for tmp in m.TIMEPOINTS)

    m.Total_Generation_Cost = Expression(rule=generation_cost_rule)

    m.total_cost_components.append("Total_Generation_Cost")
