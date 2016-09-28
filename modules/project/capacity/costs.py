#!/usr/bin/env python

"""
Describe capacity costs.
"""
from pyomo.environ import Var, Expression, Constraint, NonNegativeReals

from modules.auxiliary.auxiliary import load_gen_storage_capacity_type_modules


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

    # Import needed capacity type modules
    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(d.required_capacity_modules)

    def capacity_cost_rule(mod, g, p):
        """
        Get capacity cost for each generator's respective capacity module
        :param mod:
        :param g:
        :param p:
        :return:
        """
        gen_cap_type = mod.capacity_type[g]
        return imported_capacity_modules[gen_cap_type].\
            capacity_cost_rule(mod, g, p)
    m.Capacity_Cost_in_Period = \
        Expression(m.PROJECT_OPERATIONAL_PERIODS,
                   rule=capacity_cost_rule)

    # Add costs to objective function
    def total_capacity_cost_rule(mod):
        return sum(mod.Capacity_Cost_in_Period[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.PROJECT_OPERATIONAL_PERIODS)
    m.Total_Capacity_Costs = Expression(rule=total_capacity_cost_rule)
    d.total_cost_components.append("Total_Capacity_Costs")
