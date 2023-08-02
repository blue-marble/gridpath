# Copyright 2016-2023 Blue Marble Analytics LLC.
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

from pyomo.environ import Var, NonNegativeReals, Constraint

from gridpath.auxiliary.dynamic_components import (
    carbon_credits_balance_generation_components,
    carbon_credits_balance_purchase_components,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Available_Carbon_Credits = Var(
        m.CARBON_CREDITS_ZONES, m.PERIODS, within=NonNegativeReals, initialize=0
    )

    def total_credits_generated_rule(mod):
        return sum(
            getattr(mod, c)
            for c in getattr(d, carbon_credits_balance_generation_components)
        )

    m.Total_Carbon_Credits_Generated = m.Expression(
        initialize=total_credits_generated_rule
    )

    # Aggregate all costs
    def total_credits_purchased_rule(mod):
        return sum(
            getattr(mod, c)
            for c in getattr(d, carbon_credits_balance_purchase_components)
        )

    m.Total_Carbon_Credits_Purchased = m.Expression(
        initialize=total_credits_purchased_rule
    )

    # TODO: make this a dynamic component with other modules adding to it
    def track_available_credits(mod, z, prd):
        return (
            mod.Available_Carbon_Credits[z, prd]
            <= mod.Total_Carbon_Credits_Generated[z, prd]
            - mod.Total_Carbon_Credits_Purchased[z, prd]
        )

    m.Track_Carbon_Credits_Constraint = Constraint(
        m.CARBON_CREDITS_ZONES, m.PERIODS, rule=track_available_credits
    )
