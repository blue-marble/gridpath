# Copyright 2021 (c) Crown Copyright, GC.
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

Infinity = float("inf")


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

    # Magnitude of the requirement by reserve zone and timepoint
    # If not specified for a reserve zone - timepoint combination,
    # will default to 0
    # set
    m.INST_PEN_ZONE_BLN_TYPE_TMP = Set(
        dimen=2, within=m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS
    )

    # param
    m.min_instantaneous_penetration_mw = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS,
        within=NonNegativeReals,
        default=0,
    )
    m.max_instantaneous_penetration_mw = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS,
        within=NonNegativeReals,
        default=0,
    )

    # Load zones included in the reserve percentage requirement
    # Set
    m.INST_PEN_ZONE_LZ = Set(
        dimen=2, within=m.INSTANTANEOUS_PENETRATION_ZONES * m.LOAD_ZONES
    )

    # Requirement as percentage of load
    # param
    m.inst_pen_min_percent_load = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES,
        within=PercentFraction,
        default=0,
    )
    m.inst_pen_max_percent_load = Param(
        m.INSTANTANEOUS_PENETRATION_ZONES,
        within=PercentFraction,
        default=1,
    )

    # Projects contributing to zone requirement based on power output in the timepoint
    # and on capacity in the period
    # set
    m.INST_PEN_PRJ_CONTRIBUTION = Set(
        dimen=2, within=m.INSTANTANEOUS_PENETRATION_ZONES * m.PROJECTS
    )

    # param
    m.inst_pen_min_ratio_power_req = Param(
        m.INST_PEN_PRJ_CONTRIBUTION,
        within=NonNegativeReals,
        default=0,
    )
    m.inst_pen_min_ratio_capacity_req = Param(
        m.INST_PEN_PRJ_CONTRIBUTION,
        within=NonNegativeReals,
        default=0,
    )
    m.inst_pen_max_ratio_power_req = Param(
        m.INST_PEN_PRJ_CONTRIBUTION,
        within=NonNegativeReals,
        default=0,
    )
    m.inst_pen_max_ratio_capacity_req = Param(
        m.INST_PEN_PRJ_CONTRIBUTION,
        within=NonNegativeReals,
        default=0,
    )

    def min_instantaneous_penetration_requirement_rule(mod, inst_pen_zone, tmp):
        # If we have a map of reserve zones to load zones, apply the percentage
        # target; if no map provided, the percentage_target is 0
        if mod.INST_PEN_ZONE_LZ:
            percentage_target = sum(
                mod.inst_pen_min_percent_load[inst_pen_zone]
                * mod.static_load_mw[lz, tmp]
                for (_inst_pen_zone, lz) in mod.INSTANTANEOUS_PENETRATION_ZONES
                * mod.LOAD_ZONES
                if _inst_pen_zone == inst_pen_zone
            )
        else:
            percentage_target = 0

        # Project contributions, if any projects in the respective set
        if mod.INST_PEN_PRJ_CONTRIBUTION:
            # Project contributions to requirement based on power output
            prj_pwr_contribution = sum(
                mod.inst_pen_min_ratio_power_req[inst_pen_zone, prj]
                * mod.Power_Provision_MW[prj, tmp]
                for (_inst_pen_zone, prj) in mod.INST_PEN_PRJ_CONTRIBUTION
                if _inst_pen_zone == inst_pen_zone
                if (prj, tmp) in mod.PRJ_OPR_TMPS
            )

            # Project contributions to requirement based on (available) capacity
            # We are not holding the extra reserves when projects are unavailable
            prj_cap_contribution = sum(
                mod.inst_pen_min_ratio_capacity_req[inst_pen_zone, prj]
                * mod.Capacity_MW[prj, mod.period[tmp]]
                * mod.Availability_Derate[prj, tmp]
                for (_inst_pen_zone, prj) in mod.INST_PEN_PRJ_CONTRIBUTION
                if _inst_pen_zone == inst_pen_zone
                if (prj, tmp) in mod.PRJ_OPR_TMPS
            )
        else:
            prj_pwr_contribution = 0
            prj_cap_contribution = 0

        return (
            mod.min_instantaneous_penetration_mw[inst_pen_zone, tmp]
            + percentage_target
            + prj_pwr_contribution
            + prj_cap_contribution
        )

    m.Inst_Pen_Requirement_min = Expression(
        m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS,
        rule=min_instantaneous_penetration_requirement_rule,
    )

    def max_instantaneous_penetration_requirement_rule(mod, inst_pen_zone, tmp):
        # If we have a map of reserve zones to load zones, apply the percentage
        # target; if no map provided, the percentage_target is 0
        if mod.INST_PEN_ZONE_LZ:
            percentage_target = sum(
                mod.inst_pen_max_percent_load[inst_pen_zone]
                * mod.static_load_mw[lz, tmp]
                for (_inst_pen_zone, lz) in mod.INSTANTANEOUS_PENETRATION_ZONES
                * mod.LOAD_ZONES
                if _inst_pen_zone == inst_pen_zone
            )
        else:
            percentage_target = 0

        # Project contributions, if any projects in the respective set
        if mod.INST_PEN_PRJ_CONTRIBUTION:
            # Project contributions to requirement based on power output
            prj_pwr_contribution = sum(
                mod.inst_pen_max_ratio_power_req[inst_pen_zone, prj]
                * mod.Power_Provision_MW[prj, tmp]
                for (_inst_pen_zone, prj) in mod.INST_PEN_PRJ_CONTRIBUTION
                if _inst_pen_zone == inst_pen_zone
                if (prj, tmp) in mod.PRJ_OPR_TMPS
            )

            # Project contributions to requirement based on (available) capacity
            # We are not holding the extra reserves when projects are unavailable
            prj_cap_contribution = sum(
                mod.inst_pen_max_ratio_capacity_req[inst_pen_zone, prj]
                * mod.Capacity_MW[prj, mod.period[tmp]]
                * mod.Availability_Derate[prj, tmp]
                for (_inst_pen_zone, prj) in mod.INST_PEN_PRJ_CONTRIBUTION
                if _inst_pen_zone == inst_pen_zone
                if (prj, tmp) in mod.PRJ_OPR_TMPS
            )
        else:
            prj_pwr_contribution = 0
            prj_cap_contribution = 0

        return (
            mod.max_instantaneous_penetration_mw[inst_pen_zone, tmp]
            + percentage_target
            + prj_pwr_contribution
            + prj_cap_contribution
        )

    m.Inst_Pen_Requirement_max = Expression(
        m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS,
        rule=max_instantaneous_penetration_requirement_rule,
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

    input_dir = os.path.join(scenario_directory, subproblem, stage, "inputs")

    # Load the targets by timpoint
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "instantaneous_penetration_tmp_requirement.tab",
        ),
        index=m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS,
        param=(
            m.min_instantaneous_penetration_mw,
            m.max_instantaneous_penetration_mw,
        ),
    )

    # If we have a RPS zone to load zone map input file, load it and the
    # percent requirement; otherwise, initialize the set as an empty list (
    # the param defaults to 0)

    map_filename = os.path.join(input_dir, "instantaneous_penetration_percent_map.tab")
    if os.path.exists(map_filename):
        data_portal.load(filename=map_filename, set=m.INST_PEN_ZONE_LZ)

        data_portal.load(
            filename=os.path.join(
                input_dir, "instantaneous_penetration_percent_requirement.tab"
            ),
            index=m.INSTANTANEOUS_PENETRATION_ZONES,
            param=(m.inst_pen_min_percent_load, m.inst_pen_max_percent_load),
        )

    else:
        data_portal.data()["INST_PEN_ZONE_LZ"] = {None: []}

    # If we have a project contributions file, load it into the respective
    prj_contr_filename = os.path.join(
        input_dir, "instantaneous_penetration_requirement_project_contributions.tab"
    )
    if os.path.exists(prj_contr_filename):
        data_portal.load(
            filename=prj_contr_filename,
            index=m.INST_PEN_PRJ_CONTRIBUTION,
            param=(
                m.inst_pen_min_ratio_power_req,
                m.inst_pen_min_ratio_capacity_req,
                m.inst_pen_max_ratio_power_req,
                m.inst_pen_max_ratio_capacity_req,
            ),
        )
    else:
        data_portal.data()["INST_PEN_PRJ_CONTRIBUTION"] = {None: []}


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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    tmp_req = c.execute(
        """SELECT instantaneous_penetration_zone, timepoint, min_instantaneous_penetration_mw, 
            max_instantaneous_penetration_mw
        FROM inputs_system_instantaneous_penetration
        INNER JOIN
        (SELECT stage_id, timepoint
        FROM inputs_temporal
        WHERE temporal_scenario_id = {temporal_scenario_id}
        AND subproblem_id = {subproblem}
        AND stage_id = {stage}) as relevant_timepoints
        USING (stage_id, timepoint)
        INNER JOIN
        (SELECT instantaneous_penetration_zone
        FROM inputs_geography_instantaneous_penetration_zones
        WHERE instantaneous_penetration_zone_scenario_id = {instantaneous_penetration_zone_subscenario_id}) as relevant_bas
        USING (instantaneous_penetration_zone)
        WHERE instantaneous_penetration_scenario_id = {instantaneous_penetration_req_subscenario_id}
        AND stage_id = {stage}
        """.format(
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem=subproblem,
            stage=stage,
            instantaneous_penetration_zone_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_ZONE_SCENARIO_ID,
            instantaneous_penetration_req_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_SCENARIO_ID,
        )
    )

    c2 = conn.cursor()
    # Get any percentage requirement
    percentage_req = c2.execute(
        """
        SELECT instantaneous_penetration_zone, min_percent_load, max_percent_load
        FROM inputs_system_instantaneous_penetration_percent
        JOIN
        (SELECT instantaneous_penetration_zone
        FROM inputs_geography_instantaneous_penetration_zones
        WHERE instantaneous_penetration_zone_scenario_id = {instantaneous_penetration_zone_subscenario_id}) as relevant_bas
        USING (instantaneous_penetration_zone)
        WHERE instantaneous_penetration_scenario_id = {instantaneous_penetration_req_subscenario_id}
        AND stage_id = {stage}
        """.format(
            instantaneous_penetration_zone_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_ZONE_SCENARIO_ID,
            instantaneous_penetration_req_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_SCENARIO_ID,
            stage=stage,
        )
    )

    # Get any reserve zone to load zone mapping for the percent target
    c3 = conn.cursor()
    lz_mapping = c3.execute(
        """
        SELECT instantaneous_penetration_zone, load_zone
        FROM inputs_system_instantaneous_penetration_percent_lz_map
        JOIN
        (SELECT instantaneous_penetration_zone
        FROM inputs_geography_instantaneous_penetration_zones
        WHERE instantaneous_penetration_zone_scenario_id = {instantaneous_penetration_zone_subscenario_id}) as relevant_bas
        USING (instantaneous_penetration_zone)
        WHERE instantaneous_penetration_scenario_id = {instantaneous_penetration_req_subscenario_id}
        """.format(
            instantaneous_penetration_zone_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_ZONE_SCENARIO_ID,
            instantaneous_penetration_req_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_SCENARIO_ID,
        )
    )

    # Get any project contributions to the magnitude of the reserve requirement
    c4 = conn.cursor()
    project_contributions = c4.execute(
        """
        SELECT instantaneous_penetration_zone, project, min_ratio_power_req, min_ratio_capacity_req, 
        max_ratio_power_req, max_ratio_capacity_req
        FROM inputs_system_instantaneous_penetration_project
        JOIN (
        SELECT instantaneous_penetration_zone
        FROM inputs_geography_instantaneous_penetration_zones
        WHERE instantaneous_penetration_zone_scenario_id = {instantaneous_penetration_zone_subscenario_id}) as relevant_bas
        USING (instantaneous_penetration_zone)
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
        WHERE instantaneous_penetration_scenario_id = {instantaneous_penetration_req_subscenario_id}
        AND stage_id = {stage}
        """.format(
            instantaneous_penetration_zone_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_ZONE_SCENARIO_ID,
            instantaneous_penetration_req_subscenario_id=subscenarios.INSTANTANEOUS_PENETRATION_SCENARIO_ID,
            scenario_id=scenario_id,
            stage=stage,
        )
    )

    return tmp_req, percentage_req, lz_mapping, project_contributions


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
    # spinning_reserves = get_inputs_from_database(
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
    instantaneous_penetration_requirement.tab file.
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

    tmp_req, percent_req, percent_map, project_contributions = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
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
    timepoint_req = tmp_req.fetchall()
    if timepoint_req:
        with open(
            os.path.join(inputs_dir, "instantaneous_penetration_tmp_requirement.tab"),
            "w",
            newline="",
        ) as tmp_req_file:
            writer = csv.writer(tmp_req_file, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "instantaneous_penetration_zone",
                    "timepoint",
                    "min_instantaneous_penetration_mw",
                    "max_instantaneous_penetration_mw",
                ]
            )

            for ipz, tmp, min_ip, max_ip in timepoint_req:
                if min_ip is None:
                    min_ip = "."
                if max_ip is None:
                    max_ip = "."
                writer.writerow([ipz, tmp, min_ip, max_ip])

    # Write the percent requirement files only if there's a mapping
    lz_map_list = [row for row in percent_map]

    if lz_map_list:
        with open(
            os.path.join(
                inputs_dir, "instantaneous_penetration_percent_requirement.tab"
            ),
            "w",
            newline="",
        ) as percent_req_file:
            writer = csv.writer(percent_req_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "instantaneous_penetration_zone",
                    "min_percent_load",
                    "max_percent_load",
                ]
            )
            for ipz, min_ip, max_ip in percent_req:
                if min_ip is None:
                    min_ip = "."
                if max_ip is None:
                    max_ip = "."
                writer.writerow([ipz, min_ip, max_ip])

        with open(
            os.path.join(inputs_dir, "instantaneous_penetration_percent_map.tab"),
            "w",
            newline="",
        ) as percent_map_file:
            writer = csv.writer(percent_map_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["instantaneous_penetration_zone", "load_zone"])

            for row in lz_map_list:
                writer.writerow(row)

    # Project contributions to the magnitude requirement
    project_contributions = project_contributions.fetchall()

    prj_contributions = False
    for ip, prj, min_pwr, max_pwr, min_cap, max_cap in project_contributions:
        if (
            min_pwr is not None
            or max_pwr is not None
            or min_cap is not None
            or max_cap is not None
        ):
            prj_contributions = True

    if prj_contributions:
        with open(
            os.path.join(
                inputs_dir,
                "instantaneous_penetration_requirement_project_contributions.tab",
            ),
            "w",
            newline="",
        ) as prj_file:
            writer = csv.writer(prj_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "instantaneous_penetration_zone",
                    "project",
                    "min_ratio_power_req",
                    "min_ratio_capacity_req",
                    "max_ratio_power_req",
                    "max_ratio_capacity_req",
                ]
            )
            for ip, prj, min_pwr, max_pwr, min_cap, max_cap in project_contributions:
                if min_pwr is None:
                    min_pwr = "."
                if max_pwr is None:
                    max_pwr = "."
                if min_cap is None:
                    min_cap = "."
                if max_cap is None:
                    max_cap = "."
                writer.writerow([ip, prj, min_pwr, max_pwr, min_cap, max_cap])
