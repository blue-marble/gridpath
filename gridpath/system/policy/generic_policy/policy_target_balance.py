# Copyright 2016-2024 Blue Marble Analytics LLC.
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

""" """

from pyomo.environ import Var, Constraint, NonNegativeReals, Expression, value

from gridpath.common_functions import (
    create_results_df,
    duals_wrapper,
    none_dual_type_error_wrapper,
)
from gridpath.system.policy.generic_policy import POLICY_ZONE_PRD_DF


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

    m.Policy_Target_Shortage = Var(
        m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ, within=NonNegativeReals, initialize=0
    )

    def violation_expression_init(mod, policy, zone, bt, h):
        if mod.policy_zone_allow_violation[policy, zone]:
            return mod.Policy_Target_Shortage[policy, zone, bt, h]
        else:
            return 0

    m.Policy_Requirement_Shortage_Expression = Expression(
        m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ,
        initialize=violation_expression_init,
    )

    def meet_policy_target_constraint_rule(mod, policy, zone, bt, h):
        """
        Total delivered energy-target-eligible energy must exceed target
        :param mod:
        :param policy:
        :param zone:
        :param bt:
        :param h:
        :return:
        """
        return (
            mod.Total_Project_Policy_Zone_Tmp_Contributions[policy, zone, bt, h]
            + mod.Policy_Requirement_Shortage_Expression[policy, zone, bt, h]
            >= mod.Policy_Zone_Horizon_Requirement[policy, zone, bt, h]
        )

    m.Policy_Requirement_Constraint = Constraint(
        m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ, rule=meet_policy_target_constraint_rule
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
        "pre_load_modifier_load_in_hrz",
        "post_load_modifier_load_in_hrz",
        "policy_requirement_calculated_in_horizon",
        "policy_requirement_shortage",
        "dual",
        "policy_requirement_marginal_cost_per_unit",
    ]
    data = [
        [
            p,
            z,
            bt,
            h,
            sum(
                value(m.LZ_Bulk_Static_Load_in_Tmp[lz, tmp])
                * m.hrs_in_tmp[tmp]
                * m.tmp_weight[tmp]
                for (
                    _policy_name,
                    _policy_requirement_zone,
                    lz,
                ) in m.POLICIES_ZONE_LOAD_ZONES
                if (_policy_name, _policy_requirement_zone) == (p, z)
                for tmp in m.TMPS
                if tmp in m.TMPS_BY_BLN_TYPE_HRZ[bt, h]
            ),
            sum(
                value(m.LZ_Modified_Load_in_Tmp[lz, tmp])
                * m.hrs_in_tmp[tmp]
                * m.tmp_weight[tmp]
                for (
                    _policy_name,
                    _policy_requirement_zone,
                    lz,
                ) in m.POLICIES_ZONE_LOAD_ZONES
                if (_policy_name, _policy_requirement_zone) == (p, z)
                for tmp in m.TMPS
                if tmp in m.TMPS_BY_BLN_TYPE_HRZ[bt, h]
            ),
            value(m.Policy_Zone_Horizon_Requirement[p, z, bt, h]),
            value(m.Policy_Requirement_Shortage_Expression[p, z, bt, h]),
            (
                duals_wrapper(
                    m, getattr(m, "Policy_Requirement_Constraint")[p, z, bt, h]
                )
                if (p, z, bt, h)
                in [idx for idx in getattr(m, "Policy_Requirement_Constraint")]
                else None
            ),
            (
                none_dual_type_error_wrapper(
                    duals_wrapper(
                        m, getattr(m, "Policy_Requirement_Constraint")[p, z, bt, h]
                    ),
                    m.hrz_objective_coefficient[bt, h],
                )
                if (p, z, bt, h)
                in [idx for idx in getattr(m, "Policy_Requirement_Constraint")]
                else None
            ),
        ]
        for (p, z, bt, h) in m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ
    ]
    results_df = create_results_df(
        index_columns=["policy_name", "policy_zone", "balancing_type", "horizon"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, POLICY_ZONE_PRD_DF)[c] = None
    getattr(d, POLICY_ZONE_PRD_DF).update(results_df)


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
    instance.constraint_indices["Policy_Requirement_Constraint"] = [
        "policy_name",
        "policy_zone",
        "balancing_type",
        "horizon",
        "dual",
    ]
