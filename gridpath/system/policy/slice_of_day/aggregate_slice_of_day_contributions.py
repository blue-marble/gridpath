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

"""
Aggregate slice-of-day contribution from the project level to the
slice-of-day zone level for each period, month, and hour.
"""

from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import (
    slice_of_day_balance_provision_components,
)
from gridpath.common_functions import create_results_df
from gridpath.system.policy.slice_of_day import SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :return:
    """

    def total_slice_of_day_contribution_rule(mod, z, p, mn, hr):
        return sum(
            mod.Slice_of_Day_Contribution_MW[g, z, p, mn, hr]
            for g in mod.SLICE_OF_DAY_PRJS_BY_ZONE[z]
            if (g, z, p, mn, hr) in mod.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
            and (g, p) in mod.PRJ_OPR_PRDS
        )

    m.Total_Slice_of_Day_Contribution_MW = Expression(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS,
        rule=total_slice_of_day_contribution_rule,
    )

    # Add to balance constraint
    getattr(d, slice_of_day_balance_provision_components).append(
        "Total_Slice_of_Day_Contribution_MW"
    )


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "total_slice_of_day_contribution_mw",
    ]
    data = [
        [
            z,
            p,
            mn,
            hr,
            value(m.Total_Slice_of_Day_Contribution_MW[z, p, mn, hr]),
        ]
        for (z, p, mn, hr) in m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
    ]
    results_df = create_results_df(
        index_columns=["slice_of_day_zone", "period", "sod_month", "sod_hour"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF)[c] = None
    getattr(d, SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF).update(results_df)
