#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates all project operational costs and adds them to the
objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param di: the DynamicComponents class object we are adding components to

    Here, we sum up all operational costs. Operational costs include
    variable O&M costs, fuel costs, startup costs, and shutdown costs.

    :math:`Total\_Variable\_OM\_Cost =
    \sum_{(r, tmp)\in {RT}}{Variable\_OM\_Cost_{r, tmp}
    \\times number\_of\_hours\_in\_timepoint_{tmp}
    \\times horizon\_weight_{h^{tmp}}
    \\times number\_years\_represented_{p^{tmp}}
    \\times discount\_factor_{p^{tmp}}}`

    :math:`Total\_Fuel\_Cost =
    \sum_{(r, tmp)\in {RT}}{Fuel\_Cost_{r, tmp}
    \\times number\_of\_hours\_in\_timepoint_{tmp}
    \\times horizon\_weight_{h^{tmp}}
    \\times number\_years\_represented_{p^{tmp}}
    \\times discount\_factor_{p^{tmp}}}`

    """

    # Power production variable costs
    def total_variable_om_cost_rule(mod):
        """
        Power production cost for all generators across all timepoints
        :param mod:
        :return:
        """
        return sum(mod.Variable_OM_Cost[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.VAR_OM_COST_ALL_PRJS_OPR_TMPS)

    m.Total_Variable_OM_Cost = Expression(rule=total_variable_om_cost_rule)

    # Fuel cost
    def total_fuel_cost_rule(mod):
        """
        Fuel costs for all generators across all timepoints
        :param mod:
        :return:
        """
        return sum(mod.Fuel_Cost[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.FUEL_PRJ_OPR_TMPS)

    m.Total_Fuel_Cost = Expression(rule=total_fuel_cost_rule)

    # Startup and shutdown costs
    def total_startup_cost_rule(mod):
        """
        Sum startup costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Startup_Cost[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.STARTUP_COST_PRJ_OPR_TMPS)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)

    def total_shutdown_cost_rule(mod):
        """
        Sum shutdown costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Shutdown_Cost[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.SHUTDOWN_COST_PRJ_OPR_TMPS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)

    def total_operational_violation_cost_rule(mod):
        """
        Sum operational constraint violation costs for the objective function
        term.
        """
        return sum(mod.Operational_Violation_Cost[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.VIOL_ALL_PRJ_OPR_TMPS)
    m.Total_Operational_Violation_Cost = Expression(
        rule=total_operational_violation_cost_rule
    )

    def total_curtailment_cost_rule(mod):
        """
        Sum curtailment costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Curtailment_Cost[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.CURTAILMENT_COST_PRJ_OPR_TMPS)
    m.Total_Curtailment_Cost = Expression(rule=total_curtailment_cost_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add operational costs to the objective-function dynamic components.
    """

    getattr(dynamic_components, total_cost_components).append(
        "Total_Variable_OM_Cost")
    getattr(dynamic_components, total_cost_components).append(
        "Total_Fuel_Cost")
    getattr(dynamic_components, total_cost_components).append(
        "Total_Startup_Cost")
    getattr(dynamic_components, total_cost_components).append(
        "Total_Shutdown_Cost")
    getattr(dynamic_components, total_cost_components).append(
        "Total_Operational_Violation_Cost"
    )
    getattr(dynamic_components, total_cost_components).append(
        "Total_Curtailment_Cost"
    )
