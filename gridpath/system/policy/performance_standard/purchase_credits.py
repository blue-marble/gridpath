# Copyright 2016-2023 Blue Marble Analytics LLC
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

"""

from pyomo.environ import Set, Var, Expression

from gridpath.auxiliary.dynamic_components import (
    performance_standard_balance_credit_components,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """ """
    m.PERFORMANCE_STANDARD_ZONES_CARBON_CREDITS_ZONES = Set(
        within=m.PERFORMANCE_STANDARD_ZONES * m.CARBON_CREDITS_ZONES
    )

    m.Performance_Standard_Purchase_Credits = Var(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD
    )

    def aggregate_purchases(mod, z, prd):
        return sum(
            mod.Performance_Standard_Purchase_Credits[z, prd]
            for (
                perf_zone,
                credit_zone,
            ) in mod.PERFORMANCE_STANDARD_ZONES_CARBON_CREDITS_ZONES
            if z == perf_zone
        )

    m.Performance_Standard_Total_Credit_Purchases = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        initialize=aggregate_purchases,
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds project emissions to carbon balance
    """

    getattr(dynamic_components, performance_standard_balance_credit_components).append(
        "Performance_Standard_Total_Credit_Purchases"
    )
