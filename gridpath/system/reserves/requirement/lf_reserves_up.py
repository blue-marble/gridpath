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

from gridpath.system.reserves.requirement.reserve_requirements import (
    generic_get_inputs_from_database,
    generic_add_model_components,
    generic_load_model_data,
    generic_write_model_inputs,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_zone_set="LF_RESERVES_UP_ZONES",
        reserve_requirement_tmp_param="lf_reserves_up_requirement_mw",
        reserve_requirement_percent_param="lf_up_per_req",
        reserve_zone_load_zone_set="LF_UP_BA_LZ",
        ba_prj_req_contribution_set="LF_UP_BA_PRJ_CONTRIBUTION",
        prj_power_param="lf_up_prj_pwr_contribution",
        prj_capacity_param="lf_up_prj_cap_contribution",
        reserve_requirement_expression="LF_Up_Requirement",
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(
        m=m,
        d=d,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        reserve_requirement_param="lf_reserves_up_requirement_mw",
        reserve_zone_load_zone_set="LF_UP_BA_LZ",
        reserve_requirement_percent_param="lf_up_per_req",
        ba_prj_req_contribution_set="LF_UP_BA_PRJ_CONTRIBUTION",
        prj_power_param="lf_up_prj_pwr_contribution",
        prj_capacity_param="lf_up_prj_cap_contribution",
        reserve_type="lf_reserves_up",
    )


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    return generic_get_inputs_from_database(
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        reserve_type="lf_reserves_up",
        reserve_type_ba_subscenario_id=subscenarios.LF_RESERVES_UP_BA_SCENARIO_ID,
        reserve_type_req_subscenario_id=subscenarios.LF_RESERVES_UP_SCENARIO_ID,
    )


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
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
    # lf_reserves_up = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    lf_reserves_up_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tmp_req, percent_req, percent_map, project_contributions = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    generic_write_model_inputs(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        timepoint_req=tmp_req,
        percent_req=percent_req,
        percent_map=percent_map,
        project_contributions=project_contributions,
        reserve_type="lf_reserves_up",
    )
