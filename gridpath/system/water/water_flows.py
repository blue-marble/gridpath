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
    # Start with these as params BUT:
    # These are probably not params but expressions with a non-linear
    # relationship to elevation; most of the curves look they can be
    # piecewise linear
    m.min_flow_vol_per_second = Param(
        m.WATER_LINKS, m.TMPS, within=NonNegativeReals, default=0
    )
    m.max_flow_vol_per_second = Param(m.WATER_LINKS, m.TMPS, default=float("inf"))

    # Set WATER_LINK_DEPARTURE_ARRIVAL_TMPS
    def water_link_departure_arrival_tmp_init(mod):
        wl_dep_arr_tmp = []
        for wl in mod.WATER_LINKS:
            for departure_tmp in mod.TMPS:
                arrival_tmp = determine_arrival_timepoint(
                    mod=mod,
                    dep_tmp=departure_tmp,
                    travel_time_hours=mod.water_link_flow_transport_time_hours[wl],
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
    def min_flow_rule(mod, wl, dep_tmp, arr_tmp):
        return (
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
            + mod.Water_Link_Min_Flow_Violation_Expression[wl, dep_tmp, arr_tmp]
            >= mod.min_flow_vol_per_second[wl, dep_tmp]
        )

    m.Water_Link_Minimum_Flow_Constraint = Constraint(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, rule=min_flow_rule
    )

    def max_flow_rule(mod, wl, dep_tmp, arr_tmp):
        return (
            mod.Water_Link_Flow_Rate_Vol_per_Sec[wl, dep_tmp, arr_tmp]
            - mod.Water_Link_Max_Flow_Violation_Expression[wl, dep_tmp, arr_tmp]
            <= mod.max_flow_vol_per_second[wl, dep_tmp]
        )

    m.Water_Link_Maximum_Flow_Constraint = Constraint(
        m.WATER_LINK_DEPARTURE_ARRIVAL_TMPS, rule=max_flow_rule
    )


def determine_arrival_timepoint(mod, dep_tmp, travel_time_hours):
    # If travel time is less than the hours in the departure timepoint, we stay
    # in the same timepoint
    if travel_time_hours < mod.hrs_in_tmp[dep_tmp]:
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
        while hours_from_departure_tmp < travel_time_hours:
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
    fname = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "water_flow_bounds.tab",
    )
    if os.path.exists(fname):
        data_portal.load(
            filename=fname,
            param=(m.min_flow_vol_per_second, m.max_flow_vol_per_second),
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
    water_flows = c.execute(
        f"""SELECT water_link, timepoint, 
            min_flow_vol_per_second, max_flow_vol_per_second
            FROM inputs_system_water_flows
            WHERE water_flow_scenario_id = 
            {subscenarios.WATER_FLOW_SCENARIO_ID}
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
            AND hydro_iteration = {hydro_iteration}
            ;
            """
    )

    return water_flows


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

    water_flows = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    water_flow_bounds_list = [row for row in water_flows]
    if water_flow_bounds_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "water_flow_bounds.tab",
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
                    "min_flow_vol_per_second",
                    "max_flow_vol_per_second",
                ]
            )

            for row in water_flow_bounds_list:
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
