#!/usr/bin/env python
# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module adds load-balance penalty costs to the objective function.

.. note:: Unserved_Energy_MW, unserved_energy_penalty_per_mw,
    Overgeneration_MW, and overgeneration_penalty_per_mw are declared in
    system/load_balance/load_balance.py
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
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

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add total load balance penalty costs to cost components
    """

    getattr(dynamic_components, cost_components).append(
        "Total_Load_Balance_Penalty_Costs"
    )
