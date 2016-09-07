#!/usr/bin/env python

"""
Describe operational costs.
"""
from pyomo.environ import Var, Expression, Constraint, NonNegativeReals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    def new_build_capacity_cost_rule(mod, g, p):
        """
        Power production cost for each generator.
        :param mod:
        :return:
        """
        return sum(mod.Build_MW[g, v]
                   * mod.annualized_real_cost_per_mw_yr[g, v]
                   for (gen, v)
                   in mod.NEW_BUILD_OPTION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Option_Capacity_Cost_in_Period = \
        Expression(m.NEW_BUILD_OPTION_OPERATIONAL_PERIODS,
                   rule=new_build_capacity_cost_rule)

    def new_build_capacity_costs_rule(mod):
        return sum(mod.New_Build_Option_Capacity_Cost_in_Period[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.NEW_BUILD_OPTION_OPERATIONAL_PERIODS)
    m.New_Capacity_Costs = Expression(rule=new_build_capacity_costs_rule)
    d.total_cost_components.append("New_Capacity_Costs")
