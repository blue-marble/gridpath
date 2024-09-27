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
    m.NODE_RESERVOIRS = Set(dimen=2)
    m.RESERVOIRS = Set(
        initialize=lambda mod: sorted(list(set(r for (n, r) in mod.NODE_RESERVOIRS)))
    )

    def reservoirs_by_node_rule(mod):
        init_dict = {}
        for n, r in mod.NODE_RESERVOIRS:
            if n not in init_dict.keys():
                init_dict[n] = [r]
            else:
                init_dict[n].append(r)

        return init_dict

    m.RESERVOIRS_BY_NODE = Set(m.NODES, initialize=reservoirs_by_node_rule)

    m.RESERVOIR_TMPS_W_TARGET_VOLUME = Set(within=m.RESERVOIRS * m.TMPS)

    # ### Constraints ### #

    # ### Parameters ###
    m.balancing_type_reservoir = Param(m.RESERVOIRS, within=m.BLN_TYPES)

    m.reservoir_target_volume = Param(
        m.RESERVOIR_TMPS_W_TARGET_VOLUME, within=NonNegativeReals
    )
    m.evaporation_coefficient = Param(
        m.RESERVOIRS, m.MONTHS, within=NonNegativeReals, default=0
    )

    # Elevation bounds
    # Max varies by season
    m.maximum_elevation_elevationunit = Param(
        m.RESERVOIRS, m.TIMEPOINTS, default=0, within=NonNegativeReals
    )
    # In CHEOPS, min elevation is a single value for each reservoir and does
    # not vary over time
    m.minimum_elevation = Param(m.RESERVOIRS, default=0, within=NonNegativeReals)

    # TODO: make this piecewise linear or a nonlinear function
    # Volume to elevation conversion
    m.volume_to_elevation_conversion_coefficient = Param(
        m.RESERVOIRS, within=NonNegativeReals, default=1
    )

    # Spill bound
    # TODO: make max spill a function of elevation
    m.max_spill = Param(m.RESERVOIRS, default=0, within=NonNegativeReals)

    # ### Variables ### #
    # TODO: elevation/volume relationship
    m.Reservoir_Starting_Elevation_ElevationUnit = Var(
        Var(m.RESERVOIRS, m.TIMEPOINTS, within=NonNegativeReals)
    )
    m.Reservoir_Starting_Volume_WaterVolumeUnit = Var(
        m.RESERVOIRS, m.TIMEPOINTS, within=NonNegativeReals
    )

    # Controls
    m.Store_Water = Var(m.RESERVOIRS, m.TIMEPOINTS, within=NonNegativeReals)
    m.Discharge_Water_to_Powerhouse = Var(
        m.RESERVOIRS, m.TIMEPOINTS, within=NonNegativeReals
    )
    m.Spill_Water = Var(m.RESERVOIRS, m.TIMEPOINTS, within=NonNegativeReals)

    # Losses
    m.Evaporative_Losses = Expression(m.RESERVOIRS, m.TIMEPOINTS)

    # ### Expressions ### #

    def gross_reservoir_outflow_rule(mod, r, tmp):
        return (
            mod.Discharge_Water_to_Powerhouse[r, tmp]
            + mod.Spill_Water[r, tmp]
            + mod.Evaporative_Losses[r, tmp]
        )

    m.Gross_Reservoir_Outflow = Expression(
        m.RESERVOIRS,
        m.TIMEPOINTS,
        within=NonNegativeReals,
        initialize=gross_reservoir_outflow_rule,
    )

    def net_reservoir_outflow_rule(mod, r, tmp):
        return m.Gross_Reservoir_Outflow[r, tmp] - m.Store_Water[r, tmp]

    m.Net_Reservoir_Outflow = Expression(
        m.RESERVOIRS,
        m.TIMEPOINTS,
        within=NonNegativeReals,
        initialize=net_reservoir_outflow_rule,
    )

    # ### Constraints ### #

    def set_target_conditions(mod, node, tmp):
        return (
            m.Reservoir_Starting_Volume_WaterVolumeUnit[node, tmp]
            == mod.reservoir_target_volume[node, tmp]
        )

    m.Reservoir_Volume_Target_Volume_Constraint = Constraint(
        m.RESERVOIR_TMPS_W_TARGET_VOLUME, rule=set_target_conditions
    )

    def enforce_elevation_volume_relationship(mod, r, tmp):
        return (
            mod.Reservoir_Starting_Elevation_ElevationUnit[r, tmp]
            == mod.volume_to_elevation_conversion_coefficient[r]
            * m.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]
        )

    m.Elevation_Volume_Relationship_Constraint = Constraint(
        m.RESERVOIRS, m.TIMEPOINTS, rule=enforce_elevation_volume_relationship
    )

    def reservoir_water_volume_tracking_rule(mod, r, tmp):
        """ """
        if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_reservoir[r]
        ) and check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_reservoir[r],
            boundary_type="linear",
        ):
            return Constraint.Skip
        else:
            if check_if_first_timepoint(
                mod=mod, tmp=tmp, balancing_type=mod.balancing_type_reservoir[r]
            ) and check_boundary_type(
                mod=mod,
                tmp=tmp,
                balancing_type=mod.balancing_type_reservoir[r],
                boundary_type="linked",
            ):
                # TODO: add linked later
                pass
                starting_water_volume = None
            else:
                prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                    mod.prev_tmp[tmp, mod.balancing_type_reservoir[r]]
                ]
                prev_tmp_starting_water_volume = (
                    mod.Reservoir_Starting_Volume_WaterVolumeUnit[
                        r, mod.prev_tmp[tmp, mod.balancing_type_reservoir[r]]
                    ]
                )
                prev_tmp_net_outflow = mod.Net_Reservoir_Outflow[
                    r, mod.prev_tmp[tmp, mod.balancing_type_reservoir[r]]
                ]

                # TODO: CRITICAL, units requirements to get multiplication by
                #  hours in timepoint to work
                starting_water_volume = (
                    prev_tmp_starting_water_volume
                    - prev_tmp_net_outflow * prev_tmp_hrs_in_tmp
                )

        return (
            mod.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]
            == starting_water_volume
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

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "RESERVOIRS.tab",
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
