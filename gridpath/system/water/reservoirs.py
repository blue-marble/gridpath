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
Reservoir operation.
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

from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules,
    load_subtype_modules,
)
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import (
    create_results_df,
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

    # ### Reservoirs ### #
    m.WATER_NODES_W_RESERVOIRS = Set(within=m.WATER_NODES)

    m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME = Set(
        within=m.WATER_NODES_W_RESERVOIRS * m.TMPS
    )

    # ### Parameters ###
    m.balancing_type_reservoir = Param(m.WATER_NODES_W_RESERVOIRS, within=m.BLN_TYPES)

    # Volume targets
    m.reservoir_target_volume = Param(
        m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME, within=NonNegativeReals
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

    # Sets and params
    # Release targets
    # Total release requirements
    m.WATER_NODE_RESERVOIR_BT_HRZS_WITH_TOTAL_RELEASE_REQUIREMENTS = Set(
        within=m.WATER_NODES * m.BLN_TYPE_HRZS
    )
    m.reservoir_target_release = Param(
        m.WATER_NODE_RESERVOIR_BT_HRZS_WITH_TOTAL_RELEASE_REQUIREMENTS,
        within=NonNegativeReals,
    )

    # Spill bound
    # TODO: make max spill a function of elevation
    # TODO: move to all nodes
    # TODO: where should the spill variable be
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

    m.Discharge_Water_to_Powerhouse = Var(
        m.WATER_NODES_W_RESERVOIRS, m.TMPS, within=NonNegativeReals
    )

    m.Spill_Water = Var(m.WATER_NODES_W_RESERVOIRS, m.TMPS, within=NonNegativeReals)

    # TODO: implement the correct calculation; depends on area, which depends
    #  on elevation
    # Losses
    m.Evaporative_Losses = Expression(
        m.WATER_NODES_W_RESERVOIRS,
        m.TMPS,
        initialize=lambda mod, r, tmp: mod.evaporation_coefficient[r],
    )

    def gross_reservoir_release(mod, wn_w_r, tmp):
        return (
            mod.Discharge_Water_to_Powerhouse[wn_w_r, tmp]
            + mod.Spill_Water[wn_w_r, tmp]
            + mod.Evaporative_Losses[wn_w_r, tmp]
        )

    m.Gross_Reservoir_Release = Expression(
        m.WATER_NODES_W_RESERVOIRS,
        m.TMPS,
        initialize=gross_reservoir_release,
    )

    # ### Constraints ### #

    def reservoir_target_storage_constraint_rule(mod, wn_w_r, tmp):
        """ """
        return (
            mod.Reservoir_Starting_Volume_WaterVolumeUnit[wn_w_r, tmp]
            == mod.reservoir_target_volume[wn_w_r, tmp]
        )

    m.Reservoir_Target_Storage_Constraint = Constraint(
        m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME,
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

    # Target releases
    # TODO: check multiplication by 3600 and hrs_in_tmp
    def reservoir_target_release_constraint_rule(mod, wn, bt, hrz):
        """ """
        return (
            sum(
                mod.Gross_Reservoir_Release[wn, tmp] * 3600 * mod.hrs_in_tmp[tmp]
                for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
            )
            == mod.reservoir_target_release[wn, bt, hrz]
        )

    m.Water_Node_Target_Release_Constraint = Constraint(
        m.WATER_NODE_RESERVOIR_BT_HRZS_WITH_TOTAL_RELEASE_REQUIREMENTS,
        rule=reservoir_target_release_constraint_rule,
    )

    # ### Elevation ### #
    # TODO: move within clause to a central location
    m.elevation_type = Param(
        m.WATER_NODES_W_RESERVOIRS, within=["exogenous", "endogenous"]
    )

    # Import needed elevation modules
    required_elevation_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="elevation_type",
        filename="water_node_reservoirs",
    )

    imported_elevation_modules = load_subtype_modules(
        required_subtype_modules=required_elevation_modules,
        package="gridpath.system.water.elevation_types",
        required_attributes=[],
    )

    # Add any components specific to the operational modules
    for op_m in required_elevation_modules:
        imp_op_m = imported_elevation_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(
                m,
                d,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )

    def elevation_rule(mod, r, tmp):
        elevation_type = mod.elevation_type[r]
        return imported_elevation_modules[elevation_type].elevation_rule(mod, r, tmp)

    m.Reservoir_Starting_Elevation_ElevationUnit = Expression(
        m.WATER_NODES_W_RESERVOIRS, m.TMPS, rule=elevation_rule
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
            "water_node_reservoirs.tab",
        ),
        index=m.WATER_NODES_W_RESERVOIRS,
        param=(
            m.balancing_type_reservoir,
            m.minimum_volume_volumeunit,
            m.maximum_volume_volumeunit,
            m.max_spill,
            m.evaporation_coefficient,
            m.elevation_type,
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
            index=m.WATER_NODE_RESERVOIR_TMPS_W_TARGET_VOLUME,
            param=m.reservoir_target_volume,
        )

    rel_fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "reservoir_release_targets.tab",
    )
    if os.path.exists(rel_fname):
        data_portal.load(
            filename=rel_fname,
            index=m.WATER_NODE_RESERVOIR_BT_HRZS_WITH_TOTAL_RELEASE_REQUIREMENTS,
            param=m.reservoir_target_release,
        )

    # TODO: refactor
    # Import needed elevation modules
    required_elevation_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="elevation_type",
        filename="water_node_reservoirs",
    )

    imported_elevation_modules = load_subtype_modules(
        required_subtype_modules=required_elevation_modules,
        package="gridpath.system.water.elevation_types",
        required_attributes=[],
    )

    # Add any components specific to the operational modules
    for op_m in required_elevation_modules:
        imp_op_m = imported_elevation_modules[op_m]
        if hasattr(imp_op_m, "load_model_data"):
            imp_op_m.load_model_data(
                m,
                d,
                data_portal,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
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
    reservoirs = c.execute(
        f"""SELECT water_node, balancing_type_reservoir,
            minimum_volume_volumeunit,
            maximum_volume_volumeunit,
            max_spill,
            evaporation_coefficient,
            elevation_type
        FROM inputs_system_water_node_reservoirs
        WHERE water_node_reservoir_scenario_id = 
        {subscenarios.WATER_NODE_RESERVOIR_SCENARIO_ID};
        """
    )

    c1 = conn.cursor()
    target_volumes = c1.execute(
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

    c2 = conn.cursor()
    target_releases = c2.execute(
        f"""SELECT water_node, balancing_type, horizon, reservoir_target_release
            FROM inputs_system_water_node_reservoirs_target_releases
            WHERE (water_node, target_release_scenario_id)
            IN (SELECT water_node, target_release_scenario_id
                FROM inputs_system_water_node_reservoirs
                WHERE water_node_reservoir_scenario_id = 
                {subscenarios.WATER_NODE_RESERVOIR_SCENARIO_ID}
            )
            AND (balancing_type, horizon)
            IN (SELECT balancing_type_horizon, horizon
                FROM inputs_temporal_horizons
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            )
            ;
            """
    )

    return reservoirs, target_volumes, target_releases


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

    reservoirs, target_volumes, target_releases = get_inputs_from_database(
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
                "elevation_type",
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

    target_releases_list = [row for row in target_releases]
    if target_releases_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "reservoir_target_releases.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["reservoir", "balancing_type", "horizon", "reservoir_target_release"]
            )

            for row in target_releases_list:
                writer.writerow(row)

    # TODO: refactor
    # Import needed elevation modules
    required_elevation_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="elevation_type",
        filename="water_node_reservoirs",
    )

    imported_elevation_modules = load_subtype_modules(
        required_subtype_modules=required_elevation_modules,
        package="gridpath.system.water.elevation_types",
        required_attributes=[],
    )

    # Add any components specific to the operational modules
    for op_m in required_elevation_modules:
        imp_op_m = imported_elevation_modules[op_m]
        if hasattr(imp_op_m, "write_model_inputs"):
            imp_op_m.write_model_inputs(
                scenario_directory,
                scenario_id,
                subscenarios,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                conn,
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
            (
                value(m.Discharge_Water_to_Powerhouse[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            (
                value(m.Spill_Water[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
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
