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
    def node_inflow_rate_init(mod, wn, tmp):
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
        initialize=node_inflow_rate_init,
    )

    def node_outflow_rate_init(mod, wn, tmp):
        return sum(
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
            for (wl, dep_tmp, arr_tmp) in mod.WATER_LINK_DEPARTURE_ARRIVAL_TMPS
            if wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn] and dep_tmp == tmp
        )

    m.Gross_Water_Node_Outflow_Rate_Vol_per_Sec = Expression(
        m.WATER_NODES,
        m.TMPS,
        initialize=node_outflow_rate_init,
    )

    # ### Constraints ### #
    def get_total_inflow_for_reservoir_tracking_volunit(mod, wn, tmp):
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

    def get_total_reservoir_release_volunit(mod, wn, tmp):
        outflow_in_tmp = (
            mod.Gross_Reservoir_Release_Rate_Vol_Per_Sec[wn, tmp]
            * 3600
            * mod.hrs_in_tmp[tmp]
        )

        return outflow_in_tmp

    def reservoir_storage_tracking_rule(mod, wn, tmp):
        """ """
        # No constraint in the first timepoint of a linear horizon (no
        # previous timepoints for tracking reservoir levels)
        if check_if_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.water_system_balancing_type
        ) and check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.water_system_balancing_type,
            boundary_type="linear",
        ):
            return Constraint.Skip
        # TODO: add linked horizons
        elif check_if_first_timepoint(
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
            prev_tmp_outflow = None
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
            prev_tmp_inflow = get_total_inflow_for_reservoir_tracking_volunit(
                mod, wn, mod.prev_tmp[tmp, mod.water_system_balancing_type]
            )

            prev_tmp_outflow = get_total_reservoir_release_volunit(
                mod, wn, mod.prev_tmp[tmp, mod.water_system_balancing_type]
            )

        return current_tmp_starting_water_volume == (
            prev_tmp_starting_water_volume + prev_tmp_inflow - prev_tmp_outflow
        )

    m.Reservoir_Storage_Tracking_Constraint = Constraint(
        m.WATER_NODES_W_RESERVOIRS, m.TMPS, rule=reservoir_storage_tracking_rule
    )

    # Set the sum of outflows from the node to be equal to discharge & spill
    # for nodes with storage and to inflow for nodes without storage
    def enforce_mass_balance_outflow_rule(mod, wn, tmp):
        """
        The sum of the flows on all links from this node must equal the
        reservoir release for nodes with reservoirs and total inflows for
        reservoirs without reservoirs. Skip constraint for the last node in the
        network with no out links.

        For linear horizons, the lwater outflows may arrive outside of the
        horizon boundary if travel time is more than hours in the remaining
        timepoints. We still need to enforce outflow constraints (that are
        based on the departure timepoint). These flows have the
        "tmp_outside_horizon" index for the arrival timepoint.
        """
        if [wl for wl in mod.WATER_LINKS_FROM_BY_WATER_NODE[wn]]:
            # For nodes with reservoirs, set to reservoir release
            if wn in mod.WATER_NODES_W_RESERVOIRS:
                return (
                    mod.Gross_Water_Node_Outflow_Rate_Vol_per_Sec[wn, tmp]
                    == mod.Gross_Reservoir_Release_Rate_Vol_Per_Sec[wn, tmp]
                )
            else:
                # For nodes without reservoirs, set to inflow
                return (
                    mod.Gross_Water_Node_Outflow_Rate_Vol_per_Sec[wn, tmp]
                    == mod.Gross_Water_Node_Inflow_Rate_Vol_Per_Sec[wn, tmp]
                )
        else:
            return Constraint.Skip

    m.Water_Node_Outflow_Constraint = Constraint(
        m.WATER_NODES, m.TMPS, rule=enforce_mass_balance_outflow_rule
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
            value(m.Gross_Water_Node_Outflow_Rate_Vol_per_Sec[wn, tmp]),
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
