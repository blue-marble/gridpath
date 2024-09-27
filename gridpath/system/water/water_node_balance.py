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

"""
Water nodes and connections for modeling cascading hydro systems.
"""

import csv
import os.path
from pyomo.environ import (
    Set,
    Param,
    Boolean,
    NonNegativeReals,
    Var,
    Constraint,
    Expression,
    Any,
)

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_boundary_type,
)


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

    m.exogenous_water_node_inflow = Param(
        m.WATER_NODES, m.TIMEPOINTS, default=0, within=NonNegativeReals
    )

    def water_links_to_by_water_node_rule(mod):
        init_dict = {}
        for wn in m.WATER_NODES:
            init_dict = {wn: []}
            for wl in mod.WATER_LINKS:
                if mod.water_node_to[wl] == wn:
                    init_dict[wn].append(wl)

        return init_dict

    def water_links_from_by_water_node_rule(mod):
        init_dict = {}
        for wn in m.WATER_NODES:
            init_dict = {wn: []}
            for wl in mod.WATER_LINKS:
                if mod.water_node_from[wl] == wn:
                    init_dict[wn].append(wl)

        return init_dict

    m.WATER_LINKS_TO_BY_WATER_NODE = Set(
        m.WATER_NODES, initialize=water_links_to_by_water_node_rule
    )

    m.WATER_LINKS_FROM_BY_WATER_NODE = Set(
        m.WATER_NODES, initialize=water_links_from_by_water_node_rule
    )

    # exog inflow + var inflow - res_store_water - evap losses + res discharge
    # = water outflow

    # TODO: units with different timepoint durations
    # TODO: add time delays
    def water_node_mass_balance_rule(mod, wn, tmp):
        # TODO: sum over all reservoirs at a node
        res = "temp"
        return (
            mod.exogenous_water_node_inflow[wn, tmp]
            + sum(
                mod.Waterway_Flow_in_Tmp[wl, tmp]
                for wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn]
            )
            + sum(
                mod.Net_Reservoir_Outflow[res, tmp]
                for res in mod.RESERVOIRS_BY_NODE[wn]
            )
        ) == sum(
            mod.Waterway_Flow_in_Tmp[wl, tmp]
            for wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]
        )

    m.Water_Node_Mass_Balance_Constraint = Constraint(
        m.WATER_NODES, m.TMPS, rule=water_node_mass_balance_rule
    )
