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

from pyomo.environ import Expression

from gridpath.auxiliary.dynamic_components import (
    carbon_credits_balance_purchase_components,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """ """

    def aggregate_purchases(mod, z, prd):
        return sum(
            mod.Performance_Standard_Purchase_Credits[perf_zone, prd]
            for (
                perf_zone,
                credit_zone,
            ) in mod.PERFORMANCE_STANDARD_ZONES_CARBON_CREDITS_ZONES
            if z == credit_zone
            and (perf_zone, prd)
            in mod.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD
        )

    m.Total_Credit_Purchases_from_Performance_Standard_Zones = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        initialize=aggregate_purchases,
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds project emissions to carbon balance
    """

    getattr(dynamic_components, carbon_credits_balance_purchase_components).append(
        "Total_Credit_Purchases_from_Performance_Standard_Zones"
    )
