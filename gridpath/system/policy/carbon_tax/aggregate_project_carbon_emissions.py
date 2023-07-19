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
Aggregate carbon emissions from the project-timepoint level to
the carbon tax zone - period level.
"""


import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.common_functions import create_results_df
from gridpath.system.policy.carbon_tax import CARBON_TAX_ZONE_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    def total_carbon_emissions_rule(mod, z, p):
        """
        Calculate total emissions from all carbon tax projects in carbon
        tax zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Project_Carbon_Emissions[g, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (g, tmp) in mod.CARBON_TAX_PRJ_OPR_TMPS
            if g in mod.CARBON_TAX_PRJS_BY_CARBON_TAX_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Carbon_Tax_Project_Emissions = Expression(
        m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX, rule=total_carbon_emissions_rule
    )

    def total_carbon_tax_allowance_rule(mod, z, p):
        """
        Calculate total emission allowance from all carbon tax projects in carbon
        tax zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Project_Carbon_Tax_Allowance[g, fg, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (g, fg, tmp) in mod.CARBON_TAX_PRJ_FUEL_GROUP_OPR_TMPS
            if g in mod.CARBON_TAX_PRJS_BY_CARBON_TAX_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Carbon_Tax_Project_Allowance = Expression(
        m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX, rule=total_carbon_tax_allowance_rule
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
        "project_emissions",
    ]
    data = [
        [
            z,
            p,
            value(m.Total_Carbon_Tax_Project_Emissions[z, p]),
        ]
        for (z, p) in m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX
    ]
    results_df = create_results_df(
        index_columns=["carbon_tax_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, CARBON_TAX_ZONE_PRD_DF)[c] = None
    getattr(d, CARBON_TAX_ZONE_PRD_DF).update(results_df)
