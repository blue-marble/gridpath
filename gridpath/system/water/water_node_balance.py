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
    NonNegativeIntegers,
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

    # TODO: units
    m.exogenous_water_inflow_vol_per_sec = Param(
        m.WATER_NODES, m.TMPS, default=0, within=NonNegativeReals
    )

    def water_links_to_by_water_node_rule(mod, wn):
        wl_list = []
        for wl in mod.WATER_LINKS:
            if mod.water_node_to[wl] == wn:
                wl_list.append(wl)

        return wl_list

    def water_links_from_by_water_node_rule(mod, wn):
        wl_list = []
        for wl in mod.WATER_LINKS:
            if mod.water_node_from[wl] == wn:
                wl_list.append(wl)

        return wl_list

    m.WATER_LINKS_TO_BY_WATER_NODE = Set(
        m.WATER_NODES, initialize=water_links_to_by_water_node_rule
    )

    m.WATER_LINKS_FROM_BY_WATER_NODE = Set(
        m.WATER_NODES, initialize=water_links_from_by_water_node_rule
    )

    # ### Reservoirs ### #
    m.WATER_NODES_W_RESERVOIRS = Set(within=m.WATER_NODES)

    m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_ELEVATION = Set(
        within=m.WATER_NODES_W_RESERVOIRS * m.TMPS
    )

    # ### Parameters ###
    m.balancing_type_reservoir = Param(m.WATER_NODES_W_RESERVOIRS, within=m.BLN_TYPES)

    # Elevation targets
    m.reservoir_target_volume = Param(
        m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_ELEVATION, within=NonNegativeReals
    )
    # Elevation bounds
    # Max varies by season
    # TODO: add time varying
    m.maximum_volume_volumeunit = Param(
        m.WATER_NODES_W_RESERVOIRS, within=NonNegativeReals
    )
    # In CHEOPS, min elevation is a single value for each reservoir and does
    # not vary over time
    m.minimum_volume_volumeunit = Param(
        m.WATER_NODES_W_RESERVOIRS, within=NonNegativeReals
    )

    # Spill bound
    # TODO: make max spill a function of elevation
    m.max_spill = Param(m.WATER_NODES_W_RESERVOIRS, within=NonNegativeReals)

    # Losses
    # TODO: by month
    m.evaporation_coefficient = Param(
        m.WATER_NODES_W_RESERVOIRS, within=NonNegativeReals
    )

    # ### Variables ### #
    m.Reservoir_Starting_Volume_WaterVolumeUnit = Var(
        m.WATER_NODES_W_RESERVOIRS, m.TMPS, within=NonNegativeReals
    )

    # Controls
    # TODO: need upper bounds on discharge / spill
    m.Discharge_Water_to_Powerhouse = Var(
        m.WATER_NODES, m.TMPS, within=NonNegativeReals
    )
    m.Spill_Water = Var(m.WATER_NODES, m.TMPS, within=NonNegativeReals)

    # TODO: implement the correct calculation; depends on area, which depends
    #  on elevation
    # Losses
    m.Evaporative_Losses = Expression(
        m.WATER_NODES_W_RESERVOIRS,
        m.TMPS,
        initialize=lambda mod, r, tmp: mod.evaporation_coefficient[r],
    )

    # ### Expressions ### #
    def gross_node_inflow(mod, wn, tmp):
        return mod.exogenous_water_inflow_vol_per_sec[wn, tmp] + sum(
            mod.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp]
            for wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn]
        )

    m.Gross_Water_Node_Inflow = Expression(
        m.WATER_NODES,
        m.TMPS,
        initialize=gross_node_inflow,
    )

    def gross_node_release(mod, wn, tmp):
        return (
            mod.Discharge_Water_to_Powerhouse[wn, tmp]
            + mod.Spill_Water[wn, tmp]
            + (
                mod.Evaporative_Losses[wn, tmp]
                if wn in mod.WATER_NODES_W_RESERVOIRS
                else 0
            )
        )

    m.Gross_Water_Node_Release = Expression(
        m.WATER_NODES,
        m.TMPS,
        initialize=gross_node_release,
    )

    # ### Constraints ### #

    def reservoir_target_storage_constraint_rule(mod, wn_w_r, tmp):
        """ """
        return (
            mod.Reservoir_Starting_Volume_WaterVolumeUnit[wn_w_r, tmp]
            == mod.reservoir_target_volume[wn_w_r, tmp]
        )

    m.Reservoir_Target_Storage_Constraint = Constraint(
        m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_ELEVATION,
        rule=reservoir_target_storage_constraint_rule,
    )

    def reservoir_storage_min_bound_constraint_rule(mod, r, tmp):
        return (
            mod.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]
            >= mod.minimum_volume_volumeunit[r]
        )

    m.Minimum_Water_Storage_Constraint = Constraint(
        m.WATER_NODES_W_RESERVOIRS,
        m.TMPS,
        rule=reservoir_storage_min_bound_constraint_rule,
    )

    def reservoir_storage_max_bound_constraint_rule(mod, r, tmp):
        return (
            mod.Reservoir_Starting_Volume_WaterVolumeUnit[r, tmp]
            <= mod.maximum_volume_volumeunit[r]
        )

    m.Maximum_Water_Storage_Constraint = Constraint(
        m.WATER_NODES_W_RESERVOIRS,
        m.TMPS,
        rule=reservoir_storage_max_bound_constraint_rule,
    )

    def get_inflow_volunit_per_hour_in_tmp(mod, wn, tmp):
        # TODO: check and document multiplication by 3600 to get from per s
        #  to per h
        inflow_in_tmp = (
            mod.exogenous_water_inflow_vol_per_sec[wn, tmp]
            + sum(
                mod.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp]
                for wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn]
            )
        ) * 3600

        return inflow_in_tmp

    def get_release_volunit_per_hour_in_tmp(mod, wn, tmp):
        # TODO: check and document multiplication by 3600 to get from per s
        #  to per h
        outflow_in_tmp = mod.Gross_Water_Node_Release[wn, tmp] * 3600

        return outflow_in_tmp

    def water_mass_balance_constraint_rule(mod, wn, tmp):
        """ """
        # If no reservoir, simply set inflows equal to release
        if wn not in mod.WATER_NODES_W_RESERVOIRS:
            return get_inflow_volunit_per_hour_in_tmp(
                mod, wn, tmp
            ) == get_release_volunit_per_hour_in_tmp(mod, wn, tmp)
        # If the node does have a reservoir, we'll track the water in storage
        else:
            if check_if_first_timepoint(
                mod=mod, tmp=tmp, balancing_type=mod.balancing_type_reservoir[wn]
            ) and check_boundary_type(
                mod=mod,
                tmp=tmp,
                balancing_type=mod.balancing_type_reservoir[wn],
                boundary_type="linear",
            ):
                return Constraint.Skip
            else:
                if check_if_first_timepoint(
                    mod=mod, tmp=tmp, balancing_type=mod.balancing_type_reservoir[wn]
                ) and check_boundary_type(
                    mod=mod,
                    tmp=tmp,
                    balancing_type=mod.balancing_type_reservoir[wn],
                    boundary_type="linked",
                ):
                    # TODO: add linked later
                    prev_tmp_hrs_in_tmp = None
                    current_tmp_starting_water_volume = None
                    prev_tmp_starting_water_volume = None

                    # TODO: units; make clear net flows are per s
                    # Inflows and releases
                    prev_tmp_inflow = None

                    prev_tmp_release = None
                else:
                    prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                        mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                    ]
                    current_tmp_starting_water_volume = (
                        mod.Reservoir_Starting_Volume_WaterVolumeUnit[wn, tmp]
                    )
                    prev_tmp_starting_water_volume = (
                        mod.Reservoir_Starting_Volume_WaterVolumeUnit[
                            wn, mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                        ]
                    )

                    # TODO: units; make clear net flows are per s
                    # Inflows and releases
                    prev_tmp_inflow = get_inflow_volunit_per_hour_in_tmp(
                        mod, wn, mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                    )

                    prev_tmp_release = get_release_volunit_per_hour_in_tmp(
                        mod, wn, mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                    )

                    # TODO: CRITICAL, units requirements to get multiplication by
                    #  hours in timepoint to work

                return current_tmp_starting_water_volume == (
                    prev_tmp_starting_water_volume
                    + prev_tmp_inflow * prev_tmp_hrs_in_tmp
                    - prev_tmp_release * prev_tmp_hrs_in_tmp
                )

    m.Water_Mass_Balance_Constraint = Constraint(
        m.WATER_NODES, m.TMPS, rule=water_mass_balance_constraint_rule
    )

    # Set the sum of outflows from the node to be equal to discharge & spill
    def enforce_outflow_rule(mod, wn, tmp):
        """
        The sum of the flows on all links from this node must equal the gross
        outflow from the node. Skip constraint for the last node in the
        network with no out links.
        """
        if [wl for wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]]:
            return (
                sum(
                    mod.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp]
                    for wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]
                )
                == mod.Gross_Water_Node_Release[wn, tmp]
            )
        else:
            return Constraint.Skip

    m.Water_Node_Outflow_Constraint = Constraint(
        m.WATER_NODES, m.TMPS, rule=enforce_outflow_rule
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
            "water_inflows.tab",
        ),
        param=m.exogenous_water_inflow_vol_per_sec,
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
            "water_node_reservoirs.tab",
        ),
        index=m.WATER_NODES_W_RESERVOIRS,
        param=(
            m.balancing_type_reservoir,
            m.minimum_volume_volumeunit,
            m.maximum_volume_volumeunit,
            m.max_spill,
            m.evaporation_coefficient,
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
        "reservoir_target_volumes.tab",
    )
    if os.path.exists(fname):
        data_portal.load(
            filename=fname,
            index=m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_ELEVATION,
            param=m.reservoir_target_volume,
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
    water_inflows = c.execute(
        f"""SELECT water_node, timepoint, exogenous_water_inflow_vol_per_sec
                FROM inputs_system_water_inflows
                WHERE water_inflow_scenario_id = 
                {subscenarios.WATER_INFLOW_SCENARIO_ID}
                AND timepoint
                IN (SELECT timepoint
                    FROM inputs_temporal
                    WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                    AND subproblem_id = {subproblem}
                    AND stage_id = {stage})
                ;
                """
    )

    c2 = conn.cursor()
    reservoirs = c2.execute(
        f"""SELECT water_node, balancing_type_reservoir,
            minimum_volume_volumeunit,
            maximum_volume_volumeunit,
            max_spill,
            evaporation_coefficient
        FROM inputs_system_water_node_reservoirs
        WHERE water_node_reservoir_scenario_id = 
        {subscenarios.WATER_NODE_RESERVOIR_SCENARIO_ID};
        """
    )

    c3 = conn.cursor()
    target_volumes = c3.execute(
        f"""SELECT water_node, timepoint, reservoir_target_volume
        FROM inputs_system_water_node_reservoirs_target_volumes
        WHERE (water_node, target_volume_scenario_id)
        IN (SELECT water_node, target_volume_scenario_id
            FROM inputs_system_water_node_reservoirs
            WHERE water_node_reservoir_scenario_id = 
            {subscenarios.WATER_NODE_RESERVOIR_SCENARIO_ID}
        )
        AND timepoint
        IN (SELECT timepoint
            FROM inputs_temporal
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            AND subproblem_id = {subproblem}
            AND stage_id = {stage});
        """
    )

    return water_inflows, reservoirs, target_volumes


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

    inflows, reservoirs, target_volumes = get_inputs_from_database(
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
            "water_inflows.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "water_node",
                "timepoint",
                "exogenous_water_inflow_vol_per_sec",
            ]
        )

        for row in inflows:
            writer.writerow(row)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "water_node_reservoirs.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "water_node",
                "balancing_type_reservoir",
                "minimum_volume_volumeunit",
                "maximum_volume_volumeunit",
                "max_spill",
                "evaporation_coefficient",
            ]
        )

        for row in reservoirs:
            writer.writerow(row)

    target_volumes_list = [row for row in target_volumes]
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
                "reservoir_target_volumes.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["reservoir", "timepoint", "reservoir_target_volume"])

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
        "exogenous_water_inflows",
        "endogenous_water_inflows",
        "discharge_water_to_powerhouse",
        "spill_water",
        "evap_losses",
        "endogenous_water_outflows",
    ]
    data = [
        [
            wn,
            tmp,
            (
                value(m.Reservoir_Starting_Elevation_ElevationUnit[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            (
                value(m.Reservoir_Starting_Volume_WaterVolumeUnit[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            m.exogenous_water_inflow_vol_per_sec[wn, tmp],
            sum(
                value(m.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp])
                for wl in m.WATER_LINKS_TO_BY_WATER_NODE[wn]
            ),
            value(m.Discharge_Water_to_Powerhouse[wn, tmp]),
            value(m.Spill_Water[wn, tmp]),
            (
                value(m.Evaporative_Losses[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            sum(
                value(m.Water_Link_Flow_Vol_per_Sec_in_Tmp[wl, tmp])
                for wl in m.WATER_LINKS_FROM_BY_WATER_NODE[wn]
            ),
        ]
        for wn in m.WATER_NODES
        for tmp in m.TMPS
    ]
    results_df = create_results_df(
        index_columns=["water_node", "timepoint"],
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
            "water_node_timepoint.csv",
        ),
        sep=",",
        index=True,
    )


# TODO: results import
