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
Constraint total slice-of-day contribution to be more than or equal to the
target for each zone, period, month, and hour.
"""

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from gridpath.auxiliary.dynamic_components import slice_of_day_balance_provision_components
from gridpath.common_functions import (
    create_results_df,
    duals_wrapper,
    none_dual_type_error_wrapper,
)
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

    m.Total_Slice_of_Day_from_All_Sources_Expression = Expression(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS,
        rule=lambda mod, z, p, mn, hr: sum(
            getattr(mod, component)[z, p, mn, hr]
            for component in getattr(d, slice_of_day_balance_provision_components)
        ),
    )

    m.Slice_of_Day_Shortage_MW = Var(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p, mn, hr):
        if mod.slice_of_day_allow_violation[z]:
            return mod.Slice_of_Day_Shortage_MW[z, p, mn, hr]
        else:
            return 0

    m.Slice_of_Day_Shortage_MW_Expression = Expression(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS, rule=violation_expression_rule
    )

    def slice_of_day_requirement_rule(mod, z, p, mn, hr):
        """
        Total slice-of-day provision must be greater than or equal to the target.
        :param mod:
        :param z:
        :param p:
        :param mn:
        :param hr:
        :return:
        """
        return (
            mod.Total_Slice_of_Day_from_All_Sources_Expression[z, p, mn, hr]
            + mod.Slice_of_Day_Shortage_MW_Expression[z, p, mn, hr]
            >= mod.slice_of_day_target_mw[z, p, mn, hr]
        )

    m.Slice_of_Day_Constraint = Constraint(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS, rule=slice_of_day_requirement_rule
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
        "slice_of_day_shortage_mw",
        "dual",
        "slice_of_day_marginal_cost_per_mw",
    ]
    data = [
        [
            z,
            p,
            mn,
            hr,
            value(m.Slice_of_Day_Shortage_MW_Expression[z, p, mn, hr]),
            (
                duals_wrapper(
                    m, getattr(m, "Slice_of_Day_Constraint")[z, p, mn, hr]
                )
                if (z, p, mn, hr)
                in [idx for idx in getattr(m, "Slice_of_Day_Constraint")]
                else None
            ),
            (
                none_dual_type_error_wrapper(
                    duals_wrapper(
                        m, getattr(m, "Slice_of_Day_Constraint")[z, p, mn, hr]
                    ),
                    m.period_objective_coefficient[p],
                )
                if (z, p, mn, hr)
                in [idx for idx in getattr(m, "Slice_of_Day_Constraint")]
                else None
            ),
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


def save_duals(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    instance,
    dynamic_components,
):
    instance.constraint_indices["Slice_of_Day_Constraint"] = [
        "slice_of_day_zone",
        "period",
        "sod_month",
        "sod_hour",
        "dual",
    ]
