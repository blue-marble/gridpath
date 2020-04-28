#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

import csv
import os.path
from pyomo.environ import Param, NonNegativeReals

from gridpath.system.reserves.requirement.reserve_requirements import \
    generic_get_inputs_from_database, generic_add_model_components, \
    generic_load_model_data


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_zone_set="FREQUENCY_RESPONSE_BAS",
        reserve_zone_timepoint_set="FREQUENCY_RESPONSE_BA_TIMEPOINTS",
        reserve_requirement_tmp_param="frequency_response_requirement_mw",
        reserve_requirement_percentage_param="fr_per_req",
        reserve_zone_load_zone_set="FR_BA_LZ",
        reserve_requirement_expression="Frequency_Response_Requirement"
        )

    # Also add the partial requirement for frequency response that can be
    # met by only a subset of the projects that can provide frequency response

    m.frequency_response_requirement_partial_mw = Param(
        m.FREQUENCY_RESPONSE_BA_TIMEPOINTS,
        within=NonNegativeReals
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param stage:
    :param stage: 
    :return: 
    """
    # Don't use generic function from reserve_requirements.py, as we are
    # importing two columns (total and partial requirement), not just a
    # single param
    data_portal.load(filename=os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "frequency_response_requirement.tab"),
                     index=m.FREQUENCY_RESPONSE_BA_TIMEPOINTS,
                     param=(m.frequency_response_requirement_mw,
                            m.frequency_response_requirement_partial_mw)
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
            reserve_type="frequency_respose",
            reserve_type_ba_subscenario_id
            =subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID,
            reserve_type_req_subscenario_id
            =subscenarios.FREQUENCY_RESPONSE_SCENARIO_ID
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
    # frequency_response = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    frequency_response_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    frequency_response, _, _ = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "frequency_response_requirement.tab"), "w", newline="") as \
            frequency_response_tab_file:
        writer = csv.writer(frequency_response_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["ba", "timepoint", "requirement_mw", "partial_requirement_mw"]
        )

        for row in frequency_response:
            writer.writerow(row)
