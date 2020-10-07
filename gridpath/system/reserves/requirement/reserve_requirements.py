#!/usr/bin/env python
# Copyright 2016-2020 Blue Marble Analytics LLC.
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
from pyomo.environ import Param, Set, NonNegativeReals, PercentFraction, \
    Expression


def generic_add_model_components(
    m,
    d,
    reserve_zone_set,
    reserve_requirement_tmp_param,
    reserve_requirement_percent_param,
    reserve_zone_load_zone_set,
    reserve_requirement_expression
):
    """
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_requirement_tmp_param:
    :param reserve_requirement_percent_param:
    :param reserve_zone_load_zone_set:
    :param reserve_requirement_expression:
    :return:

    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
    1) the reserve requirement by zone and timepoint, if any
    2) the reserve requirement as a percent of load and map for which load
    zones' load to consider.
    """

    # Magnitude of the requirement by reserve zone and timepoint
    # If not specified for a reserve zone - timepoint combination,
    # will default to 0
    setattr(m, reserve_requirement_tmp_param,
            Param(getattr(m, reserve_zone_set), m.TMPS,
                  within=NonNegativeReals,
                  default=0)
            )

    # Requirement as percentage of load
    setattr(m, reserve_requirement_percent_param,
            Param(getattr(m, reserve_zone_set),
                  within=PercentFraction,
                  default=0)
            )

    # Load zones included in the reserve percentage requirement
    setattr(m, reserve_zone_load_zone_set,
            Set(dimen=2,
                within=getattr(m, reserve_zone_set) * m.LOAD_ZONES
                )
            )

    def reserve_requirement_rule(mod, reserve_zone, tmp):
        # If we have a map of reserve zones to load zones, apply the percentage
        # target; if no map provided, the percentage_target is 0
        if getattr(mod, reserve_zone_load_zone_set):
            percentage_target = sum(
                getattr(mod, reserve_requirement_percent_param)[reserve_zone]
                * mod.static_load_mw[lz, tmp]
                for (_reserve_zone, lz)
                in getattr(mod, reserve_zone_load_zone_set)
                if _reserve_zone == reserve_zone
            )
        else:
            percentage_target = 0

        return \
            getattr(mod, reserve_requirement_tmp_param)[reserve_zone, tmp] \
            + percentage_target

    setattr(m, reserve_requirement_expression,
            Expression(getattr(m, reserve_zone_set) * m.TMPS,
                       rule=reserve_requirement_rule)
            )


def generic_load_model_data(
        m, d, data_portal, scenario_directory, subproblem, stage,
        reserve_requirement_param, reserve_zone_load_zone_set,
        reserve_requirement_percent_param,
        reserve_type
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
    :param reserve_type:
    :return:
    """
    input_dir = os.path.join(
        scenario_directory, str(subproblem), str(stage), "inputs")

    # Load by-tmp requriement if input file was written
    by_tmp_req_filename = os.path.join(
        input_dir,
        "{}_tmp_requirement.tab".format(reserve_type)
    )
    if os.path.exists(by_tmp_req_filename):
        tmp_params_to_load = \
            (getattr(m, reserve_requirement_param),
             m.frequency_response_requirement_partial_mw) \
            if reserve_type == "frequency_response" \
            else getattr(m, reserve_requirement_param)
        data_portal.load(
            filename=by_tmp_req_filename,
            param=tmp_params_to_load
        )

    # If we have a RPS zone to load zone map input file, load it and the
    # percent requirement; otherwise, initialize the set as an empty list (
    # the param defaults to 0)
    map_filename = os.path.join(
        input_dir,
        "{}_percent_map.tab".format(reserve_type)
    )
    if os.path.exists(map_filename):
        data_portal.load(
            filename=map_filename,
            set=getattr(m, reserve_zone_load_zone_set)
        )
        data_portal.load(
            filename=os.path.join(
                input_dir, "{}_percent_requirement.tab".format(reserve_type)
            ),
            param=getattr(m, reserve_requirement_percent_param)
        )
    else:
        data_portal.data()[reserve_zone_load_zone_set] = {None: []}


def generic_get_inputs_from_database(
    scenario_id, subscenarios, subproblem, stage, conn, reserve_type,
    reserve_type_ba_subscenario_id, reserve_type_req_subscenario_id
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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    partial_freq_resp_extra_column = \
        ", frequency_response_partial_mw" \
        if reserve_type == "frequency_response" else ""

    tmp_req = c.execute(
        """SELECT {}_ba, timepoint, {}_mw{}
        FROM inputs_system_{}
        INNER JOIN
        (SELECT timepoint
        FROM inputs_temporal
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT {}_ba
        FROM inputs_geography_{}_bas
        WHERE {}_ba_scenario_id = {}) as relevant_bas
        USING ({}_ba)
        WHERE {}_scenario_id = {}
        AND stage_id = {}
        """.format(
            reserve_type,
            reserve_type,
            partial_freq_resp_extra_column,
            reserve_type,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type_ba_subscenario_id,
            reserve_type,
            reserve_type,
            reserve_type_req_subscenario_id,
            stage
        )
    )

    c2 = conn.cursor()
    # Get any percentage requirement
    percentage_req = c2.execute("""
        SELECT {}_ba, percent_load_req
        FROM inputs_system_{}_percent
        WHERE {}_scenario_id = {}
        """.format(
        reserve_type,
        reserve_type,
        reserve_type,
        reserve_type_req_subscenario_id
    )
    )

    # Get any reserve zone to load zone mapping for the percent target
    c3 = conn.cursor()
    lz_mapping = c3.execute("""
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
            reserve_type_req_subscenario_id
        )
    )

    return tmp_req, percentage_req, lz_mapping


def generic_write_model_inputs(
    scenario_directory, subproblem, stage,
    timepoint_req, percent_req, percent_map, reserve_type
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
    :param reserve_type:
    :return:
    """
    inputs_dir = os.path.join(
        scenario_directory, str(subproblem), str(stage), "inputs"
    )

    # Write the by-timepoint requirement file if by-tmp requirement specified
    timepoint_req = timepoint_req.fetchall()
    if timepoint_req:
        with open(os.path.join(inputs_dir,
                               "{}_tmp_requirement.tab".format(reserve_type)
                               ),
                  "w", newline=""
                  ) as tmp_req_file:
            writer = csv.writer(tmp_req_file, delimiter="\t", lineterminator="\n")

            # Write header
            extra_column = \
                ["partial_requirement"] \
                if reserve_type == "frequency_response" \
                else []
            writer.writerow(
                ["ba", "timepoint", "requirement"] + extra_column
            )

            for row in timepoint_req:
                writer.writerow(row)

    # Write the percent requirement files only if there's a mapping
    ba_lz_map_list = [row for row in percent_map]

    if ba_lz_map_list:
        with open(os.path.join(inputs_dir,
                               "{}_percent_requirement.tab".format(
                                   reserve_type)
                               ),
                  "w", newline=""
                  ) as percent_req_file:
            writer = csv.writer(percent_req_file, delimiter="\t",
                                lineterminator="\n")

            # Write header
            writer.writerow(
                ["ba", "percent_requirement"]
            )

            for row in percent_req:
                writer.writerow(row)

        with open(os.path.join(inputs_dir,
                               "{}_percent_map.tab".format(reserve_type)
                               ),
                  "w", newline=""
                  ) as percent_map_file:
            writer = csv.writer(percent_map_file, delimiter="\t",
                                lineterminator="\n")

            # Write header
            writer.writerow(
                ["ba", "load_zone"]
            )

            for row in ba_lz_map_list:
                writer.writerow(row)
    else:
        pass
