# Copyright 2021 (c) Crown Copyright, GC.
# Modifications Copyright 2016-2023 Blue Marble Analytics LLC.
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
Aggregate carbon credits from the project-period level to the carbon credit
zone - period level.
"""

from pyomo.environ import Expression, value

from gridpath.common_functions import create_results_df
from gridpath.auxiliary.dynamic_components import (
    carbon_credits_balance_generation_components,
)
from gridpath.system.policy.carbon_credits import CARBON_CREDITS_ZONE_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    def total_carbon_credits_rule(mod, z, prd):
        """
        Calculate total emissions from all carbon tax projects in carbon
        tax zone
        :param mod:
        :param z:
        :param prd:
        :return:
        """
        return sum(
            mod.Project_Carbon_Credits_Generated[prj, prd]
            for (prj, period) in mod.CARBON_CREDITS_PRJ_OPR_PRDS
            if prj in mod.CARBON_CREDITS_PRJS_BY_CARBON_CREDITS_ZONE[z]
            and prd == period
        )

    m.Total_Project_Carbon_Credits_Generated = Expression(
        m.CARBON_CREDITS_ZONES, m.PERIODS, rule=total_carbon_credits_rule
    )

    # Add to the carbon credits tracking balance
    record_dynamic_components(d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds the static load to the load balance dynamic components.
    """
    getattr(dynamic_components, carbon_credits_balance_generation_components).append(
        "Total_Project_Carbon_Credits_Generated"
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
        "project_generated_credits",
    ]
    data = [
        [
            z,
            p,
            value(m.Total_Carbon_Credits_Generated[z, p]),
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
