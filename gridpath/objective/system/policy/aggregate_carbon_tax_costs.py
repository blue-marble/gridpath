"""
This module aggregates carbon tax costs for use in the objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    Here, we sum up all carbon tax costs.
    """

    def total_carbon_tax_cost_rule(mod):
        return sum(mod.Carbon_Tax_Cost[z, p]
                   * mod.number_years_represented[p]
                   * mod.discount_factor[p]
                   for (z, p) in mod.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX)

    m.Total_Carbon_Tax_Cost = Expression(rule=total_carbon_tax_cost_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total carbon tax costs to cost components

    """

    getattr(dynamic_components, cost_components).append(
        "Total_Carbon_Tax_Cost"
    )
