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
This module aggregates all subsidies and subtracts them from the objective function.
"""

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import cost_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we sum up all subsidies, take the negative of that, and add the resulting
    expression to the objective-function dynamic components.
    """
    # Add costs to objective function
    def total_subsidy_rule(mod):
        return -sum(
            mod.Project_Annual_Payment_Reduction_from_Base[g, p]
            * mod.discount_factor[p]
            * mod.number_years_represented[p]
            for (g, p) in mod.PRJ_FIN_PRDS
        )

    m.Total_Subsidies = Expression(rule=total_subsidy_rule)

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    Add subsidy expression (it's a non-positive number) to cost components
    """

    getattr(dynamic_components, cost_components).append("Total_Subsidies")
