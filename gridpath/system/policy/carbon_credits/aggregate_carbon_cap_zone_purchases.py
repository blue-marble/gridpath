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

from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import (
    carbon_credits_balance_purchase_components,
)
from gridpath.common_functions import create_results_df
from gridpath.system.policy.carbon_credits import CARBON_CREDITS_ZONE_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """ """

    def aggregate_purchases(mod, z, prd):
        return sum(
            mod.Carbon_Cap_Purchase_Credits[cap_zone, prd]
            for (cap_zone, credit_zone) in mod.CARBON_CAP_ZONES_CARBON_CREDITS_ZONES
            if z == credit_zone
            and (cap_zone, prd) in mod.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP
        )

    m.Total_Credit_Purchases_from_Carbon_Cap_Zones = Expression(
        m.CARBON_CREDITS_ZONES, m.PERIODS, initialize=aggregate_purchases
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds project emissions to carbon balance
    """

    getattr(dynamic_components, carbon_credits_balance_purchase_components).append(
        "Total_Credit_Purchases_from_Carbon_Cap_Zones"
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    results_columns = [
        "carbon_cap_zone_purchases",
    ]
    data = [
        [
            z,
            p,
            value(m.Total_Credit_Purchases_from_Carbon_Cap_Zones[z, p]),
        ]
        for z in m.CARBON_CREDITS_ZONES
        for p in m.PERIODS
    ]
    results_df = create_results_df(
        index_columns=["carbon_credits_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, CARBON_CREDITS_ZONE_PRD_DF)[c] = None
    getattr(d, CARBON_CREDITS_ZONE_PRD_DF).update(results_df)
