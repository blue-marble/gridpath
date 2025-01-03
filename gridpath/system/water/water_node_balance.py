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

from gridpath.auxiliary.db_interface import directories_to_db_values, import_csv
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
    def gross_node_inflow_rate_init(mod, wn, tmp):
        """
        Exogenous inflow to node + sum of flow on all links to note in the
        timepoint of arrival
        """
        return mod.exogenous_water_inflow_rate_vol_per_sec[wn, tmp] + sum(
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
            for (wl, dep_tmp, arr_tmp) in mod.WATER_LINK_DEPARTURE_ARRIVAL_TMPS
            if wl in mod.WATER_LINKS_TO_BY_WATER_NODE[wn] and arr_tmp == tmp
        )

    m.Gross_Water_Node_Inflow_Rate_Vol_Per_Sec = Expression(
        m.WATER_NODES,
        m.TMPS,
        initialize=gross_node_inflow_rate_init,
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
            mod.Gross_Water_Node_Inflow_Rate_Vol_Per_Sec[wn, tmp]
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
                mod=mod, tmp=tmp, balancing_type=mod.water_system_balancing_type
            ) and check_boundary_type(
                mod=mod,
                tmp=tmp,
                balancing_type=mod.water_system_balancing_type,
                boundary_type="linear",
            ):
                return Constraint.Skip
            else:
                # TODO: add linked horizons
                if check_if_first_timepoint(
                    mod=mod, tmp=tmp, balancing_type=mod.water_system_balancing_type
                ) and check_boundary_type(
                    mod=mod,
                    tmp=tmp,
                    balancing_type=mod.water_system_balancing_type,
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
                            wn, mod.prev_tmp[tmp, mod.water_system_balancing_type]
                        ]
                    )

                    # Inflows and releases; these are already calculated
                    # based on per sec flows and hours in the timepoint
                    prev_tmp_inflow = get_total_inflow_volunit(
                        mod, wn, mod.prev_tmp[tmp, mod.water_system_balancing_type]
                    )

                    prev_tmp_release = get_total_release_volunit(
                        mod, wn, mod.prev_tmp[tmp, mod.water_system_balancing_type]
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
                    mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
                    for (wl, dep_tmp, arr_tmp) in mod.WATER_LINK_DEPARTURE_ARRIVAL_TMPS
                    if wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn] and dep_tmp == tmp
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
        "exogenous_water_inflow_rate_vol_per_sec",
        "endogenous_water_inflow_rate_vol_per_sec",
        "gross_water_inflow_rate_vol_per_sec",
        "discharge_water_to_powerhouse_rate_vol_per_sec",
        "spill_water_rate_vol_per_sec",
        "evap_losses_NOT_IMPLEMENTED",
        "gross_water_outflow_rate_vol_per_sec",
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
                value(m.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp])
                for (wl, dep_tmp, arr_tmp) in m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS
                if wl in m.WATER_LINKS_TO_BY_WATER_NODE[wn] and arr_tmp == tmp
            ),
            value(m.Gross_Water_Node_Inflow_Rate_Vol_Per_Sec[wn, tmp]),
            value(
                m.Discharge_Water_to_Powerhouse_Rate_Vol_Per_Sec[wn, tmp]
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            (
                value(m.Spill_Water_Rate_Vol_Per_Sec[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            (
                value(m.Evaporative_Losses[wn, tmp])
                if wn in m.WATER_NODES_W_RESERVOIRS
                else None
            ),
            value(m.Gross_Water_Node_Release_Rate_Vol_per_Sec[wn, tmp]),
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
            "system_water_node_timepoint.csv",
        ),
        sep=",",
        index=True,
    )


def import_results_into_database(
    scenario_id,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    c,
    db,
    results_directory,
    quiet,
):
    import_csv(
        conn=db,
        cursor=c,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        quiet=quiet,
        results_directory=results_directory,
        which_results="system_water_node_timepoint",
    )
