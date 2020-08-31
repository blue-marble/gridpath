#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module adds load-balance penalty costs to the objective function.

.. note:: Unserved_Energy_MW, unserved_energy_penalty_per_mw,
    Overgeneration_MW, and overgeneration_penalty_per_mw are declared in
    system/load_balance/load_balance.py
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    Add total load balance penalty costs to cost components
    :param d:
    :return:
    """

    getattr(d, total_cost_components).append(
        "Total_Load_Balance_Penalty_Costs"
    )


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    Here, we aggregate total unserved-energy and overgeneration costs,
    and add them as a dynamic component to the objective function.

    :math:`Total\_Load\_Balance\_Penalty\_Costs =
    \sum_{z, tmp} {(Unserved\_Energy\_MW\_Expression_{z, tmp} +
    Overgeneration\_MW\_Expression_{z,
    tmp})
    \\times number\_of\_hours\_in\_timepoint_{tmp}
    \\times horizon\_weight_{h^{tmp}}
    \\times number\_years\_represented_{p^{tmp}}
    \\times discount\_factor_{p^{tmp}}}`
    """

    def total_penalty_costs_rule(mod):
        return sum((mod.Unserved_Energy_MW_Expression[z, tmp]
                    * mod.unserved_energy_penalty_per_mw[z] +
                    mod.Overgeneration_MW_Expression[z, tmp]
                    * mod.overgeneration_penalty_per_mw[z])
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for z in mod.LOAD_ZONES for tmp in mod.TMPS)
    m.Total_Load_Balance_Penalty_Costs = Expression(
        rule=total_penalty_costs_rule)
