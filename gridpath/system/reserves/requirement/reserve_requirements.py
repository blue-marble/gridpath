# Copyright 2016-2023 Blue Marble Analytics LLC.
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

import csv
import os.path
from pyomo.environ import Param, Set, NonNegativeReals, PercentFraction, Expression

from gridpath.auxiliary.db_interface import directories_to_db_values


def generic_add_model_components(
    m,
    d,
    reserve_zone_set,
    reserve_requirement_tmp_param,
    reserve_requirement_percent_param,
    reserve_zone_load_zone_set,
    ba_prj_req_contribution_set,
    prj_power_param,
    prj_capacity_param,
    reserve_requirement_expression,
):
    """
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_requirement_tmp_param:
    :param reserve_requirement_percent_param:
    :param reserve_zone_load_zone_set:
    :param ba_prj_req_contribution_set:
    :param prj_power_param:
    :param prj_capacity_param:
    :param reserve_requirement_expression:
    :return:

    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
    1) the reserve requirement by zone and timepoint, if any
    2) the reserve requirement as a percent of load and map for which load
    zones' load to consider
    3) the contributions to the reserve requirement from projects: there are two
    types of these contributions, those based on the power output in the timepoint
    and those based on the project capacity.
    """

    # Magnitude of the requirement by reserve zone and timepoint
    # If not specified for a reserve zone - timepoint combination,
    # will default to 0
    setattr(
        m,
        reserve_requirement_tmp_param,
        Param(getattr(m, reserve_zone_set), m.TMPS, within=NonNegativeReals, default=0),
    )

    # Requirement as percentage of load
    setattr(
        m,
        reserve_requirement_percent_param,
        Param(getattr(m, reserve_zone_set), within=PercentFraction, default=0),
    )

    # Load zones included in the reserve percentage requirement
    setattr(
        m,
        reserve_zone_load_zone_set,
        Set(dimen=2, within=getattr(m, reserve_zone_set) * m.LOAD_ZONES),
    )

    # Projects contributing to BA requirement based on power output in the timepoint
    # and on capacity in the period
    setattr(
        m,
        ba_prj_req_contribution_set,
        Set(dimen=2, within=getattr(m, reserve_zone_set) * m.PROJECTS),
    )

    setattr(
        m,
        prj_power_param,
        Param(
            getattr(m, ba_prj_req_contribution_set), within=PercentFraction, default=0
        ),
    )

    setattr(
        m,
        prj_capacity_param,
        Param(
            getattr(m, ba_prj_req_contribution_set), within=PercentFraction, default=0
        ),
    )

    def reserve_requirement_rule(mod, reserve_zone, tmp):
        # If we have a map of reserve zones to load zones, apply the percentage
        # target; if no map provided, the percentage_target is 0
        if getattr(mod, reserve_zone_load_zone_set):
            percentage_target = sum(
                getattr(mod, reserve_requirement_percent_param)[reserve_zone]
                * mod.static_load_mw[lz, tmp]
                for (_reserve_zone, lz) in getattr(mod, reserve_zone_load_zone_set)
                if _reserve_zone == reserve_zone
            )
        else:
            percentage_target = 0

        # Project contributions, if any projects in the respective set
        if getattr(mod, ba_prj_req_contribution_set):
            # Project contributions to requirement based on power output
            prj_pwr_contribution = sum(
                getattr(mod, prj_power_param)[reserve_zone, prj]
                * mod.Power_Provision_MW[prj, tmp]
                for (_reserve_zone, prj) in getattr(mod, ba_prj_req_contribution_set)
                if _reserve_zone == reserve_zone
                if (prj, tmp) in mod.PRJ_OPR_TMPS
            )

            # Project contributions to requirement based on (available) capacity
            # We are not holding the extra reserves when projects are unavailable
            prj_cap_contribution = sum(
                getattr(mod, prj_capacity_param)[reserve_zone, prj]
                * mod.Capacity_MW[prj, mod.period[tmp]]
                * mod.Availability_Derate[prj, tmp]
                for (_reserve_zone, prj) in getattr(mod, ba_prj_req_contribution_set)
                if _reserve_zone == reserve_zone
                if (prj, tmp) in mod.PRJ_OPR_TMPS
            )
        else:
            prj_pwr_contribution = 0
            prj_cap_contribution = 0

        return (
            getattr(mod, reserve_requirement_tmp_param)[reserve_zone, tmp]
            + percentage_target
            + prj_pwr_contribution
            + prj_cap_contribution
        )

    setattr(
        m,
        reserve_requirement_expression,
        Expression(
            getattr(m, reserve_zone_set) * m.TMPS, rule=reserve_requirement_rule
        ),
    )


def generic_load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    reserve_requirement_param,
    reserve_zone_load_zone_set,
    reserve_requirement_percent_param,
    ba_prj_req_contribution_set,
    prj_power_param,
    prj_capacity_param,
    reserve_type,
):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param reserve_requirement_param:
    :param reserve_zone_load_zone_set:
    :param reserve_requirement_percent_param
    :param ba_prj_req_contribution_set
    :param prj_power_param
    :param prj_capacity_param
    :param reserve_type:
    :return:
    """
    input_dir = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
    )

    # Load by-tmp requriement if input file was written
    by_tmp_req_filename = os.path.join(
        input_dir, "{}_tmp_requirement.tab".format(reserve_type)
    )
    if os.path.exists(by_tmp_req_filename):
        tmp_params_to_load = (
            (
                getattr(m, reserve_requirement_param),
                m.frequency_response_requirement_partial_mw,
            )
            if reserve_type == "frequency_response"
            else getattr(m, reserve_requirement_param)
        )
        data_portal.load(filename=by_tmp_req_filename, param=tmp_params_to_load)

    # If we have a RPS zone to load zone map input file, load it and the
    # percent requirement; otherwise, initialize the set as an empty list (
    # the param defaults to 0)
    map_filename = os.path.join(input_dir, "{}_percent_map.tab".format(reserve_type))
    if os.path.exists(map_filename):
        data_portal.load(
            filename=map_filename, set=getattr(m, reserve_zone_load_zone_set)
        )
        data_portal.load(
            filename=os.path.join(
                input_dir, "{}_percent_requirement.tab".format(reserve_type)
            ),
            param=getattr(m, reserve_requirement_percent_param),
        )
    else:
        data_portal.data()[reserve_zone_load_zone_set] = {None: []}

    # If we have a project contributions file, load it into the respective
    prj_contr_filename = os.path.join(
        input_dir, "{}_requirement_project_contributions.tab".format(reserve_type)
    )
    if os.path.exists(prj_contr_filename):
        data_portal.load(
            filename=prj_contr_filename,
            index=getattr(m, ba_prj_req_contribution_set),
            param=(getattr(m, prj_power_param), getattr(m, prj_capacity_param)),
        )
    else:
        data_portal.data()[ba_prj_req_contribution_set] = {None: []}


def generic_get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
    reserve_type,
    reserve_type_ba_subscenario_id,
    reserve_type_req_subscenario_id,
):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :param reserve_type:
    :param reserve_type_ba_subscenario_id:
    :param reserve_type_req_subscenario_id:
    :return:
    """

    c = conn.cursor()

    partial_freq_resp_extra_column = (
        ", frequency_response_partial_mw"
        if reserve_type == "frequency_response"
        else ""
    )

    tmp_req = c.execute(
        """SELECT {reserve_type}_ba, timepoint, {reserve_type}_mw{partial_freq_resp_extra_column}
        FROM inputs_system_{reserve_type}
        INNER JOIN
        (SELECT stage_id, timepoint
        FROM inputs_temporal
        WHERE temporal_scenario_id = {temporal_scenario_id}
        AND subproblem_id = {subproblem}
        AND stage_id = {stage}) as relevant_timepoints
        USING (stage_id, timepoint)
        INNER JOIN
        (SELECT {reserve_type}_ba
        FROM inputs_geography_{reserve_type}_bas
        WHERE {reserve_type}_ba_scenario_id = {reserve_type_ba_subscenario_id}) as relevant_bas
        USING ({reserve_type}_ba)
        WHERE {reserve_type}_scenario_id = {reserve_type_req_subscenario_id}
        AND stage_id = {stage}
        """.format(
            reserve_type=reserve_type,
            partial_freq_resp_extra_column=partial_freq_resp_extra_column,
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem=subproblem,
            stage=stage,
            reserve_type_ba_subscenario_id=reserve_type_ba_subscenario_id,
            reserve_type_req_subscenario_id=reserve_type_req_subscenario_id,
        )
    )

    c2 = conn.cursor()
    # Get any percentage requirement
    percentage_req = c2.execute(
        """
        SELECT {reserve_type}_ba, percent_load_req
        FROM inputs_system_{reserve_type}_percent
        JOIN
        (SELECT {reserve_type}_ba
        FROM inputs_geography_{reserve_type}_bas
        WHERE {reserve_type}_ba_scenario_id = {reserve_type_ba_subscenario_id}) as relevant_bas
        USING ({reserve_type}_ba)
        WHERE {reserve_type}_scenario_id = {reserve_type_req_subscenario_id}
        AND stage_id = {stage}
        """.format(
            reserve_type=reserve_type,
            reserve_type_ba_subscenario_id=reserve_type_ba_subscenario_id,
            reserve_type_req_subscenario_id=reserve_type_req_subscenario_id,
            stage=stage,
        )
    )

    # Get any reserve zone to load zone mapping for the percent target
    c3 = conn.cursor()
    lz_mapping = c3.execute(
        """
        SELECT {}_ba, load_zone
        FROM inputs_system_{}_percent_lz_map
        JOIN
        (SELECT {}_ba
        FROM inputs_geography_{}_bas
        WHERE {}_ba_scenario_id = {}) as relevant_bas
        USING ({}_ba)
        WHERE {}_scenario_id = {}
        """.format(
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type_ba_subscenario_id,
            reserve_type,
            reserve_type,
            reserve_type_req_subscenario_id,
        )
    )

    # Get any project contributions to the magnitude of the reserve requirement
    c4 = conn.cursor()
    project_contributions = c4.execute(
        """
        SELECT {reserve_type}_ba, project, percent_power_req, 
        percent_capacity_req
        FROM inputs_system_{reserve_type}_project
        JOIN (
        SELECT {reserve_type}_ba
        FROM inputs_geography_{reserve_type}_bas
        WHERE {reserve_type}_ba_scenario_id = {reserve_type_ba_subscenario_id}
        ) as relevant_bas
        USING ({reserve_type}_ba)
        JOIN (
        SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = (
                SELECT project_portfolio_scenario_id
                FROM scenarios
                WHERE scenario_id = {scenario_id}
            )
        ) as relevant_prj
        USING (project)
        WHERE {reserve_type}_scenario_id = {reserve_type_req_subscenario_id}
        AND stage_id = {stage}
        """.format(
            reserve_type=reserve_type,
            reserve_type_ba_subscenario_id=reserve_type_ba_subscenario_id,
            scenario_id=scenario_id,
            reserve_type_req_subscenario_id=reserve_type_req_subscenario_id,
            stage=stage,
        )
    )

    return tmp_req, percentage_req, lz_mapping, project_contributions


def generic_write_model_inputs(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    timepoint_req,
    percent_req,
    percent_map,
    project_contributions,
    reserve_type,
):
    """
    Get inputs from database and write out the model input
    lf_reserves_down_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subproblem:
    :param stage:
    :param timepoint_req:
    :param percent_req:
    :param percent_map:
    :param project_contributions:
    :param reserve_type:
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

    inputs_dir = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
    )

    # Write the by-timepoint requirement file if by-tmp requirement specified
    timepoint_req = timepoint_req.fetchall()
    if timepoint_req:
        with open(
            os.path.join(inputs_dir, "{}_tmp_requirement.tab".format(reserve_type)),
            "w",
            newline="",
        ) as tmp_req_file:
            writer = csv.writer(tmp_req_file, delimiter="\t", lineterminator="\n")

            # Write header
            extra_column = (
                ["partial_requirement"] if reserve_type == "frequency_response" else []
            )
            writer.writerow(["ba", "timepoint", "requirement"] + extra_column)

            for row in timepoint_req:
                writer.writerow(row)

    # Write the percent requirement files only if there's a mapping
    ba_lz_map_list = [row for row in percent_map]

    if ba_lz_map_list:
        with open(
            os.path.join(inputs_dir, "{}_percent_requirement.tab".format(reserve_type)),
            "w",
            newline="",
        ) as percent_req_file:
            writer = csv.writer(percent_req_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["ba", "percent_requirement"])

            for row in percent_req:
                writer.writerow(row)

        with open(
            os.path.join(inputs_dir, "{}_percent_map.tab".format(reserve_type)),
            "w",
            newline="",
        ) as percent_map_file:
            writer = csv.writer(percent_map_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["ba", "load_zone"])

            for row in ba_lz_map_list:
                writer.writerow(row)

    # Project contributions to the magnitude requirement
    project_contributions = project_contributions.fetchall()

    prj_contributions = False
    for ba, prj, pwr, cap in project_contributions:
        if pwr is not None or cap is not None:
            prj_contributions = True

    if prj_contributions:
        with open(
            os.path.join(
                inputs_dir,
                "{}_requirement_project_contributions.tab".format(reserve_type),
            ),
            "w",
            newline="",
        ) as prj_file:
            writer = csv.writer(prj_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["ba", "project", "percent_power_req", "percent_capacity_req"]
            )
            for ba, prj, pwr, cap in project_contributions:
                if pwr is None:
                    pwr = "."
                if cap is None:
                    cap = "."
                writer.writerow([ba, prj, pwr, cap])
