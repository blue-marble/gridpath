# Copyright 2022 (c) Crown Copyright, GC.
# Modifications Copyright 2016-2023 Blue Marble Analytics.
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
Constrain total carbon emissions to be less than performance standard
"""

from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from gridpath.auxiliary.dynamic_components import (
    performance_standard_balance_emission_components,
    performance_standard_balance_credit_components,
)
from gridpath.common_functions import create_results_df
from gridpath.system.policy.performance_standard import PERFORMANCE_STANDARD_Z_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Performance_Standard_Overage = Var(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        within=NonNegativeReals,
    )

    def violation_expression_rule(mod, z, p):
        return (
            mod.Performance_Standard_Overage[z, p]
            * mod.performance_standard_allow_violation[z]
        )

    m.Performance_Standard_Overage_Expression = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        rule=violation_expression_rule,
    )

    m.Total_Performance_Standard_Emissions_from_All_Sources_Expression = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        rule=lambda mod, z, p: sum(
            getattr(mod, component)[z, p]
            for component in getattr(
                d, performance_standard_balance_emission_components
            )
        ),
    )

    m.Total_Performance_Standard_Credits_from_All_Sources_Expression = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        rule=lambda mod, z, p: sum(
            getattr(mod, component)[z, p]
            for component in getattr(d, performance_standard_balance_credit_components)
        ),
    )

    def performance_standard_rule(mod, z, p):
        """
        Total carbon emitted must be less than performance standard
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return (
            mod.Total_Performance_Standard_Emissions_from_All_Sources_Expression[z, p]
            - mod.Performance_Standard_Overage_Expression[z, p]
            <= (
                mod.Total_Performance_Standard_Project_Energy[z, p]
                * mod.performance_standard[z, p]
            )
            + mod.Total_Performance_Standard_Credits_from_All_Sources_Expression[z, p]
        )

    m.Performance_Standard_Constraint = Constraint(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        rule=performance_standard_rule,
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
        "performance_standard_overage_tco2",
    ]
    data = [
        [
            z,
            p,
            value(m.Performance_Standard_Overage_Expression[z, p]),
        ]
        for (z, p) in m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD
    ]
    results_df = create_results_df(
        index_columns=["performance_standard_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, PERFORMANCE_STANDARD_Z_PRD_DF)[c] = None
    getattr(d, PERFORMANCE_STANDARD_Z_PRD_DF).update(results_df)


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    instance.constraint_indices["Performance_Standard_Constraint"] = [
        "performance_standard_zone",
        "period",
        "dual",
    ]
