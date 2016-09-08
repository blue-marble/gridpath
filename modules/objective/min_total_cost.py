#!/usr/bin/env python

from pyomo.environ import Expression, Objective, minimize


def add_model_components(m, d, scenario_directory, horizon, stage):
    """
    Aggregate costs and components to objective function.
    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    def penalty_costs_rule(mod):
        return sum((mod.Unserved_Energy_MW[z, tmp]
                    * mod.unserved_energy_penalty_per_mw +
                    mod.Overgeneration_MW[z, tmp]
                    * mod.overgeneration_penalty_per_mw)
                   * mod.discount_factor[mod.period[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   for z in mod.LOAD_ZONES for tmp in mod.TIMEPOINTS)
    m.Penalty_Costs = Expression(rule=penalty_costs_rule)
    d.total_cost_components.append("Penalty_Costs")

    # Define objective function
    def total_cost_rule(mod):

        return sum(getattr(mod, c)
                   for c in d.total_cost_components)

    m.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)