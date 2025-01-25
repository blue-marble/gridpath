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
Flows across water links.
"""

import csv
import os.path

from pyomo.environ import (
    Set,
    Param,
    NonNegativeReals,
    Var,
    Constraint,
    Any,
    value,
    Expression,
    Boolean,
    PositiveReals,
    Reals,
)

from gridpath.auxiliary.db_interface import directories_to_db_values, import_csv
from gridpath.common_functions import create_results_df
from gridpath.project.common_functions import (
    check_if_boundary_type_and_last_timepoint,
    check_boundary_type,
    check_if_boundary_type_and_first_timepoint,
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
    m.water_link_default_min_flow_vol_per_sec = Param(m.WATER_LINKS, default=0)
    m.allow_water_link_min_flow_violation = Param(
        m.WATER_LINKS, within=Boolean, default=0
    )
    m.min_flow_violation_penalty_cost = Param(
        m.WATER_LINKS, within=NonNegativeReals, default=0
    )
    m.allow_water_link_max_flow_violation = Param(
        m.WATER_LINKS, within=Boolean, default=0
    )
    m.max_flow_violation_penalty_cost = Param(
        m.WATER_LINKS, within=NonNegativeReals, default=0
    )

    # Start with these as params BUT:
    # These are probably not params but expressions with a non-linear
    # relationship to elevation; most of the curves look they can be
    # piecewise linear
    m.min_tmp_flow_vol_per_second = Param(
        m.WATER_LINKS,
        m.TMPS,
        within=NonNegativeReals,
        default=lambda mod, wl, tmp: mod.water_link_default_min_flow_vol_per_sec[wl],
    )
    m.max_tmp_flow_vol_per_second = Param(m.WATER_LINKS, m.TMPS, default=float("inf"))

    # Min and max total flows by horizon
    m.WATER_LINKS_W_BT_HRZ_MIN_FLOW_CONSTRAINT = Set(
        dimen=3, within=m.WATER_LINKS * m.BLN_TYPE_HRZS
    )
    m.WATER_LINKS_W_BT_HRZ_MAX_FLOW_CONSTRAINT = Set(
        dimen=3, within=m.WATER_LINKS * m.BLN_TYPE_HRZS
    )

    m.min_bt_hrz_flow_avg_vol_per_second = Param(
        m.WATER_LINKS_W_BT_HRZ_MIN_FLOW_CONSTRAINT,
        within=NonNegativeReals,
    )

    m.max_bt_hrz_flow_avg_vol_per_second = Param(
        m.WATER_LINKS_W_BT_HRZ_MAX_FLOW_CONSTRAINT,
        within=NonNegativeReals,
    )

    # Set WATER_LINK_DEPARTURE_ARRIVAL_TMPS
    def water_link_departure_arrival_tmp_init(mod):
        wl_dep_arr_tmp = []
        for wl in mod.WATER_LINKS:
            for departure_tmp in mod.TMPS:
                arrival_tmp = determine_future_timepoint(
                    mod=mod,
                    dep_tmp=departure_tmp,
                    time_from_dep_tmp=mod.water_link_flow_transport_time_hours[wl],
                )
                if arrival_tmp is not None:
                    wl_dep_arr_tmp.append((wl, departure_tmp, arrival_tmp))

        return wl_dep_arr_tmp

    m.TMPS_AND_OUTSIDE_HORIZON = Set(initialize=m.TMPS | {"tmp_outside_horizon"})
    m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS = Set(
        dimen=3,
        within=m.WATER_LINKS * m.TMPS * m.TMPS_AND_OUTSIDE_HORIZON,
        initialize=water_link_departure_arrival_tmp_init,
    )

    def departure_tmp_init(mod):
        dep_tmp_dict = {}
        for water_link, dep_tmp, arr_tmp in mod.WATER_LINK_DEPARTURE_ARRIVAL_TMPS:
            dep_tmp_dict[water_link, arr_tmp] = dep_tmp

        return dep_tmp_dict

    m.departure_timepoint = Param(
        m.WATER_LINKS,
        m.TMPS_AND_OUTSIDE_HORIZON,
        default="tmp_outside_horizon",
        within=m.TMPS_AND_OUTSIDE_HORIZON,
        initialize=departure_tmp_init,
    )

    def arrival_tmp_init(mod):
        arr_tmp_dict = {}
        for water_link, dep_tmp, arr_tmp in mod.WATER_LINK_DEPARTURE_ARRIVAL_TMPS:
            arr_tmp_dict[water_link, dep_tmp] = arr_tmp

        return arr_tmp_dict

    m.arrival_timepoint = Param(
        m.WATER_LINKS,
        m.TMPS,
        within=m.TMPS_AND_OUTSIDE_HORIZON,
        initialize=arrival_tmp_init,
    )

    # Ramp limits
    # TODO: remove initialize
    m.WATER_LINK_RAMP_LIMITS = Set(
        dimen=2,
        within=m.WATER_LINKS * Any,
        initialize=[("Newhalem_to_Marblemount", "one_hour_downramp")],
    )
    m.water_link_ramp_limit_up_or_down = Param(
        m.WATER_LINK_RAMP_LIMITS,
        within=[1, -1],
        initialize={("Newhalem_to_Marblemount", "one_hour_downramp"): -1},
    )
    m.water_link_ramp_limit_n_hours = Param(
        m.WATER_LINK_RAMP_LIMITS,
        within=PositiveReals,
        initialize={("Newhalem_to_Marblemount", "one_hour_downramp"): 1},
    )

    # TODO: move to balancing type horizon definition
    m.water_link_ramp_limit_allowed_flow_delta = Param(
        m.WATER_LINK_RAMP_LIMITS,
        within=Reals,
        initialize={("Newhalem_to_Marblemount", "one_hour_downramp"): 500},
    )

    def ramp_limit_tmps_set_init(mod):
        ramp_limit_tmps = []
        for water_link, ramp_limit in mod.WATER_LINK_RAMP_LIMITS:
            for tmp in mod.TMPS:
                arr_tmp = determine_future_timepoint(
                    mod, tmp, mod.water_link_ramp_limit_n_hours[water_link, ramp_limit]
                )
                ramp_limit_tmps.append((water_link, ramp_limit, tmp, arr_tmp))

        print(ramp_limit_tmps)
        return ramp_limit_tmps

    m.WATER_LINK_RAMP_LIMIT_DEP_ARR_TMPS = Set(
        dimen=4,
        within=m.WATER_LINK_RAMP_LIMITS * m.TMPS * m.TMPS_AND_OUTSIDE_HORIZON,
        initialize=ramp_limit_tmps_set_init,
    )

    # ### Variables ### #
    m.Water_Link_Flow_Rate_Vol_per_Sec = Var(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, within=NonNegativeReals
    )

    m.Water_Link_Min_Flow_Violation = Var(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, within=NonNegativeReals
    )
    m.Water_Link_Max_Flow_Violation = Var(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, within=NonNegativeReals
    )

    def min_flow_violation_expression_init(mod, wl, dep_tmp, arr_tmp):
        """

        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        if mod.allow_water_link_min_flow_violation[wl]:
            return mod.Water_Link_Min_Flow_Violation[wl, dep_tmp, arr_tmp]
        else:
            return 0

    m.Water_Link_Min_Flow_Violation_Expression = Expression(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS,
        initialize=min_flow_violation_expression_init,
    )

    def max_flow_violation_expression_init(mod, wl, dep_tmp, arr_tmp):
        """

        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        if mod.allow_water_link_max_flow_violation[wl]:
            return mod.Water_Link_Max_Flow_Violation[wl, dep_tmp, arr_tmp]
        else:
            return 0

    m.Water_Link_Max_Flow_Violation_Expression = Expression(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS,
        initialize=max_flow_violation_expression_init,
    )

    # ### Constraints ### #
    def min_tmp_flow_rule(mod, wl, dep_tmp, arr_tmp):
        return (
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
            + mod.Water_Link_Min_Flow_Violation_Expression[wl, dep_tmp, arr_tmp]
            >= mod.min_tmp_flow_vol_per_second[wl, dep_tmp]
        )

    m.Water_Link_Minimum_Flow_Constraint = Constraint(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, rule=min_tmp_flow_rule
    )

    def max_tmp_flow_rule(mod, wl, dep_tmp, arr_tmp):
        return (
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
            - mod.Water_Link_Max_Flow_Violation_Expression[wl, dep_tmp, arr_tmp]
            <= mod.max_tmp_flow_vol_per_second[wl, dep_tmp]
        )

    m.Water_Link_Maximum_Flow_Constraint = Constraint(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, rule=max_tmp_flow_rule
    )

    def min_total_hrz_flow_constraint_rule(mod, wl, bt, hrz):
        """ """
        return sum(
            mod.Water_Link_Flow_Rate_Vol_per_Sec[
                wl, dep_tmp, mod.arrival_timepoint[wl, dep_tmp]
            ]
            * mod.hrs_in_tmp[dep_tmp]
            for dep_tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
        ) >= sum(
            mod.min_bt_hrz_flow_avg_vol_per_second[wl, bt, hrz] * mod.hrs_in_tmp[tmp]
            for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
        )

    m.Water_Link_Min_Total_Hrz_Flow_Constraint = Constraint(
        m.WATER_LINKS_W_BT_HRZ_MIN_FLOW_CONSTRAINT,
        rule=min_total_hrz_flow_constraint_rule,
    )

    def max_total_hrz_flow_constraint_rule(mod, wl, bt, hrz):
        """ """
        return sum(
            mod.Water_Link_Flow_Rate_Vol_per_Sec[
                wl, dep_tmp, mod.arrival_timepoint[wl, dep_tmp]
            ]
            * mod.hrs_in_tmp[dep_tmp]
            for dep_tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
        ) <= sum(
            mod.max_bt_hrz_flow_avg_vol_per_second[wl, bt, hrz] * mod.hrs_in_tmp[tmp]
            for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
        )

    m.Water_Link_Max_Total_Hrz_Flow_Constraint = Constraint(
        m.WATER_LINKS_W_BT_HRZ_MAX_FLOW_CONSTRAINT,
        rule=max_total_hrz_flow_constraint_rule,
    )

    # Ramp constraints
    def up_ramp_constraint_rule(mod, wl, ramp_limit, tmp, future_tmp):
        if future_tmp == "tmp_outside_horizon":
            return Constraint.Skip
        else:
            return (
                mod.water_link_ramp_limit_up_or_down[wl, ramp_limit]
                * (
                    mod.Water_Link_Flow_Rate_Vol_per_Sec[
                        wl, future_tmp, mod.arrival_timepoint[wl, future_tmp]
                    ]
                    - mod.Water_Link_Flow_Rate_Vol_per_Sec[
                        wl, tmp, mod.arrival_timepoint[wl, tmp]
                    ]
                )
                <= mod.water_link_ramp_limit_allowed_flow_delta[wl, ramp_limit]
            )

    m.Water_Link_Down_Constraint = Constraint(
        m.WATER_LINK_RAMP_LIMIT_DEP_ARR_TMPS, rule=up_ramp_constraint_rule
    )


def determine_future_timepoint(mod, dep_tmp, time_from_dep_tmp):
    """
    USER WARNING: timepoint durations longer than the travel time may create
    issues. You could also see issues if timepoints don't receive any flows
    because of short durations. This functionality is new and not yet
    extensively tested, so proceed with caution.
    """
    # If travel time is less than the hours in the departure timepoint,
    # balancing happens within the departure timepoint
    if time_from_dep_tmp < mod.hrs_in_tmp[dep_tmp]:
        arr_tmp = dep_tmp
    # If this is the last timepoint of a linear horizon, there are no
    # timepoints to check and we'll return 'tmp_outside_horizon'
    elif check_if_boundary_type_and_last_timepoint(
        mod=mod,
        tmp=dep_tmp,
        balancing_type=mod.water_system_balancing_type,
        boundary_type="linear",
    ):
        arr_tmp = "tmp_outside_horizon"
    elif check_if_boundary_type_and_last_timepoint(
        mod=mod,
        tmp=dep_tmp,
        balancing_type=mod.water_system_balancing_type,
        boundary_type="linked",
    ):
        # TODO: add linked
        arr_tmp = None
    else:
        # Otherwise, we check the following timepoints
        # First we'll check the next timepoint of the starting timepoint and
        # start with the duration of the starting timepoint
        arr_tmp = mod.next_tmp[dep_tmp, mod.water_system_balancing_type]
        hours_from_departure_tmp = mod.hrs_in_tmp[dep_tmp]
        while hours_from_departure_tmp < time_from_dep_tmp:
            # If we haven't exceeded the travel time yet, we move on to the next tmp
            # In a 'linear' horizon setting, once we reach the last
            # timepoint of the horizon, we set the arrival timepoint to
            # "tmp_outside_horizon" and break out of the loop
            if check_if_boundary_type_and_last_timepoint(
                mod=mod,
                tmp=arr_tmp,
                balancing_type=mod.water_system_balancing_type,
                boundary_type="linear",
            ):
                arr_tmp = "tmp_outside_horizon"
                break
            # In a 'circular' horizon setting, once we loop back to the
            # departure timepoint again, we break out of the loop since there
            # are no more timepoints to consider (we have already checked all
            # horizon timepoints)
            elif (
                check_boundary_type(
                    mod=mod,
                    tmp=dep_tmp,
                    balancing_type=mod.water_system_balancing_type,
                    boundary_type="circular",
                )
                and arr_tmp == dep_tmp
            ):
                arr_tmp = "tmp_outside_horizon"
                break
            # TODO: only allow the first horizon of a subproblem to have
            #  linked timepoints
            # In a 'linked' horizon setting, once we reach the first
            # timepoint of the horizon, we'll start adding the linked
            # timepoints until we reach the target min time
            elif check_if_boundary_type_and_last_timepoint(
                mod=mod,
                tmp=arr_tmp,
                balancing_type=mod.water_system_balancing_type,
                boundary_type="linked",
            ):
                # TODO: add linked
                arr_tmp = None
                break
            # Otherwise, we move on to the next timepoint and will add that
            # timepoint's duration to hours_from_departure_tmp
            else:
                hours_from_departure_tmp += mod.hrs_in_tmp[arr_tmp]
                arr_tmp = mod.next_tmp[arr_tmp, mod.water_system_balancing_type]

    return arr_tmp


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
            "water_flow_params.tab",
        ),
        param=(
            m.water_link_default_min_flow_vol_per_sec,
            m.allow_water_link_min_flow_violation,
            m.min_flow_violation_penalty_cost,
            m.allow_water_link_max_flow_violation,
            m.max_flow_violation_penalty_cost,
        ),
    )

    tmp_fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "water_flow_tmp_bounds.tab",
    )
    if os.path.exists(tmp_fname):
        data_portal.load(
            filename=tmp_fname,
            param=(m.min_tmp_flow_vol_per_second, m.max_tmp_flow_vol_per_second),
        )

    hrz_min_fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "water_flow_hrz_min_bounds.tab",
    )

    if os.path.exists(hrz_min_fname):
        data_portal.load(
            filename=hrz_min_fname,
            index=m.WATER_LINKS_W_BT_HRZ_MIN_FLOW_CONSTRAINT,
            param=m.min_bt_hrz_flow_avg_vol_per_second,
        )

    hrz_max_fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "water_flow_hrz_max_bounds.tab",
    )

    if os.path.exists(hrz_max_fname):
        data_portal.load(
            filename=hrz_max_fname,
            index=m.WATER_LINKS_W_BT_HRZ_MAX_FLOW_CONSTRAINT,
            param=m.max_bt_hrz_flow_avg_vol_per_second,
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
    c0 = conn.cursor()
    water_flow_params = c0.execute(
        f"""SELECT water_link,
        default_min_flow_vol_per_sec,
        allow_water_link_min_flow_violation,
        min_flow_violation_penalty_cost,
        allow_water_link_max_flow_violation,
        max_flow_violation_penalty_cost
        FROM inputs_system_water_flows
        WHERE water_flow_scenario_id = {subscenarios.WATER_FLOW_SCENARIO_ID}
        AND water_link IN (
                SELECT water_link
                FROM inputs_geography_water_network
                WHERE water_network_scenario_id = 
                {subscenarios.WATER_NETWORK_SCENARIO_ID}
            )
        ;
        """
    )

    c1 = conn.cursor()
    tmp_sql = f"""SELECT water_link, timepoint, 
            min_tmp_flow_vol_per_second, max_tmp_flow_vol_per_second
            FROM inputs_system_water_flows_timepoint_bounds
            WHERE (water_link, water_flow_timepoint_bounds_scenario_id) in (
                SELECT water_link, water_flow_timepoint_bounds_scenario_id
                FROM inputs_system_water_flows
                WHERE water_flow_scenario_id = 
                {subscenarios.WATER_FLOW_SCENARIO_ID}
            )
            AND water_link IN (
                SELECT water_link
                FROM inputs_geography_water_network
                WHERE water_network_scenario_id = 
                {subscenarios.WATER_NETWORK_SCENARIO_ID}
            )
            AND timepoint
            IN (SELECT timepoint
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage})
            ;
            """

    tmp_flow_bounds = c1.execute(tmp_sql)

    hrz_min_sql = f"""SELECT water_link, balancing_type, horizon,
            min_bt_hrz_flow_avg_vol_per_second
            FROM inputs_system_water_flows_horizon_bounds
            WHERE min_bt_hrz_flow_avg_vol_per_second IS NOT NULL
            AND (water_link, water_flow_horizon_bounds_scenario_id) in (
                SELECT water_link, water_flow_horizon_bounds_scenario_id
                FROM inputs_system_water_flows
                WHERE water_flow_scenario_id = 
                {subscenarios.WATER_FLOW_SCENARIO_ID}
            )
            AND water_link IN (
                SELECT water_link
                FROM inputs_geography_water_network
                WHERE water_network_scenario_id = 
                {subscenarios.WATER_NETWORK_SCENARIO_ID}
            )
            AND (balancing_type, horizon)
            IN (SELECT DISTINCT balancing_type, horizon
                FROM inputs_temporal_horizon_timepoints
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                AND subproblem_id = {subproblem}
                )
            ;
            """
    c2 = conn.cursor()
    hrz_min_flow_bounds = c2.execute(hrz_min_sql)

    hrz_max_sql = f"""SELECT water_link, balancing_type, horizon,
            max_bt_hrz_flow_avg_vol_per_second
            FROM inputs_system_water_flows_horizon_bounds
            WHERE max_bt_hrz_flow_avg_vol_per_second IS NOT NULL
            AND (water_link, water_flow_horizon_bounds_scenario_id) in (
                SELECT water_link, water_flow_horizon_bounds_scenario_id
                FROM inputs_system_water_flows
                WHERE water_flow_scenario_id = 
                {subscenarios.WATER_FLOW_SCENARIO_ID}
            )
            AND water_link IN (
                SELECT water_link
                FROM inputs_geography_water_network
                WHERE water_network_scenario_id = 
                {subscenarios.WATER_NETWORK_SCENARIO_ID}
            )
            AND (balancing_type, horizon)
            IN (SELECT DISTINCT balancing_type, horizon
                FROM inputs_temporal_horizon_timepoints
                WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                AND subproblem_id = {subproblem}
                )
            ;
            """
    c3 = conn.cursor()
    hrz_max_flow_bounds = c3.execute(hrz_max_sql)

    return water_flow_params, tmp_flow_bounds, hrz_min_flow_bounds, hrz_max_flow_bounds


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
    water_flow_tmp_bounds.tab file.
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

    water_flow_params, tmp_flow_bounds, hrz_min_flow_bounds, hrz_max_flow_bounds = (
        get_inputs_from_database(
            scenario_id,
            subscenarios,
            db_weather_iteration,
            db_hydro_iteration,
            db_availability_iteration,
            db_subproblem,
            db_stage,
            conn,
        )
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
            "water_flow_params.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "water_link",
                "default_min_flow_vol_per_sec",
                "allow_water_link_min_flow_violation",
                "min_flow_violation_penalty_cost",
                "allow_water_link_max_flow_violation",
                "max_flow_violation_penalty_cost",
            ]
        )

        for row in water_flow_params:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    tmp_water_flow_bounds_list = [row for row in tmp_flow_bounds]
    if tmp_water_flow_bounds_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "water_flow_tmp_bounds.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "water_link",
                    "timepoint",
                    "min_tmp_flow_vol_per_second",
                    "max_tmp_flow_vol_per_second",
                ]
            )

            for row in tmp_water_flow_bounds_list:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)

    hrz_min_flow_bounds_list = [row for row in hrz_min_flow_bounds]
    if hrz_min_flow_bounds_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "water_flow_hrz_min_bounds.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "water_link",
                    "balancing_type",
                    "horizon",
                    "min_bt_hrz_flow_avg_vol_per_second",
                ]
            )

            for row in hrz_min_flow_bounds_list:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)

    hrz_max_flow_bounds_list = [row for row in hrz_max_flow_bounds]
    if hrz_max_flow_bounds_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "water_flow_hrz_max_bounds.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "water_link",
                    "balancing_type",
                    "horizon",
                    "max_bt_hrz_flow_avg_vol_per_second",
                ]
            )

            for row in hrz_max_flow_bounds_list:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)


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
        "water_flow_vol_per_sec",
        "water_flow_min_violation_vol_per_sec",
        "water_flow_max_violation_vol_per_sec",
    ]
    data = [
        [
            wl,
            dep_tmp,
            arr_tmp,
            value(m.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]),
            value(m.Water_Link_Min_Flow_Violation_Expression[wl, dep_tmp, arr_tmp]),
            value(m.Water_Link_Max_Flow_Violation_Expression[wl, dep_tmp, arr_tmp]),
        ]
        for (wl, dep_tmp, arr_tmp) in m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS
    ]
    results_df = create_results_df(
        index_columns=["water_link", "departure_timepoint", "arrival_timepoint"],
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
            "system_water_link_timepoint.csv",
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
        which_results="system_water_link_timepoint",
    )
