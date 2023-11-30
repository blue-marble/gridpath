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
This module, aggregates the power production by all operational projects
to create a load-balance production component, and adds it to the
load-balance constraint.
"""

from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import load_balance_production_components
from gridpath.common_functions import create_results_df
from gridpath.system.load_balance import LOAD_ZONE_TMP_DF


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
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we add the *Power_Production_in_Zone_MW* expression -- an
    aggregation of power production by all operational projects in each load
    zone *z* and timepoint *tmp* --and add it to the dynamic load-balance
    production components that will go into the load balance constraint in
    the *load_balance* module (i.e. the constraint's lhs).

    :math:`Power\_Production\_in\_Zone\_MW_{z, tmp} =
    \sum_{r^z\in OR_{tmp}}{Power\_Provision\_MW_{r, tmp}}`
    """

    # Add power generation to load balance constraint
    # TODO: is this better done with a set intersection (all projects in the
    #  zone intersected with all operational project sin the timepoint)
    def total_power_production_rule(mod, z, tmp):
        return sum(
            mod.Power_Provision_MW[g, tmp]
            for g in mod.OPR_PRJS_IN_TMP[tmp]
            if mod.load_zone[g] == z
        )

    m.Power_Production_in_Zone_MW = Expression(
        m.LOAD_ZONES, m.TMPS, rule=total_power_production_rule
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:
    :return:

    """
    getattr(dynamic_components, load_balance_production_components).append(
        "Power_Production_in_Zone_MW"
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
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "total_power_mw",
    ]
    data = [
        [
            lz,
            tmp,
            value(m.Power_Production_in_Zone_MW[lz, tmp]),
        ]
        for lz in getattr(m, "LOAD_ZONES")
        for tmp in getattr(m, "TMPS")
    ]
    results_df = create_results_df(
        index_columns=["load_zone", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, LOAD_ZONE_TMP_DF)[c] = None
    getattr(d, LOAD_ZONE_TMP_DF).update(results_df)
