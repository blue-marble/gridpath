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
Defines the mass balance at each node. For nodes with no reservoirs,
total inflows equal total outflows. For nodes with reservoirs, total inflows
minus total inflows equals the change in reservoir volume between timepoints.
"""

import csv
import os.path
from pyomo.environ import (
    Boolean,
    NonNegativeIntegers,
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

    # ### Expressions ### #
    def gross_node_inflow(mod, wn, tmp):
        return mod.exogenous_water_inflow_rate_vol_per_sec[wn, tmp] + sum(
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp]
            for wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn]
        )

    m.Gross_Water_Node_Inflow_Rate_Vol_Per_Sec = Expression(
        m.WATER_NODES,
        m.TMPS,
        initialize=gross_node_inflow,
    )

    def gross_node_release_rate_vol_per_sec(mod, wn, tmp):
        # If we have e reservoir, this is controlled by the reservoir
        # variables; otherwise, just set it to inflow for the mass balance
        return (
            mod.Gross_Reservoir_Release_Rate_Vol_Per_Sec[wn, tmp]
            if wn in mod.WATER_NODES_W_RESERVOIRS
            else 0
        ) + (
            mod.Gross_Water_Node_Inflow_Rate_Vol_Per_Sec[wn, tmp]
            if wn not in mod.WATER_NODES_W_RESERVOIRS
            else 0
        )

    m.Gross_Water_Node_Release_Rate_Vol_per_Sec = Expression(
        m.WATER_NODES,
        m.TMPS,
        initialize=gross_node_release_rate_vol_per_sec,
    )

    # ### Constraints ### #
    def get_total_inflow_volunit(mod, wn, tmp):
        """
        Total inflow is exogenous inflow at node plus sum of endogenous
        inflow from all links to node
        """
        inflow_in_tmp = (
            (
                mod.exogenous_water_inflow_rate_vol_per_sec[wn, tmp]
                + sum(
                    mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp]
                    for wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn]
                )
            )
            * 3600
            * mod.hrs_in_tmp[tmp]
        )

        return inflow_in_tmp

    def get_total_release_volunit(mod, wn, tmp):
        outflow_in_tmp = (
            mod.Gross_Water_Node_Release_Rate_Vol_per_Sec[wn, tmp]
            * 3600
            * mod.hrs_in_tmp[tmp]
        )

        return outflow_in_tmp

    def water_mass_balance_constraint_rule(mod, wn, tmp):
        """ """
        # If no reservoir, simply set total inflow equal to total release
        if wn not in mod.WATER_NODES_W_RESERVOIRS:
            return get_total_inflow_volunit(mod, wn, tmp) == get_total_release_volunit(
                mod, wn, tmp
            )
        # If the node does have a reservoir, we'll track the water in storage
        else:
            # No constraint in the first timepoint of a linear horizon (no
            # previous timepoint for tracking)
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
                # TODO: add linked horizons
                if check_if_first_timepoint(
                    mod=mod, tmp=tmp, balancing_type=mod.balancing_type_reservoir[wn]
                ) and check_boundary_type(
                    mod=mod,
                    tmp=tmp,
                    balancing_type=mod.balancing_type_reservoir[wn],
                    boundary_type="linked",
                ):
                    current_tmp_starting_water_volume = None
                    prev_tmp_starting_water_volume = None

                    # Inflows and releases
                    prev_tmp_inflow = None
                    prev_tmp_release = None
                    raise (
                        UserWarning(
                            "Linked horizons have not been implemented for "
                            "water system feature."
                        )
                    )
                else:
                    current_tmp_starting_water_volume = (
                        mod.Reservoir_Starting_Volume_WaterVolumeUnit[wn, tmp]
                    )
                    prev_tmp_starting_water_volume = (
                        mod.Reservoir_Starting_Volume_WaterVolumeUnit[
                            wn, mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                        ]
                    )

                    # Inflows and releases; these are already calculated
                    # based on per sec flows and hours in the timepoint
                    prev_tmp_inflow = get_total_inflow_volunit(
                        mod, wn, mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                    )

                    prev_tmp_release = get_total_release_volunit(
                        mod, wn, mod.prev_tmp[tmp, mod.balancing_type_reservoir[wn]]
                    )

                return current_tmp_starting_water_volume == (
                    prev_tmp_starting_water_volume + prev_tmp_inflow - prev_tmp_release
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
                    mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp]
                    for wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]
                )
                == mod.Gross_Water_Node_Release_Rate_Vol_per_Sec[wn, tmp]
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
        param=m.exogenous_water_inflow_rate_vol_per_sec,
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
    water_inflows = c1.execute(
        f"""SELECT water_node, timepoint, exogenous_water_inflow_rate_vol_per_sec
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

    return water_inflows


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

    inflows = get_inputs_from_database(
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
                "exogenous_water_inflow_rate_vol_per_sec",
            ]
        )

        for row in inflows:
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
            m.exogenous_water_inflow_rate_vol_per_sec[wn, tmp],
            sum(
                value(m.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp])
                for wl in m.WATER_LINKS_TO_BY_WATER_NODE[wn]
            ),
            value(
                m.Discharge_Water_to_Powerhouse[wn, tmp]
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
                value(m.Water_Link_Flow_Rate_Vol_per_Sec[wl, tmp])
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
