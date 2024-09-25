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

    m.WATER_LINKS = Set()
    m.water_node_from = Param(m.WATER_LINKS, within=Any)
    m.water_node_to = Param(m.WATER_LINKS, within=Any)

    m.WATER_NODES = Set(
        initialize=lambda mod: list(
            sorted(
                set(
                    [mod.water_node_from[wl] for wl in mod.WATER_LINKS]
                    + [mod.water_node_to[wl] for wl in mod.WATER_LINKS]
                )
            )
        )
    )

    # m.water_node_reservoir_capacity = Param(m.WATER_NODES)
    #
    # # Is this a function of flow
    # m.water_link_flow_transport_time = Param(m.WATER_LINKS, default=0)
    #
    # m.water_link_maximum_level_violation_penalty = Param(
    #     m.WATER_NODES, within=NonNegativeReals
    # )
    # m.water_link_maximum_level_violation_penalty = Param(
    #     m.WATER_NODES, within=NonNegativeReals
    # )
    #
    # # KSFD: A volume of water equal to 1,000 cubic feet of water flowing past a point for an entire day
    # # TODO: move these params to system-level modules when in place
    # # Will this be hourly or daily?
    # m.water_node_exog_inflow = Param(m.WATER_NODES, m.TIMEPOINTS)
    # # by month?
    # m.evaporation_coefficient = Param(m.WATER_NODES, m.MONTHS)
    #
    # # Elevation bounds
    # # Max varies by season
    # m.water_node_maximum_elevation = Param(m.WATER_NODES, m.TIMEPOINTS)
    # # In CHEOPS, min elevation is a single value for each reservoir and does
    # # not vary over time
    # m.water_node_minimum_elevation = Param(m.WATER_NODES, m.TIMEPOINTS)
    #
    # # Spill bound
    # # Max spill is a function of elevation, so this may be an expression
    # # This will constraint the Spill variable
    # m.max_spill = Param(m.WATER_NODES, m.TIMEPOINTS)
    #
    # # TODO: convert from whatever base unit we choose to timepoint
    # m.water_link_min_bypass_flow_vol_per_tmp = Param(m.WATER_LINKS, m.TIMEPOINTS)
    # m.water_link_min_powerhouse_flow_vol_per_tmp = Param(m.WATER_LINKS, m.TIMEPOINTS)
    # m.water_link_min_total_flow_vol_per_tmp = Param(m.WATER_LINKS, m.TIMEPOINTS)
    #
    # # Start with these as params BUT:
    # # These are probably not params but expressions with a non-linear
    # # relationship to elevation; most of the curves look they can be
    # # piecewise linear
    # # With tailwater curves, flow depends on elevation; or does max flow
    # # depend on elevation?
    # m.water_link_max_flow_vol_per_tmp = Param(m.WATER_LINKS, m.TIMEPOINTS)
    #
    # # Hydro system variables and constraints; need to figure out where this
    # # module will be
    # # Note elevation has a quadratic relationship to volume in Verene's
    # # spreadsheet
    # m.Reservoir_Elevation = Var(
    #     Var(m.WATER_NODES, m.TIMEPOINTS, within=NonNegativeReals)
    # )
    # m.Reservoir_Volume = Expression(
    #     m.WATER_NODES, m.TIMEPOINTS, within=NonNegativeReals
    # )
    # # Is a separate variable needed for spill vs valve release?
    # m.Release_Water = Var(m.WATER_NODES, m.TIMEPOINTS, within=NonNegativeReals)
    #
    # # Flows on some links may be able/required to bypass the powerhouse
    # m.NonPowerhouse_Water_Flow = Var(
    #     m.WATER_LINKS, m.TIMEPOINTS, within=NonNegativeReals
    # )
    # m.Powerhouse_Water_Flow = Var(m.WATER_LINKS, m.TIMEPOINTS, within=NonNegativeReals)
    #
    # m.Total_Water_Flow = Expression(
    #     m.WATER_LINKS,
    #     m.TIMEPOINTS,
    #     within=NonNegativeReals,
    #     rule=lambda mod, wl, tmp: mod.NonPowerhouse_Water_Flow[wl, tmp]
    #     + mod.Powerhouse_Water_Flow[wl, tmp],
    # )
    #
    # # TODO: add total and bypass limits for each link; be careful to set
    # #  bypass flows to 0 where there's no bypass
    # def min_water_flow_on_link(mod, l, tmp):
    #     return (
    #         mod.Powerhouse_Water_Flow(l, tmp)
    #         >= mod.water_link_min_powerhouse_flow_vol_per_tmp[l, tmp]
    #     )
    #
    # def conservation_of_water_mass_constraint(mod, r, tmp):
    #     pass
    #
    # # TODO: move to operational type
    # # This is unit dependent; different if we are using MW, kg/s (l/s) vs cfs,
    # # m vs ft; user must ensure consistent units
    # m.theoretical_power_coefficient = Param()
    #
    # # Hydro system generator operational type
    # m.water_link = Param(m.GEN_HYDRO_WATER_SYSTEM_PRJS, within=m.WATER_LINKS)
    #
    # # This can actually depend on flow
    # m.tailwater_elevation = Param(m.GEN_HYDRO_WATER_SYSTEM_PRJS)
    #
    # # Depends on flow
    # m.headloss_coefficient = Param(m.GEN_HYDRO_WATER_SYSTEM_PRJS)
    #
    # # TODO: turbine efficiency is a function of water flow through the turbine
    # m.turbine_efficiency = Param(m.GEN_HYDRO_WATER_SYSTEM_PRJS)
    #
    # # TODO: generator efficiency; a function of power output
    # m.generator_efficiency = Param(m.GEN_HYDRO_WATER_SYSTEM_PRJS)
    #
    # #
    # m.Gross_Head = Expression(
    #     m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS,
    #     within=NonNegativeReals,
    #     rule=lambda mod, g, tmp: mod.Reservoir_Elevation[
    #         mod.water_node_from[mod.water_link[g]]
    #     ]
    #     - mod.tailwater_elevation[g],
    # )
    #
    # #
    # m.Net_Head = Expression(
    #     m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS,
    #     within=NonNegativeReals,
    #     rule=lambda mod, g, tmp: mod.Gross_Head[g, tmp]
    #     * (1 - mod.headloss_coefficient[g]),
    # )
    #
    # m.GenHydroWaterSystem_Power_MW = Var(
    #     m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS, within=NonNegativeReals
    # )
    #
    # def water_to_power_rule(mod, g, tmp):
    #     """
    #     Start with simple linear relationship; this actually will depend on
    #     volume
    #     """
    #     return (
    #         mod.GenHydroWaterSystem_Power_MW[g, tmp]
    #         == mod.theoretical_power_coefficient
    #         * mod.Water_Flow[mod.water_link[g], tmp]
    #         * mod.Net_Head[g, tmp]
    #         * mod.turbine_efficiency[g]
    #         * mod.generator_efficiency[g]
    #     )
    #
    # m.Water_to_Power_Constraint = Constraint(
    #     m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS, rule=water_to_power_rule
    # )


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "water_network.tab",
        ),
        index=m.WATER_LINKS,
        param=(m.water_node_from, m.water_node_to),
    )


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    water_links = c.execute(
        f"""SELECT water_link, water_node_from, water_node_to
        FROM inputs_geography_water_network
        WHERE water_network_scenario_id = {subscenarios.WATER_NETWORK_SCENARIO_ID};
        """
    )

    return water_links


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # carbon_cap_zone = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input
    water_network.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    carbon_cap_zone = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "water_network.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["water_link", "water_node_from", "water_node_to"])

        for row in carbon_cap_zone:
            writer.writerow(row)
