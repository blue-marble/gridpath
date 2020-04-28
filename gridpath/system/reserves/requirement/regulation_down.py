#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from gridpath.system.reserves.requirement.reserve_requirements import \
    generic_get_inputs_from_database, generic_add_model_components, \
    generic_load_model_data, generic_write_model_inputs


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_zone_set="REGULATION_DOWN_ZONES",
        reserve_requirement_tmp_param="regulation_down_requirement_mw",
        reserve_requirement_percent_param="reg_down_per_req",
        reserve_zone_load_zone_set="REG_DOWN_BA_LZ",
        reserve_requirement_expression="Reg_Down_Requirement"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(
        m=m, d=d, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage,
        reserve_requirement_param="regulation_down_requirement_mw",
        reserve_zone_load_zone_set="REG_DOWN_BA_LZ",
        reserve_requirement_percent_param="reg_down_per_req",
        reserve_type="regulation_down"
    )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    return \
        generic_get_inputs_from_database(
            subscenarios=subscenarios,
            subproblem=subproblem, stage=stage, conn=conn,
            reserve_type="regulation_down",
            reserve_type_ba_subscenario_id
            =subscenarios.REGULATION_DOWN_BA_SCENARIO_ID,
            reserve_type_req_subscenario_id
            =subscenarios.REGULATION_DOWN_SCENARIO_ID
        )


def validate_inputs(subscenarios, subproblem, stage, conn):
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
    # regulation_down = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    regulation_down_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tmp_req, percent_req, percent_map = \
        get_inputs_from_database(subscenarios, subproblem, stage, conn)

    generic_write_model_inputs(
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage,
        timepoint_req=tmp_req,
        percent_req=percent_req, percent_map=percent_map,
        reserve_type="regulation_down"
    )
