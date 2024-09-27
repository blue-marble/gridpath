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

    # ### Sets ### #

    m.POWERHOUSES = Set(within=Any)

    m.powerhouse_reservoir = Param(m.POWERHOUSES, within=m.RESERVOIRS)

    m.POWERHOUSE_GENERATORS = Set(dimen=2, within=m.POWERHOUSES * m.GEN_HYDRO_SYSTEM)

    def generators_by_powerhouse_init(mod):
        init_dict = {}
        for p, g in mod.POWERHOUSE_GENERATORS:
            if p not in mod.POWERHOUSE_GENERATORS:
                init_dict[p] = [g]
            else:
                init_dict[p].append(g)

        return init_dict

    m.GENERATORS_BY_POWERHOUSE = Set(
        m.POWERHOUSES,
        within=m.GEN_HYDRO_SYSTEM,
        initialize=generators_by_powerhouse_init,
    )

    # TODO: move to a more central location?
    # This is unit dependent; different if we are using MW, kg/s (l/s) vs cfs,
    # m vs ft; user must ensure consistent units
    m.theoretical_power_coefficient = Param()

    # This can actually depend on flow
    m.tailwater_elevation = Param(m.POWERHOUSES)

    # Depends on flow
    m.headloss_coefficient = Param(m.POWERHOUSES)

    # TODO: turbine efficiency is a function of water flow through the turbine
    m.turbine_efficiency = Param(m.POWERHOUSES)

    # TODO: generator efficiency; a function of power output
    # TODO: move to projects
    m.generator_efficiency = Param(m.POWERHOUSES)

    def gross_head_expression_init(mod, p, tmp):
        return (
            mod.Reservoir_Elevation[mod.powerhouse_reservoir[p], tmp]
            - mod.tailwater_elevation[p]
        )

    m.Gross_Head = Expression(
        m.POWERHOUSES,
        m.TIMEPOINTS,
        within=NonNegativeReals,
        rule=gross_head_expression_init,
    )

    def net_head_expression_init(mod, p, tmp):
        return mod.Gross_Head[p, tmp] * (1 - mod.headloss_coefficient[p])

    m.Net_Head = Expression(
        m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS,
        within=NonNegativeReals,
        rule=net_head_expression_init,
    )

    # Allocate water to generators within the powerhouse
    m.Generator_Allocated_Water_Flow = Var(
        m.GEN_HYDRO_SYSTEM, m.TMPS, within=NonNegativeReals
    )

    def generator_water_allocation_constraint_rule(mod, p, tmp):
        return (
            sum(
                mod.Generator_Allocated_Water_Flow[g, tmp]
                for g in mod.GENERATORS_BY_POWERHOUSE[p]
            )
            == mod.Discharge_Water_to_Powerhouse[mod.powerhouse_reservoir[p], tmp]
        )

    m.Generator_Water_Allocation_Constraint = Constraint(
        m.POWERHOUSES, m.TMPS, rule=generator_water_allocation_constraint_rule
    )

    m.GenHydroWaterSystem_Power_MW = Var(
        m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS, within=NonNegativeReals
    )

    def water_to_power_rule(mod, g, tmp):
        """
        Start with simple linear relationship; this actually will depend on
        volume
        """
        return (
            mod.GenHydroWaterSystem_Power_MW[g, tmp]
            == mod.theoretical_power_coefficient
            * mod.Generator_Allocated_Water_Flow[g, tmp]
            * mod.Net_Head[g, tmp]
            * mod.turbine_efficiency[g]
            * mod.generator_efficiency[g]
        )

    m.Water_to_Power_Constraint = Constraint(
        m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS, rule=water_to_power_rule
    )
