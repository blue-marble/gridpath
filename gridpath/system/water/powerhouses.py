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
    value,
)

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import create_results_df
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

    m.powerhouse_water_node = Param(m.POWERHOUSES, within=m.WATER_NODES)

    # TODO: move this to projects
    # m.POWERHOUSE_GENERATORS = Set(dimen=2, within=m.POWERHOUSES * m.GEN_HYDRO_SYSTEM)

    # def generators_by_powerhouse_init(mod):
    #     init_dict = {}
    #     for p, g in mod.POWERHOUSE_GENERATORS:
    #         if p not in mod.POWERHOUSE_GENERATORS:
    #             init_dict[p] = [g]
    #         else:
    #             init_dict[p].append(g)
    #
    #     return init_dict
    #
    # m.GENERATORS_BY_POWERHOUSE = Set(
    #     m.POWERHOUSES,
    #     within=m.GEN_HYDRO_SYSTEM,
    #     initialize=generators_by_powerhouse_init,
    # )

    # TODO: move to a more central location?
    # This is unit dependent; different if we are using MW, kg/s (l/s) vs cfs,
    # m vs ft; user must ensure consistent units
    m.theoretical_power_coefficient = Param(m.POWERHOUSES, within=NonNegativeReals)

    # This can actually depend on flow
    m.tailwater_elevation = Param(m.POWERHOUSES, within=NonNegativeReals)

    # Depends on flow
    m.headloss_factor = Param(m.POWERHOUSES, within=NonNegativeReals)

    # TODO: turbine efficiency is a function of water flow through the turbine
    m.turbine_efficiency = Param(m.POWERHOUSES, within=NonNegativeReals)

    def gross_head_expression_init(mod, p, tmp):
        return (
            mod.Reservoir_Starting_Elevation_ElevationUnit[
                mod.powerhouse_water_node[p], tmp
            ]
            - mod.tailwater_elevation[p]
        )

    m.Gross_Head = Expression(
        m.POWERHOUSES,
        m.TMPS,
        rule=gross_head_expression_init,
    )

    def net_head_expression_init(mod, p, tmp):
        return mod.Gross_Head[p, tmp] * (1 - mod.headloss_factor[p])

    m.Net_Head = Expression(
        m.POWERHOUSES,
        m.TMPS,
        rule=net_head_expression_init,
    )

    # # Allocate water to generators within the powerhouse
    # m.Generator_Allocated_Water_Flow = Var(
    #     m.GEN_HYDRO_SYSTEM, m.TMPS, within=NonNegativeReals
    # )
    #
    # def generator_water_allocation_constraint_rule(mod, p, tmp):
    #     return (
    #         sum(
    #             mod.Generator_Allocated_Water_Flow[g, tmp]
    #             for g in mod.GENERATORS_BY_POWERHOUSE[p]
    #         )
    #         == mod.Discharge_Water_to_Powerhouse[mod.powerhouse_water_node[p], tmp]
    #     )
    #
    # m.Generator_Water_Allocation_Constraint = Constraint(
    #     m.POWERHOUSES, m.TMPS, rule=generator_water_allocation_constraint_rule
    # )
    #
    # m.GenHydroWaterSystem_Power_MW = Var(
    #     m.GEN_HYDRO_WATER_SYSTEM_OPR_TMPS, within=NonNegativeReals
    # )

    def water_to_power_init(mod, pwrh, tmp):
        """
        Start with simple linear relationship; this actually will depend on
        volume
        """
        return (
            mod.theoretical_power_coefficient[pwrh]
            * mod.Discharge_Water_to_Powerhouse[mod.powerhouse_water_node[pwrh], tmp]
            * mod.Net_Head[pwrh, tmp]
            * mod.turbine_efficiency[pwrh]
        )

    m.Powerhouse_Output_Single_Generator = Expression(
        m.POWERHOUSES, m.TMPS, initialize=water_to_power_init
    )


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
    fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "powerhouses.tab",
    )

    data_portal.load(
        filename=fname,
        index=m.POWERHOUSES,
        param=(
            m.powerhouse_water_node,
            m.theoretical_power_coefficient,
            m.tailwater_elevation,
            m.headloss_factor,
            m.turbine_efficiency,
        ),
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
    powerhouses = c.execute(
        f"""SELECT powerhouse, powerhouse_water_node, 
            theoretical_power_coefficient, tailwater_elevation, headloss_factor,
            turbine_efficiency
            FROM inputs_system_water_powerhouses
            WHERE water_powerhouse_scenario_id = 
            {subscenarios.WATER_POWERHOUSE_SCENARIO_ID}
            ;
            """
    )

    return powerhouses


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
    water_flow_bounds.tab file.
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

    powerhouses = get_inputs_from_database(
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
            "powerhouses.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "powerhouse",
                "powerhouse_water_node",
                "theoretical_power_coefficient",
                "tailwater_elevation",
                "headloss_factor",
                "turbine_efficiency",
            ]
        )

        for row in powerhouses:
            writer.writerow(row)


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
    # TODO: add results
    results_columns = [
        "reservoir",
        "gross_head",
        "net_head",
        "water_discharge_to_powerhouse",
    ]
    data = [
        [
            p,
            tmp,
            m.powerhouse_water_node[p],
            value(m.Gross_Head[p, tmp]),
            value(m.Net_Head[p, tmp]),
            value(m.Discharge_Water_to_Powerhouse[m.powerhouse_water_node[p], tmp]),
        ]
        for p in m.POWERHOUSES
        for tmp in m.TMPS
    ]
    results_df = create_results_df(
        index_columns=["powerhouse", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    results_df.to_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "powerhouse_timepoint.csv",
        ),
        sep=",",
        index=True,
    )


# TODO: results import
