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
from gridpath.common_functions import (
    create_results_df,
)
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
    m.RESERVOIR_NODES = Set(dimen=2)
    m.RESERVOIRS = Set(
        initialize=lambda mod: sorted(list(set(r for (r, n) in mod.RESERVOIR_NODES)))
    )

    def reservoirs_by_node_rule(mod, node):
        list_of_res = []
        for r, n in mod.RESERVOIR_NODES:
            if n == node:
                list_of_res.append(r)

        return list_of_res

    m.RESERVOIRS_BY_NODE = Set(m.WATER_NODES, initialize=reservoirs_by_node_rule)

    m.RESERVOIR_TMPS_W_TARGET_ELEVATION = Set(within=m.RESERVOIRS * m.TMPS)

    # ### Parameters ###
    m.balancing_type_reservoir = Param(m.RESERVOIRS, within=m.BLN_TYPES)

    # Elevation targets
    m.reservoir_target_elevation = Param(
        m.RESERVOIR_TMPS_W_TARGET_ELEVATION, within=NonNegativeReals
    )
    # Elevation bounds
    # Max varies by season
    # TODO: add time varying
    m.maximum_elevation_elevationunit = Param(
        m.RESERVOIRS, default=float("inf"), within=NonNegativeReals
    )
    # In CHEOPS, min elevation is a single value for each reservoir and does
    # not vary over time
    m.minimum_elevation_elevationunit = Param(
        m.RESERVOIRS, default=0, within=NonNegativeReals
    )

    # TODO: make this piecewise linear or a nonlinear function
    # Volume to elevation conversion
    m.volume_to_elevation_conversion_coefficient = Param(
        m.RESERVOIRS, within=NonNegativeReals, default=1
    )

    # Spill bound
    # TODO: make max spill a function of elevation
    m.max_spill = Param(m.RESERVOIRS, default=0, within=NonNegativeReals)

    # Losses
    # TODO: by month
    m.evaporation_coefficient = Param(m.RESERVOIRS, within=NonNegativeReals, default=0)

    # ### Variables ### #
    # TODO: elevation/volume relationship
    m.Reservoir_Starting_Elevation_ElevationUnit = Var(
        m.RESERVOIRS, m.TMPS, within=NonNegativeReals
    )
    m.Reservoir_Starting_Volume_WaterVolumeUnit = Var(
        m.RESERVOIRS, m.TMPS, within=NonNegativeReals
    )

    # Controls
    m.Store_Water = Var(m.RESERVOIRS, m.TMPS, within=NonNegativeReals)
    m.Discharge_Water_to_Powerhouse = Var(m.RESERVOIRS, m.TMPS, within=NonNegativeReals)
    m.Spill_Water = Var(m.RESERVOIRS, m.TMPS, within=NonNegativeReals)

    # TODO: implement the correct calculation; depends on area, which depends
    #  on elevation
    # Losses
    m.Evaporative_Losses = Expression(
        m.RESERVOIRS,
        m.TMPS,
        initialize=lambda mod, r, tmp: mod.evaporation_coefficient[r],
    )

    # ### Expressions ### #

    def gross_reservoir_outflow_rule(mod, r, tmp):
        return (
            mod.Discharge_Water_to_Powerhouse[r, tmp]
            + mod.Spill_Water[r, tmp]
            + mod.Evaporative_Losses[r, tmp]
        )

    m.Gross_Reservoir_Outflow = Expression(
        m.RESERVOIRS,
        m.TMPS,
        initialize=gross_reservoir_outflow_rule,
    )

    def net_reservoir_outflow_rule(mod, r, tmp):
        return mod.Gross_Reservoir_Outflow[r, tmp] - mod.Store_Water[r, tmp]

    m.Net_Reservoir_Outflow = Expression(
        m.RESERVOIRS,
        m.TMPS,
        initialize=net_reservoir_outflow_rule,
    )

    # ### Constraints ### #

    def set_target_conditions(mod, r, tmp):
        return (
            mod.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]
            == mod.reservoir_target_elevation[r, tmp]
            / mod.volume_to_elevation_conversion_coefficient[r]
        )

    m.Reservoir_Volume_Target_Volume_Constraint = Constraint(
        m.RESERVOIR_TMPS_W_TARGET_ELEVATION, rule=set_target_conditions
    )

    def enforce_elevation_volume_relationship(mod, r, tmp):
        return (
            mod.Reservoir_Starting_Elevation_ElevationUnit[r, tmp]
            == mod.volume_to_elevation_conversion_coefficient[r]
            * mod.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]
        )

    m.Elevation_Volume_Relationship_Constraint = Constraint(
        m.RESERVOIRS, m.TMPS, rule=enforce_elevation_volume_relationship
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

    m.Reservoir_Water_Volume_Tracking_Constraint = Constraint(
        m.RESERVOIRS, m.TMPS, rule=reservoir_water_volume_tracking_rule
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
            "reservoirs.tab",
        ),
        select=("reservoir", "water_node"),
        index=m.RESERVOIR_NODES,
        param=(),
    )

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "reservoirs.tab",
        ),
        param=(
            m.balancing_type_reservoir,
            m.minimum_elevation_elevationunit,
            m.maximum_elevation_elevationunit,
            m.volume_to_elevation_conversion_coefficient,
            m.max_spill,
            m.evaporation_coefficient,
        ),
        select=(
            "reservoir",
            "balancing_type_reservoir",
            "minimum_elevation_elevationunit",
            "maximum_elevation_elevationunit",
            "volume_to_elevation_conversion_coefficient",
            "max_spill",
            "evaporation_coefficient",
        ),
    )
    fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "reservoir_target_elevations.tab",
    )
    if os.path.exists(fname):
        data_portal.load(
            filename=fname,
            index=m.RESERVOIR_TMPS_W_TARGET_ELEVATION,
            param=m.reservoir_target_elevation,
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

    c1 = conn.cursor()
    reservoirs = c1.execute(
        f"""SELECT reservoir, water_node, balancing_type_reservoir,
            minimum_elevation_elevationunit,
            maximum_elevation_elevationunit,
            volume_to_elevation_conversion_coefficient,
            max_spill,
            evaporation_coefficient
        FROM inputs_system_water_reservoirs
        WHERE water_reservoir_scenario_id = 
        {subscenarios.WATER_RESERVOIR_SCENARIO_ID};
        """
    )

    c2 = conn.cursor()
    target_elevations = c2.execute(
        f"""SELECT reservoir, timepoint, reservoir_target_elevation
        FROM inputs_system_water_reservoirs_target_elevations
        WHERE (reservoir, target_elevation_scenario_id)
        IN (SELECT reservoir, target_elevation_scenario_id
            FROM inputs_system_water_reservoirs
            WHERE water_reservoir_scenario_id = 
            {subscenarios.WATER_RESERVOIR_SCENARIO_ID}
        )
        AND timepoint
        IN (SELECT timepoint
            FROM inputs_temporal
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            AND subproblem_id = {subproblem}
            AND stage_id = {stage});
        """
    )

    return reservoirs, target_elevations


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

    reservoirs, target_elevations = get_inputs_from_database(
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
            "reservoirs.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "reservoir",
                "water_node",
                "balancing_type_reservoir",
                "minimum_elevation_elevationunit",
                "maximum_elevation_elevationunit",
                "volume_to_elevation_conversion_coefficient",
                "max_spill",
                "evaporation_coefficient",
            ]
        )

        for row in reservoirs:
            writer.writerow(row)

    target_volumes_list = [row for row in target_elevations]
    if target_volumes_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "reservoir_target_elevations.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["reservoir", "timepoint", "reservoir_target_elevation"])

            for row in target_volumes_list:
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
    results_columns = [
        "starting_elevation",
        "starting_volume",
        "store_water",
        "discharge_water_to_powerhouse",
        "spill_water",
    ]
    data = [
        [
            r,
            tmp,
            value(m.Reservoir_Starting_Elevation_ElevationUnit[r, tmp]),
            value(m.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]),
            value(m.Store_Water[r, tmp]),
            value(m.Discharge_Water_to_Powerhouse[r, tmp]),
            value(m.Spill_Water[r, tmp]),
        ]
        for r in m.RESERVOIRS
        for tmp in m.TMPS
    ]
    results_df = create_results_df(
        index_columns=["reservoir", "timepoint"],
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
            "reservoir_timepoint.csv",
        ),
        sep=",",
        index=True,
    )


# TODO: results import
